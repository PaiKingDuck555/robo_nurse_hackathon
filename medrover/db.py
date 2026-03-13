"""
MongoDB integration for MedRover robot.
Writes patient data that the dashboard reads in real time.
"""
from pymongo import MongoClient
from datetime import datetime, timezone
from bson import ObjectId
import os

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/medrover")

client = MongoClient(MONGODB_URI)
db = client.medrover


def create_patient(name: str, language: str, language_code: str, age: int = None, country: str = None) -> str:
    """Creates a patient record and returns its _id as string."""
    now = datetime.now(timezone.utc)
    result = db.patients.insert_one({
        "name": name,
        "language": language,
        "languageCode": language_code,
        "age": age,
        "country": country,
        "createdAt": now,
        "updatedAt": now,
    })
    print(f"[DB] Created patient: {name} ({language}) -> {result.inserted_id}")
    return str(result.inserted_id)


def create_intake_session(
    patient_id: str,
    qa_pairs: list,
    clinical_summary: str,
    symptoms: list,
    pain_level: int,
    allergies: list,
    medications: list,
    mental_health_flags: list = None,
    urgency_level: str = "medium",
) -> str:
    """Creates a completed intake session. Returns session _id as string."""
    now = datetime.now(timezone.utc)
    result = db.sessions.insert_one({
        "patientId": ObjectId(patient_id),
        "type": "intake",
        "status": "completed",
        "qaPairs": qa_pairs,
        "clinicalSummary": clinical_summary,
        "symptoms": symptoms,
        "painLevel": pain_level,
        "allergies": allergies,
        "currentMedications": medications,
        "mentalHealthFlags": mental_health_flags or [],
        "urgencyLevel": urgency_level,
        "relayTranscript": [],
        "startedAt": now,
        "completedAt": now,
        "createdAt": now,
        "updatedAt": now,
    })
    print(f"[DB] Created intake session for patient {patient_id} -> {result.inserted_id}")
    return str(result.inserted_id)


def create_relay_session(patient_id: str) -> str:
    """Creates an in-progress relay session. Returns session _id as string."""
    now = datetime.now(timezone.utc)
    result = db.sessions.insert_one({
        "patientId": ObjectId(patient_id),
        "type": "relay",
        "status": "in_progress",
        "qaPairs": [],
        "clinicalSummary": "",
        "symptoms": [],
        "painLevel": 0,
        "allergies": [],
        "currentMedications": [],
        "mentalHealthFlags": [],
        "urgencyLevel": "medium",
        "relayTranscript": [],
        "startedAt": now,
        "createdAt": now,
        "updatedAt": now,
    })
    print(f"[DB] Created relay session for patient {patient_id} -> {result.inserted_id}")
    return str(result.inserted_id)


def append_relay_message(session_id: str, speaker: str, text_original: str, text_translated: str):
    """Appends a message to the relay transcript."""
    db.sessions.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {
                "relayTranscript": {
                    "speaker": speaker,
                    "textOriginal": text_original,
                    "textTranslated": text_translated,
                    "timestamp": datetime.now(timezone.utc),
                }
            },
            "$set": {"updatedAt": datetime.now(timezone.utc)},
        },
    )


def complete_relay_session(session_id: str):
    """Marks a relay session as completed."""
    now = datetime.now(timezone.utc)
    db.sessions.update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"status": "completed", "completedAt": now, "updatedAt": now}},
    )
    print(f"[DB] Relay session {session_id} completed")
