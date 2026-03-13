"""
tests/test_e2e_demo.py

End-to-end demo:
  - GPT-4o generates nurse questions in English
  - GPT-4o translates to Spanish
  - smallest.ai Lightning V2 speaks Spanish to patient
  - Patient responds in Spanish via mic
  - smallest.ai Pulse transcribes patient speech
  - GPT-4o translates transcript to English
  - GPT-4o generates next nurse response
  - Repeat until intake complete

Run from nurse_screening/ directory:
    python tests/test_e2e_demo.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.agent  import (NURSE_INTRO_EN, start_nurse_conversation,
                        next_nurse_turn, translate,
                        generate_clinical_summary, extract_structured_data)
from ai.tts    import speak
from ai.stt    import transcribe
from hardware.audio import record, play

PATIENT_LANG_CODE = "es"
PATIENT_LANG_NAME = "Spanish"


def _speak_spanish(text_en: str) -> str:
    """Translate EN → ES, speak via smallest.ai TTS, return Spanish text."""
    text_es = translate(text_en, "English", PATIENT_LANG_NAME)
    print(f"\n  ┌─ EN : {text_en}")
    print(f"  └─ ES : {text_es}")
    audio = speak(text_es, PATIENT_LANG_CODE)
    if audio:
        play(audio)
    return text_es


def run():
    print("\n" + "=" * 62)
    print("  MEDROVER — End-to-End Demo")
    print("  TTS/STT: smallest.ai  |  Nurse/Translation: GPT-4o")
    print("=" * 62)

    name = input("\n  Patient name: ").strip() or "Demo Patient"
    english_log, native_log = [], []

    # ── INTRO ──────────────────────────────────────────────────────────────
    print("\n[INTRO]")
    intro_es = _speak_spanish(NURSE_INTRO_EN)
    english_log.append({"role": "nurse", "text": NURSE_INTRO_EN})
    native_log.append( {"role": "nurse", "text": intro_es})

    # ── FIRST QUESTION ─────────────────────────────────────────────────────
    print("\n[NURSE] Generating first question...")
    gpt_history, _, first_q_en = start_nurse_conversation()
    first_q_es = _speak_spanish(first_q_en)
    english_log.append({"role": "nurse", "text": first_q_en})
    native_log.append( {"role": "nurse", "text": first_q_es})

    # ── CONVERSATION LOOP ──────────────────────────────────────────────────
    turn = 1
    while True:
        print(f"\n[TURN {turn}] Press Enter then speak in Spanish (8 seconds)...")
        input("  ── Press Enter to start recording ──")
        print("  🎙  Recording...")
        audio_bytes = record(seconds=8)
        print("  ✓  Transcribing via smallest.ai...")

        patient_es = transcribe(audio_bytes, language=PATIENT_LANG_CODE)

        if not patient_es.strip():
            retry_es = _speak_spanish("I'm sorry, I didn't catch that. Could you please repeat?")
            english_log.append({"role": "nurse", "text": "I'm sorry, I didn't catch that. Could you please repeat?"})
            native_log.append( {"role": "nurse", "text": retry_es})
            continue

        # Translate patient answer to English
        patient_en = translate(patient_es, PATIENT_LANG_NAME, "English")
        print(f"\n  🧑 Patient")
        print(f"  ┌─ ES : {patient_es}")
        print(f"  └─ EN : {patient_en}")

        english_log.append({"role": "patient", "text": patient_en})
        native_log.append( {"role": "patient", "text": patient_es})

        # GPT-4o nurse next response
        gpt_history, nurse_reply_en, done = next_nurse_turn(gpt_history, patient_en)
        nurse_reply_es = _speak_spanish(nurse_reply_en)
        english_log.append({"role": "nurse", "text": nurse_reply_en})
        native_log.append( {"role": "nurse", "text": nurse_reply_es})

        if done:
            print("\n  ✓  Intake complete.")
            break

        turn += 1

    # ── SUMMARY ───────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  CLINICAL SUMMARY")
    print("=" * 62)
    structured = extract_structured_data(english_log)
    summary    = generate_clinical_summary(english_log)
    print(f"\n{summary}")
    print(f"\n  Severity : {structured.get('severity_score')}/10  |  Risk : {structured.get('risk_level','').upper()}")

    # ── SAVE ──────────────────────────────────────────────────────────────
    save = input("\n  Save to MongoDB? (y/n): ").strip().lower()
    if save == "y":
        from db.mongo import save_patient_session, print_priority_queue
        sid = save_patient_session(
            name=name,
            language_code=PATIENT_LANG_CODE, language_name=PATIENT_LANG_NAME,
            english_log=english_log, native_log=native_log,
            structured=structured, clinical_summary=summary,
        )
        print(f"  ✓  Saved → session_id: {sid}")
        print_priority_queue()


if __name__ == "__main__":
    run()
