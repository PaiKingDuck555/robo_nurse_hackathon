"""
api.py — MedRover FastAPI

Run from medrover/ directory:
    uvicorn api:app --reload --port 8000

Interactive docs: http://localhost:8000/docs
"""

import base64
import json
import uuid
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai.agent import (
    NURSE_INTRO_EN,
    extract_structured_data,
    generate_clinical_summary,
    next_nurse_turn,
    start_nurse_conversation,
    translate,
)
from ai.stt import transcribe
from ai.tts import speak
from db.mongo import (
    get_all_waiting,
    get_priority_queue,
    get_session,
    print_priority_queue,
    save_patient_session,
    search_by_name,
    update_status,
)

app = FastAPI(
    title="MedRover API",
    description="Multilingual nurse intake, patient prioritization, and doctor relay.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory store for active (in-progress) sessions
# Keyed by session_id. Cleared once session is saved to MongoDB.
# ---------------------------------------------------------------------------
_active: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PATIENT_LANG_CODE = "es"
PATIENT_LANG_NAME = "Spanish"
DOCTOR_LANG_CODE  = "en"
DOCTOR_LANG_NAME  = "English"


def _audio_to_b64(audio_bytes: bytes) -> str:
    return base64.b64encode(audio_bytes).decode("utf-8")


def _tts_b64(text_en: str, lang_code: str, lang_name: str) -> tuple[str, str]:
    """Translate English text → target language, synthesise, return (translated_text, b64_audio)."""
    translated = translate(text_en, "English", lang_name) if lang_name != "English" else text_en
    audio = speak(translated, lang_code)
    return translated, _audio_to_b64(audio) if audio else ""


def _require_session(session_id: str) -> dict:
    session = _active.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found or already completed.")
    return session


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class StartSessionResponse(BaseModel):
    session_id: str
    intro_text: str
    intro_audio_b64: str
    first_question_text: str             # English
    first_question_text_native: str      # patient's language
    first_question_audio_b64: str

class AnswerResponse(BaseModel):
    session_id: str                      # always returned — pass this in future turns
    patient_text_en: str                 # patient's answer in English
    nurse_reply_text_en: str             # nurse reply in English
    done: bool
    # Populated only when done=True
    clinical_summary: Optional[str] = None
    severity_score: Optional[int] = None
    risk_level: Optional[str] = None

class SummaryResponse(BaseModel):
    session_id: str
    name: str
    clinical_summary: str
    chief_complaint: str
    symptoms: list[str]
    pain_level: int
    allergies: list[str]
    current_medications: list[str]
    severity_score: int
    risk_level: str

class QueueEntry(BaseModel):
    session_id: str
    name: str
    chief_complaint: str
    symptoms: list[str]
    severity_score: int
    risk_level: str
    pain_level: int
    checked_in_at: str

class RelayResponse(BaseModel):
    original_text: str
    translated_text: str
    translated_audio_b64: str

class StatusUpdate(BaseModel):
    status: str   # "with_doctor" | "done"

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/session/start", response_model=StartSessionResponse,
          summary="Start a new patient session")
def start_session(
    patient_name: str = Form(..., description="Patient's name"),
    language_code: str = Form(default="es"),
    language_name: str = Form(default="Spanish"),
):
    """
    Creates a new nurse intake session.

    Returns the MedRover intro and first clinical question — both as text
    and base64-encoded WAV audio — ready for the frontend to play.
    """
    session_id = str(uuid.uuid4())

    # Fixed intro
    intro_native, intro_audio_b64 = _tts_b64(NURSE_INTRO_EN, language_code, language_name)

    # GPT-4o first question (English)
    gpt_history, _, first_q_en = start_nurse_conversation()
    first_q_native, first_q_audio_b64 = _tts_b64(first_q_en, language_code, language_name)

    _active[session_id] = {
        "name":          patient_name,
        "language_code": language_code,
        "language_name": language_name,
        "gpt_history":   gpt_history,
        "english_log":   [
            {"role": "nurse", "text": NURSE_INTRO_EN},
            {"role": "nurse", "text": first_q_en},
        ],
        "native_log": [
            {"role": "nurse", "text": intro_native},
            {"role": "nurse", "text": first_q_native},
        ],
    }

    return StartSessionResponse(
        session_id=session_id,
        intro_text=intro_native,
        intro_audio_b64=intro_audio_b64,
        first_question_text=first_q_en,
        first_question_text_native=first_q_native,
        first_question_audio_b64=first_q_audio_b64,
    )


@app.post("/answer", response_model=AnswerResponse,
          summary="Submit a patient answer and get the next nurse response")
async def submit_answer(
    session_id: Optional[str]  = Form(default=None, description="Session ID from a previous turn. Omit to start a new session."),
    text:       Optional[str]  = Form(default=None, description="Patient answer in English"),
    audio:      Optional[UploadFile] = File(default=None, description="WAV audio of patient's answer"),
):
    """
    Single endpoint for the full nurse intake conversation.

    - Omit session_id to auto-start a new session. The returned session_id must
      be passed in every subsequent turn.
    - Pass text (English) or audio on each turn.
    - Repeat until done=True, which also saves the session to MongoDB.
    """
    # --- Resolve or create session ---
    if not session_id or session_id not in _active:
        session_id = str(uuid.uuid4())[:8]   # short readable ID
        gpt_history, _, first_q_en = start_nurse_conversation()
        _active[session_id] = {
            "name":          "Patient",
            "language_code": PATIENT_LANG_CODE,
            "language_name": PATIENT_LANG_NAME,
            "gpt_history":   gpt_history,
            "english_log":   [
                {"role": "nurse", "text": NURSE_INTRO_EN},
                {"role": "nurse", "text": first_q_en},
            ],
            "native_log":    [
                {"role": "nurse", "text": NURSE_INTRO_EN},
                {"role": "nurse", "text": first_q_en},
            ],
        }

    session   = _active[session_id]
    lang_code = session["language_code"]
    lang_name = session["language_name"]

    # --- Get patient answer text ---
    if audio:
        audio_bytes = await audio.read()
        patient_text = transcribe(audio_bytes, language="multi")
    elif text:
        patient_text = text
    else:
        raise HTTPException(status_code=422, detail="Provide either 'text' or 'audio'.")

    if not patient_text.strip():
        raise HTTPException(status_code=400, detail="Empty input.")

    # --- Log patient answer (English) ---
    session["english_log"].append({"role": "patient", "text": patient_text})
    session["native_log"].append( {"role": "patient", "text": patient_text})

    # --- GPT-4o next nurse turn ---
    session["gpt_history"], nurse_reply_en, done = next_nurse_turn(
        session["gpt_history"], patient_text
    )
    session["english_log"].append({"role": "nurse", "text": nurse_reply_en})
    session["native_log"].append( {"role": "nurse", "text": nurse_reply_en})

    response = AnswerResponse(
        session_id=session_id,
        patient_text_en=patient_text,
        nurse_reply_text_en=nurse_reply_en,
        done=done,
    )

    # --- If intake complete: save to DB ---
    if done:
        english_log = session["english_log"]
        structured  = extract_structured_data(english_log)
        summary     = generate_clinical_summary(english_log)

        save_patient_session(
            name=session["name"],
            language_code=lang_code,
            language_name=lang_name,
            english_log=english_log,
            native_log=session["native_log"],
            structured=structured,
            clinical_summary=summary,
        )
        del _active[session_id]

        response.clinical_summary = summary
        response.severity_score   = structured.get("severity_score")
        response.risk_level       = structured.get("risk_level")

    return response


@app.get("/session/{session_id}/summary", response_model=SummaryResponse,
         summary="Get the clinical summary for a completed session")
def get_summary(session_id: str):
    """
    Returns the full clinical summary and structured fields from MongoDB
    for a completed intake session.
    """
    doc = get_session(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    return SummaryResponse(
        session_id=doc["session_id"],
        name=doc["name"],
        clinical_summary=doc["clinical_summary"],
        chief_complaint=doc.get("chief_complaint", ""),
        symptoms=doc.get("symptoms", []),
        pain_level=doc.get("pain_level", 0),
        allergies=doc.get("allergies", []),
        current_medications=doc.get("current_medications", []),
        severity_score=doc.get("severity_score", 0),
        risk_level=doc.get("risk_level", "unknown"),
    )


@app.get("/waiting", summary="All waiting patients — full details including conversation logs")
def get_waiting():
    """
    Returns every field for all patients with status='waiting',
    sorted by severity score descending.
    Includes clinical_summary, conversation_english, conversation_native, and all structured fields.
    """
    patients = get_all_waiting()
    for p in patients:
        if "checked_in_at" in p:
            p["checked_in_at"] = str(p["checked_in_at"])
    return patients


@app.get("/queue", response_model=list[QueueEntry],
         summary="Get the priority-sorted patient queue")
def queue():
    """
    Returns all patients with status='waiting', sorted by severity score
    (highest first). The doctor uses this to decide who to see next.
    """
    patients = get_priority_queue()
    return [
        QueueEntry(
            session_id=p["session_id"],
            name=p.get("name", ""),
            chief_complaint=p.get("chief_complaint", ""),
            symptoms=p.get("symptoms", []),
            severity_score=p.get("severity_score", 0),
            risk_level=p.get("risk_level", "unknown"),
            pain_level=p.get("pain_level", 0),
            checked_in_at=str(p.get("checked_in_at", "")),
        )
        for p in patients
    ]


@app.post("/relay/{session_id}/doctor", response_model=RelayResponse,
          summary="Doctor speaks English → translated to patient's language")
async def relay_doctor(
    session_id: str,
    audio: Optional[UploadFile] = File(default=None, description="WAV audio of doctor speaking"),
    text:  Optional[str]        = Form(default=None, description="Doctor's message as text"),
):
    """
    Accepts the doctor's English speech (or text) and returns the translation
    in the patient's language as text + audio.
    """
    doc = get_session(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    lang_code = doc["language_code"]
    lang_name = doc["language_name"]

    if audio:
        audio_bytes = await audio.read()
        doctor_text = transcribe(audio_bytes, language="en")
    elif text:
        doctor_text = text
    else:
        raise HTTPException(status_code=422, detail="Provide either 'audio' or 'text'.")

    translated, audio_b64 = _tts_b64(doctor_text, lang_code, lang_name)

    return RelayResponse(
        original_text=doctor_text,
        translated_text=translated,
        translated_audio_b64=audio_b64,
    )


@app.post("/relay/{session_id}/patient", response_model=RelayResponse,
          summary="Patient speaks their language → translated to English")
async def relay_patient(
    session_id: str,
    audio: Optional[UploadFile] = File(default=None, description="WAV audio of patient speaking"),
    text:  Optional[str]        = Form(default=None, description="Patient's message as text"),
):
    """
    Accepts the patient's speech (or text) and returns the English translation
    as text + audio for the doctor.
    """
    doc = get_session(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    lang_code = doc["language_code"]
    lang_name = doc["language_name"]

    if audio:
        audio_bytes = await audio.read()
        patient_text = transcribe(audio_bytes, language=lang_code)
    elif text:
        patient_text = text
    else:
        raise HTTPException(status_code=422, detail="Provide either 'audio' or 'text'.")

    translated, audio_b64 = _tts_b64(patient_text, lang_name, "English")
    # For relay, speak in English for the doctor
    english_audio = speak(translated, "en")

    return RelayResponse(
        original_text=patient_text,
        translated_text=translated,
        translated_audio_b64=_audio_to_b64(english_audio) if english_audio else "",
    )


@app.get("/patients", response_model=list[QueueEntry],
         summary="Search patients by name")
def search_patients(name: str):
    """
    Case-insensitive partial name search across all patients (any status).
    e.g. /patients?name=juan  matches 'Juan Garcia', 'Juana Lopez', etc.
    """
    results = search_by_name(name)
    return [
        QueueEntry(
            session_id=p["session_id"],
            name=p.get("name", ""),
            chief_complaint=p.get("chief_complaint", ""),
            symptoms=p.get("symptoms", []),
            severity_score=p.get("severity_score", 0),
            risk_level=p.get("risk_level", "unknown"),
            pain_level=p.get("pain_level", 0),
            checked_in_at=str(p.get("checked_in_at", "")),
        )
        for p in results
    ]


@app.patch("/session/{session_id}/status",
           summary="Update patient session status")
def set_status(session_id: str, body: StatusUpdate):
    """
    Updates a patient's status in MongoDB.
    Valid transitions: waiting → with_doctor → done
    """
    valid = {"waiting", "with_doctor", "done"}
    if body.status not in valid:
        raise HTTPException(status_code=422, detail=f"status must be one of: {valid}")

    doc = get_session(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    update_status(session_id, body.status)
    return {"session_id": session_id, "status": body.status}


@app.websocket("/ws/relay/{session_id}")
async def relay_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket relay for real-time doctor ↔ patient voice translation.

    Frontend connects once per consultation session and sends audio turns
    as they happen. Each message is JSON:

        Incoming (frontend → backend):
        {
            "direction": "doctor" | "patient",
            "audio_b64": "<base64-encoded WAV>"   // mic recording
        }

        Outgoing (backend → frontend):
        {
            "direction": "doctor" | "patient",
            "original_text":    "...",   // what was said
            "translated_text":  "...",   // translation
            "audio_b64":        "..."    // translated speech as base64 WAV
        }

    Pipeline:
        doctor  → smallest.ai STT (EN) → GPT-4o translate EN→ES → smallest.ai TTS (ES)
        patient → smallest.ai STT (multi) → GPT-4o translate ES→EN → smallest.ai TTS (EN)
    """
    await websocket.accept()

    doc = get_session(session_id)
    if not doc:
        await websocket.send_text(json.dumps({"error": f"Session '{session_id}' not found."}))
        await websocket.close()
        return

    lang_code = doc.get("language_code", "es")
    lang_name = doc.get("language_name", "Spanish")

    print(f"[WS Relay] Connected — session={session_id} lang={lang_name}")

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)

            direction = payload.get("direction")
            audio_b64 = payload.get("audio_b64", "")

            if not direction or not audio_b64:
                await websocket.send_text(json.dumps(
                    {"error": "Payload must include 'direction' and 'audio_b64'."}
                ))
                continue

            audio_bytes = base64.b64decode(audio_b64)

            if direction == "doctor":
                # Doctor speaks English → transcribe → translate → speak Spanish to patient
                original = transcribe(audio_bytes, language="en")
                if not original:
                    await websocket.send_text(json.dumps({"error": "Could not transcribe doctor audio."}))
                    continue
                translated = translate(original, "English", lang_name)
                audio_out  = speak(translated, lang_code)

            elif direction == "patient":
                # Patient speaks (auto-detect) → transcribe → translate → speak English to doctor
                original   = transcribe(audio_bytes, language="multi")
                if not original:
                    await websocket.send_text(json.dumps({"error": "Could not transcribe patient audio."}))
                    continue
                translated = translate(original, lang_name, "English")
                audio_out  = speak(translated, "en")

            else:
                await websocket.send_text(json.dumps(
                    {"error": "direction must be 'doctor' or 'patient'."}
                ))
                continue

            await websocket.send_text(json.dumps({
                "direction":       direction,
                "original_text":   original,
                "translated_text": translated,
                "audio_b64":       base64.b64encode(audio_out).decode() if audio_out else "",
            }))

    except WebSocketDisconnect:
        print(f"[WS Relay] Disconnected — session={session_id}")


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
