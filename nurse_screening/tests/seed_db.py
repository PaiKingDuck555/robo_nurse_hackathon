"""
tests/seed_db.py

Inserts 6 realistic dummy patient sessions into MongoDB.
Covers the full severity spectrum: critical → low.

Run from medrover/ directory:
    python tests/seed_db.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, timedelta
from db.mongo import _get_collection

PATIENTS = [
    # ── 1. CRITICAL ────────────────────────────────────────────────────────
    {
        "name": "Maria Lopez",
        "language_code": "es", "language_name": "Spanish",
        "chief_complaint": "Chest pain and shortness of breath",
        "symptoms": ["chest pain", "shortness of breath", "left arm pain", "sweating"],
        "pain_level": 8,
        "allergies": [],
        "current_medications": ["Aspirin 81mg"],
        "severity_score": 9,
        "risk_level": "critical",
        "clinical_summary": (
            "CHIEF COMPLAINT: Chest pain radiating to left arm with shortness of breath\n"
            "HISTORY: Symptoms onset 2 hours ago, sudden onset while resting. "
            "Associated left arm pain and diaphoresis.\n"
            "PAIN LEVEL: 8/10\n"
            "ALLERGIES: None known\n"
            "CURRENT MEDICATIONS: Aspirin 81mg daily\n"
            "CLINICAL NOTES: High suspicion for acute cardiac event. "
            "Requires immediate physician evaluation."
        ),
        "conversation_english": [
            {"role": "nurse",   "text": "Hello, I am MedRover. I will ask you a few questions before the doctor sees you."},
            {"role": "nurse",   "text": "What brings you in today?"},
            {"role": "patient", "text": "I have very bad chest pain and I can't breathe properly."},
            {"role": "nurse",   "text": "When did the chest pain start and does it spread anywhere?"},
            {"role": "patient", "text": "About 2 hours ago. It goes to my left arm and I am sweating a lot."},
            {"role": "nurse",   "text": "On a scale of 1 to 10 how severe is the pain?"},
            {"role": "patient", "text": "It is an 8 out of 10."},
            {"role": "nurse",   "text": "Are you taking any medications or do you have any allergies?"},
            {"role": "patient", "text": "I take aspirin every day. No allergies."},
            {"role": "nurse",   "text": "Thank you. The doctor will be with you very shortly. [INTAKE_COMPLETE]"},
        ],
        "conversation_native": [
            {"role": "nurse",   "text": "Hola, soy MedRover. Le haré algunas preguntas antes de que el médico le atienda."},
            {"role": "nurse",   "text": "¿Cuál es el motivo de su visita hoy?"},
            {"role": "patient", "text": "Tengo un dolor muy fuerte en el pecho y no puedo respirar bien."},
            {"role": "nurse",   "text": "¿Cuándo empezó el dolor de pecho y se extiende a algún lugar?"},
            {"role": "patient", "text": "Hace unas 2 horas. Se va al brazo izquierdo y estoy sudando mucho."},
            {"role": "nurse",   "text": "En una escala del 1 al 10, ¿qué tan fuerte es el dolor?"},
            {"role": "patient", "text": "Es un 8 de 10."},
            {"role": "nurse",   "text": "¿Está tomando algún medicamento o tiene alguna alergia?"},
            {"role": "patient", "text": "Tomo aspirina todos los días. Sin alergias."},
            {"role": "nurse",   "text": "Gracias. El médico estará con usted muy pronto."},
        ],
        "status": "waiting",
        "checked_in_at": datetime.now(timezone.utc) - timedelta(minutes=5),
    },

    # ── 2. HIGH ────────────────────────────────────────────────────────────
    {
        "name": "Roberto Sanchez",
        "language_code": "es", "language_name": "Spanish",
        "chief_complaint": "High fever with confusion",
        "symptoms": ["fever", "confusion", "neck stiffness", "headache"],
        "pain_level": 7,
        "allergies": ["penicillin"],
        "current_medications": [],
        "severity_score": 8,
        "risk_level": "high",
        "clinical_summary": (
            "CHIEF COMPLAINT: High fever (39.5°C) with confusion and neck stiffness\n"
            "HISTORY: Symptoms started yesterday evening. Family reports increasing confusion "
            "over the last 3 hours. Reports neck stiffness and severe headache.\n"
            "PAIN LEVEL: 7/10\n"
            "ALLERGIES: Penicillin\n"
            "CURRENT MEDICATIONS: None\n"
            "CLINICAL NOTES: Triad of fever, headache, and neck stiffness warrants urgent "
            "meningitis evaluation. Penicillin allergy noted — alternative antibiotics required."
        ),
        "conversation_english": [
            {"role": "nurse",   "text": "Hello, I am MedRover. What brings you in today?"},
            {"role": "patient", "text": "I have a very high fever and I feel confused. My neck hurts a lot."},
            {"role": "nurse",   "text": "How long have you had these symptoms?"},
            {"role": "patient", "text": "The fever started yesterday. The confusion got worse in the last few hours."},
            {"role": "nurse",   "text": "How severe is your headache on a scale of 1 to 10?"},
            {"role": "patient", "text": "About 7. It is the worst headache of my life."},
            {"role": "nurse",   "text": "Do you have any medication allergies?"},
            {"role": "patient", "text": "Yes, I am allergic to penicillin."},
            {"role": "nurse",   "text": "Thank you. The doctor will see you immediately. [INTAKE_COMPLETE]"},
        ],
        "conversation_native": [
            {"role": "nurse",   "text": "Hola, soy MedRover. ¿Cuál es el motivo de su visita?"},
            {"role": "patient", "text": "Tengo fiebre muy alta y me siento confundido. Me duele mucho el cuello."},
            {"role": "nurse",   "text": "¿Hace cuánto tiempo tiene estos síntomas?"},
            {"role": "patient", "text": "La fiebre empezó ayer. La confusión empeoró en las últimas horas."},
            {"role": "nurse",   "text": "¿Qué tan fuerte es su dolor de cabeza del 1 al 10?"},
            {"role": "patient", "text": "Como un 7. Es el peor dolor de cabeza de mi vida."},
            {"role": "nurse",   "text": "¿Tiene alguna alergia a medicamentos?"},
            {"role": "patient", "text": "Sí, soy alérgico a la penicilina."},
            {"role": "nurse",   "text": "Gracias. El médico le verá de inmediato."},
        ],
        "status": "waiting",
        "checked_in_at": datetime.now(timezone.utc) - timedelta(minutes=12),
    },

    # ── 3. HIGH ────────────────────────────────────────────────────────────
    {
        "name": "Ana Reyes",
        "language_code": "es", "language_name": "Spanish",
        "chief_complaint": "Severe abdominal pain and vomiting",
        "symptoms": ["abdominal pain", "vomiting", "nausea", "fever"],
        "pain_level": 7,
        "allergies": [],
        "current_medications": ["omeprazole"],
        "severity_score": 7,
        "risk_level": "high",
        "clinical_summary": (
            "CHIEF COMPLAINT: Severe right lower quadrant abdominal pain with vomiting\n"
            "HISTORY: Sudden onset abdominal pain 6 hours ago, progressively worsening. "
            "Three episodes of vomiting. Low-grade fever (38.1°C).\n"
            "PAIN LEVEL: 7/10\n"
            "ALLERGIES: None known\n"
            "CURRENT MEDICATIONS: Omeprazole 20mg daily\n"
            "CLINICAL NOTES: RLQ pain with fever and vomiting — appendicitis cannot be excluded. "
            "Surgical consult may be warranted."
        ),
        "conversation_english": [
            {"role": "nurse",   "text": "Hello, I am MedRover. What brings you in today?"},
            {"role": "patient", "text": "I have very bad stomach pain on the right side and I keep vomiting."},
            {"role": "nurse",   "text": "Where exactly is the pain and how long has it been going on?"},
            {"role": "patient", "text": "Lower right side. It started about 6 hours ago and keeps getting worse."},
            {"role": "nurse",   "text": "How would you rate the pain from 1 to 10?"},
            {"role": "patient", "text": "A 7. I also have a small fever."},
            {"role": "nurse",   "text": "Are you on any medications?"},
            {"role": "patient", "text": "Just omeprazole for my stomach. No allergies."},
            {"role": "nurse",   "text": "Thank you. The doctor will be with you shortly. [INTAKE_COMPLETE]"},
        ],
        "conversation_native": [
            {"role": "nurse",   "text": "Hola, soy MedRover. ¿Qué le trae por aquí hoy?"},
            {"role": "patient", "text": "Tengo un dolor muy fuerte en el estómago del lado derecho y sigo vomitando."},
            {"role": "nurse",   "text": "¿Dónde exactamente es el dolor y hace cuánto tiempo lo tiene?"},
            {"role": "patient", "text": "Lado inferior derecho. Empezó hace unas 6 horas y sigue empeorando."},
            {"role": "nurse",   "text": "¿Cómo calificaría el dolor del 1 al 10?"},
            {"role": "patient", "text": "Un 7. También tengo un poco de fiebre."},
            {"role": "nurse",   "text": "¿Está tomando algún medicamento?"},
            {"role": "patient", "text": "Solo omeprazol para el estómago. Sin alergias."},
            {"role": "nurse",   "text": "Gracias. El médico estará con usted pronto."},
        ],
        "status": "waiting",
        "checked_in_at": datetime.now(timezone.utc) - timedelta(minutes=20),
    },

    # ── 4. MEDIUM ──────────────────────────────────────────────────────────
    {
        "name": "Carlos Mendez",
        "language_code": "es", "language_name": "Spanish",
        "chief_complaint": "Persistent headache and mild fever for 2 days",
        "symptoms": ["headache", "fever", "fatigue", "mild sore throat"],
        "pain_level": 5,
        "allergies": ["ibuprofen"],
        "current_medications": ["paracetamol"],
        "severity_score": 5,
        "risk_level": "medium",
        "clinical_summary": (
            "CHIEF COMPLAINT: Persistent frontal headache with mild fever for 2 days\n"
            "HISTORY: Gradual onset headache and low-grade fever (37.8°C) for 48 hours. "
            "Mild sore throat and fatigue. No neck stiffness.\n"
            "PAIN LEVEL: 5/10\n"
            "ALLERGIES: Ibuprofen (GI intolerance)\n"
            "CURRENT MEDICATIONS: Paracetamol as needed\n"
            "CLINICAL NOTES: Presentation consistent with viral upper respiratory infection. "
            "Ibuprofen allergy noted — avoid NSAIDs."
        ),
        "conversation_english": [
            {"role": "nurse",   "text": "Hello, I am MedRover. What brings you in today?"},
            {"role": "patient", "text": "I have had a headache and fever for two days now."},
            {"role": "nurse",   "text": "Can you describe the headache and how high is the fever?"},
            {"role": "patient", "text": "It is in the front of my head. The fever is around 37.8. I am also very tired."},
            {"role": "nurse",   "text": "How severe is your pain on a scale of 1 to 10?"},
            {"role": "patient", "text": "About a 5."},
            {"role": "nurse",   "text": "Any allergies or current medications?"},
            {"role": "patient", "text": "I am allergic to ibuprofen. Taking paracetamol for the pain."},
            {"role": "nurse",   "text": "Thank you. The doctor will see you soon. [INTAKE_COMPLETE]"},
        ],
        "conversation_native": [
            {"role": "nurse",   "text": "Hola, soy MedRover. ¿Qué le trae por aquí hoy?"},
            {"role": "patient", "text": "Llevo dos días con dolor de cabeza y fiebre."},
            {"role": "nurse",   "text": "¿Puede describir el dolor de cabeza y qué tan alta es la fiebre?"},
            {"role": "patient", "text": "Es en la frente. La fiebre es de unos 37.8. También estoy muy cansado."},
            {"role": "nurse",   "text": "¿Qué tan fuerte es el dolor del 1 al 10?"},
            {"role": "patient", "text": "Como un 5."},
            {"role": "nurse",   "text": "¿Tiene alguna alergia o medicamentos actuales?"},
            {"role": "patient", "text": "Soy alérgico al ibuprofeno. Tomo paracetamol para el dolor."},
            {"role": "nurse",   "text": "Gracias. El médico le atenderá pronto."},
        ],
        "status": "with_doctor",
        "checked_in_at": datetime.now(timezone.utc) - timedelta(minutes=35),
    },

    # ── 5. LOW ─────────────────────────────────────────────────────────────
    {
        "name": "Sofia Herrera",
        "language_code": "es", "language_name": "Spanish",
        "chief_complaint": "Mild cold symptoms and runny nose",
        "symptoms": ["runny nose", "mild cough", "sneezing"],
        "pain_level": 2,
        "allergies": [],
        "current_medications": [],
        "severity_score": 2,
        "risk_level": "low",
        "clinical_summary": (
            "CHIEF COMPLAINT: Mild cold symptoms — runny nose, cough, sneezing for 3 days\n"
            "HISTORY: Gradual onset of common cold symptoms 3 days ago. No fever. "
            "No shortness of breath. Denies any systemic symptoms.\n"
            "PAIN LEVEL: 2/10\n"
            "ALLERGIES: None known\n"
            "CURRENT MEDICATIONS: None\n"
            "CLINICAL NOTES: Likely viral upper respiratory tract infection. Low acuity."
        ),
        "conversation_english": [
            {"role": "nurse",   "text": "Hello, I am MedRover. What brings you in today?"},
            {"role": "patient", "text": "I have a runny nose and a little cough for the past 3 days."},
            {"role": "nurse",   "text": "Do you have any fever or other symptoms?"},
            {"role": "patient", "text": "No fever. Just sneezing a lot. I feel a little tired."},
            {"role": "nurse",   "text": "How would you rate your discomfort from 1 to 10?"},
            {"role": "patient", "text": "About a 2. It is not that bad."},
            {"role": "nurse",   "text": "Any allergies or medications?"},
            {"role": "patient", "text": "No allergies. No medications."},
            {"role": "nurse",   "text": "Thank you. The doctor will be with you shortly. [INTAKE_COMPLETE]"},
        ],
        "conversation_native": [
            {"role": "nurse",   "text": "Hola, soy MedRover. ¿Qué le trae por aquí hoy?"},
            {"role": "patient", "text": "Tengo moqueo y un poco de tos desde hace 3 días."},
            {"role": "nurse",   "text": "¿Tiene fiebre u otros síntomas?"},
            {"role": "patient", "text": "Sin fiebre. Solo estornudo mucho. Me siento un poco cansada."},
            {"role": "nurse",   "text": "¿Cómo calificaría su malestar del 1 al 10?"},
            {"role": "patient", "text": "Como un 2. No está tan mal."},
            {"role": "nurse",   "text": "¿Tiene alergias o medicamentos?"},
            {"role": "patient", "text": "Sin alergias. Sin medicamentos."},
            {"role": "nurse",   "text": "Gracias. El médico estará con usted pronto."},
        ],
        "status": "waiting",
        "checked_in_at": datetime.now(timezone.utc) - timedelta(minutes=45),
    },

    # ── 6. MEDIUM ──────────────────────────────────────────────────────────
    {
        "name": "Diego Vargas",
        "language_code": "es", "language_name": "Spanish",
        "chief_complaint": "Lower back pain after lifting",
        "symptoms": ["lower back pain", "muscle stiffness", "limited mobility"],
        "pain_level": 6,
        "allergies": [],
        "current_medications": ["ibuprofen 400mg"],
        "severity_score": 4,
        "risk_level": "medium",
        "clinical_summary": (
            "CHIEF COMPLAINT: Acute lower back pain after heavy lifting yesterday\n"
            "HISTORY: Onset after lifting heavy boxes at work yesterday afternoon. "
            "Localized to lumbar region, no radiation to legs. No numbness or tingling. "
            "Self-treating with ibuprofen.\n"
            "PAIN LEVEL: 6/10\n"
            "ALLERGIES: None known\n"
            "CURRENT MEDICATIONS: Ibuprofen 400mg as needed\n"
            "CLINICAL NOTES: Mechanism and presentation consistent with acute lumbar muscle strain. "
            "No red flags for disc herniation at this time."
        ),
        "conversation_english": [
            {"role": "nurse",   "text": "Hello, I am MedRover. What brings you in today?"},
            {"role": "patient", "text": "My lower back is killing me. I hurt it lifting boxes at work yesterday."},
            {"role": "nurse",   "text": "Does the pain go down your legs at all?"},
            {"role": "patient", "text": "No, it stays in the lower back. No numbness either."},
            {"role": "nurse",   "text": "How severe is the pain from 1 to 10?"},
            {"role": "patient", "text": "A 6. Hard to bend or stand up straight."},
            {"role": "nurse",   "text": "Any allergies or are you taking anything for the pain?"},
            {"role": "patient", "text": "No allergies. I have been taking ibuprofen 400mg."},
            {"role": "nurse",   "text": "Thank you. The doctor will see you soon. [INTAKE_COMPLETE]"},
        ],
        "conversation_native": [
            {"role": "nurse",   "text": "Hola, soy MedRover. ¿Qué le trae por aquí hoy?"},
            {"role": "patient", "text": "Me duele mucho la espalda baja. Me la lastimé levantando cajas en el trabajo ayer."},
            {"role": "nurse",   "text": "¿El dolor baja por las piernas?"},
            {"role": "patient", "text": "No, se queda en la espalda baja. Tampoco tengo entumecimiento."},
            {"role": "nurse",   "text": "¿Qué tan fuerte es el dolor del 1 al 10?"},
            {"role": "patient", "text": "Un 6. Es difícil doblarme o ponerme recto."},
            {"role": "nurse",   "text": "¿Tiene alergias o está tomando algo para el dolor?"},
            {"role": "patient", "text": "Sin alergias. He tomado ibuprofeno 400mg."},
            {"role": "nurse",   "text": "Gracias. El médico le atenderá pronto."},
        ],
        "status": "waiting",
        "checked_in_at": datetime.now(timezone.utc) - timedelta(minutes=50),
    },

    # ── 7. CRITICAL ────────────────────────────────────────────────────────
    {
        "name": "Elena Castillo",
        "language_code": "es", "language_name": "Spanish",
        "chief_complaint": "Difficulty breathing and swollen throat after eating",
        "symptoms": ["throat swelling", "difficulty breathing", "hives", "dizziness"],
        "pain_level": 8,
        "allergies": ["shellfish"],
        "current_medications": [],
        "severity_score": 10,
        "risk_level": "critical",
        "clinical_summary": (
            "CHIEF COMPLAINT: Acute throat swelling and difficulty breathing after eating shrimp\n"
            "HISTORY: Symptoms onset 15 minutes ago after accidental shellfish ingestion. "
            "Progressive throat tightening, hives on arms and neck, dizziness.\n"
            "PAIN LEVEL: 8/10\n"
            "ALLERGIES: Shellfish (severe)\n"
            "CURRENT MEDICATIONS: None\n"
            "CLINICAL NOTES: Presentation consistent with anaphylaxis. "
            "Epinephrine required immediately. Do not delay."
        ),
        "conversation_english": [
            {"role": "nurse",   "text": "Hello, I am MedRover. What brings you in today?"},
            {"role": "patient", "text": "I can't breathe properly. My throat is swelling up after I ate shrimp."},
            {"role": "nurse",   "text": "Are you allergic to shellfish? When did this start?"},
            {"role": "patient", "text": "Yes I am allergic. It started about 15 minutes ago. I also have hives on my arms."},
            {"role": "nurse",   "text": "Are you feeling dizzy or lightheaded?"},
            {"role": "patient", "text": "Yes very dizzy. Please hurry."},
            {"role": "nurse",   "text": "The doctor is coming right now. Stay calm. [INTAKE_COMPLETE]"},
        ],
        "conversation_native": [
            {"role": "nurse",   "text": "Hola, soy MedRover. ¿Qué le trae por aquí hoy?"},
            {"role": "patient", "text": "No puedo respirar bien. Se me está hinchando la garganta después de comer camarones."},
            {"role": "nurse",   "text": "¿Es alérgica a los mariscos? ¿Cuándo empezó esto?"},
            {"role": "patient", "text": "Sí soy alérgica. Empezó hace unos 15 minutos. También tengo ronchas en los brazos."},
            {"role": "nurse",   "text": "¿Siente mareos o sensación de desmayo?"},
            {"role": "patient", "text": "Sí, mucho mareo. Por favor dense prisa."},
            {"role": "nurse",   "text": "El médico viene ahora mismo. Mantenga la calma."},
        ],
        "status": "waiting",
        "checked_in_at": datetime.now(timezone.utc) - timedelta(minutes=3),
    },

    # ── 8. HIGH ────────────────────────────────────────────────────────────
    {
        "name": "Miguel Torres",
        "language_code": "es", "language_name": "Spanish",
        "chief_complaint": "Severe eye pain and blurred vision",
        "symptoms": ["eye pain", "blurred vision", "headache", "nausea", "red eye"],
        "pain_level": 8,
        "allergies": [],
        "current_medications": ["eye drops for glaucoma"],
        "severity_score": 8,
        "risk_level": "high",
        "clinical_summary": (
            "CHIEF COMPLAINT: Sudden severe right eye pain with blurred vision and halos\n"
            "HISTORY: Sudden onset right eye pain 1 hour ago. Reports seeing halos around lights, "
            "blurred vision, associated nausea and frontal headache. Known glaucoma patient.\n"
            "PAIN LEVEL: 8/10\n"
            "ALLERGIES: None known\n"
            "CURRENT MEDICATIONS: Glaucoma eye drops (name unknown)\n"
            "CLINICAL NOTES: Presentation consistent with acute angle-closure glaucoma. "
            "Urgent IOP measurement and ophthalmology consult required."
        ),
        "conversation_english": [
            {"role": "nurse",   "text": "Hello, I am MedRover. What brings you in today?"},
            {"role": "patient", "text": "I have terrible pain in my right eye and I can barely see. Everything is blurry."},
            {"role": "nurse",   "text": "Did this come on suddenly? Are you seeing halos around lights?"},
            {"role": "patient", "text": "Yes very suddenly, about an hour ago. Yes I see halos and I feel nauseous."},
            {"role": "nurse",   "text": "Do you have any eye conditions or take any eye medications?"},
            {"role": "patient", "text": "I have glaucoma. I use eye drops for it every day."},
            {"role": "nurse",   "text": "How severe is the pain from 1 to 10?"},
            {"role": "patient", "text": "An 8. It is the worst eye pain I have ever had."},
            {"role": "nurse",   "text": "The doctor will see you immediately. [INTAKE_COMPLETE]"},
        ],
        "conversation_native": [
            {"role": "nurse",   "text": "Hola, soy MedRover. ¿Qué le trae por aquí hoy?"},
            {"role": "patient", "text": "Tengo un dolor terrible en el ojo derecho y casi no puedo ver. Todo está borroso."},
            {"role": "nurse",   "text": "¿Apareció de repente? ¿Ve halos alrededor de las luces?"},
            {"role": "patient", "text": "Sí, muy de repente, hace como una hora. Sí veo halos y tengo náuseas."},
            {"role": "nurse",   "text": "¿Tiene alguna condición ocular o toma medicamentos para los ojos?"},
            {"role": "patient", "text": "Tengo glaucoma. Uso gotas para los ojos todos los días."},
            {"role": "nurse",   "text": "¿Qué tan fuerte es el dolor del 1 al 10?"},
            {"role": "patient", "text": "Un 8. Es el peor dolor de ojos que he tenido."},
            {"role": "nurse",   "text": "El médico le atenderá de inmediato."},
        ],
        "status": "waiting",
        "checked_in_at": datetime.now(timezone.utc) - timedelta(minutes=8),
    },

    # ── 9. MEDIUM ──────────────────────────────────────────────────────────
    {
        "name": "Lucia Ramirez",
        "language_code": "es", "language_name": "Spanish",
        "chief_complaint": "Urinary burning and frequent urination for 3 days",
        "symptoms": ["burning urination", "frequent urination", "lower abdominal discomfort", "cloudy urine"],
        "pain_level": 4,
        "allergies": ["sulfa drugs"],
        "current_medications": [],
        "severity_score": 5,
        "risk_level": "medium",
        "clinical_summary": (
            "CHIEF COMPLAINT: Dysuria and urinary frequency for 3 days\n"
            "HISTORY: Gradual onset burning sensation on urination and increased frequency "
            "over 3 days. Reports cloudy urine. No fever. No flank pain.\n"
            "PAIN LEVEL: 4/10\n"
            "ALLERGIES: Sulfa drugs\n"
            "CURRENT MEDICATIONS: None\n"
            "CLINICAL NOTES: Presentation consistent with uncomplicated UTI. "
            "Sulfa allergy noted — avoid trimethoprim-sulfamethoxazole. Consider nitrofurantoin."
        ),
        "conversation_english": [
            {"role": "nurse",   "text": "Hello, I am MedRover. What brings you in today?"},
            {"role": "patient", "text": "It burns when I urinate and I have to go very frequently. It has been 3 days."},
            {"role": "nurse",   "text": "Do you have any fever or pain in your back or sides?"},
            {"role": "patient", "text": "No fever. No back pain. Just burning and my urine looks cloudy."},
            {"role": "nurse",   "text": "How would you rate the discomfort from 1 to 10?"},
            {"role": "patient", "text": "About a 4."},
            {"role": "nurse",   "text": "Any medication allergies?"},
            {"role": "patient", "text": "Yes I am allergic to sulfa drugs."},
            {"role": "nurse",   "text": "Thank you. The doctor will be with you shortly. [INTAKE_COMPLETE]"},
        ],
        "conversation_native": [
            {"role": "nurse",   "text": "Hola, soy MedRover. ¿Qué le trae por aquí hoy?"},
            {"role": "patient", "text": "Me arde cuando orino y tengo que ir muy seguido. Lleva 3 días así."},
            {"role": "nurse",   "text": "¿Tiene fiebre o dolor en la espalda o los costados?"},
            {"role": "patient", "text": "Sin fiebre. Sin dolor de espalda. Solo ardor y la orina se ve turbia."},
            {"role": "nurse",   "text": "¿Cómo calificaría el malestar del 1 al 10?"},
            {"role": "patient", "text": "Como un 4."},
            {"role": "nurse",   "text": "¿Tiene alergias a medicamentos?"},
            {"role": "patient", "text": "Sí, soy alérgica a las sulfas."},
            {"role": "nurse",   "text": "Gracias. El médico estará con usted pronto."},
        ],
        "status": "waiting",
        "checked_in_at": datetime.now(timezone.utc) - timedelta(minutes=25),
    },

    # ── 10. LOW ────────────────────────────────────────────────────────────
    {
        "name": "Pedro Guzman",
        "language_code": "es", "language_name": "Spanish",
        "chief_complaint": "Minor cut on hand needing wound check",
        "symptoms": ["laceration on right hand", "minor bleeding"],
        "pain_level": 2,
        "allergies": [],
        "current_medications": [],
        "severity_score": 2,
        "risk_level": "low",
        "clinical_summary": (
            "CHIEF COMPLAINT: Small laceration on right palm from kitchen knife\n"
            "HISTORY: Accidental knife cut while cooking approximately 30 minutes ago. "
            "Bleeding controlled with pressure. No tendon or nerve involvement reported. "
            "Tetanus status unknown.\n"
            "PAIN LEVEL: 2/10\n"
            "ALLERGIES: None known\n"
            "CURRENT MEDICATIONS: None\n"
            "CLINICAL NOTES: Low acuity wound. Assess for closure needs and tetanus status."
        ),
        "conversation_english": [
            {"role": "nurse",   "text": "Hello, I am MedRover. What brings you in today?"},
            {"role": "patient", "text": "I cut my hand on a knife while cooking. It stopped bleeding but I want it checked."},
            {"role": "nurse",   "text": "Can you move your fingers normally? Any numbness?"},
            {"role": "patient", "text": "Yes I can move them fine. No numbness."},
            {"role": "nurse",   "text": "How severe is the pain from 1 to 10?"},
            {"role": "patient", "text": "Just a 2. It is not too bad."},
            {"role": "nurse",   "text": "Any allergies or medications?"},
            {"role": "patient", "text": "No allergies. No medications."},
            {"role": "nurse",   "text": "Thank you. The doctor will clean and assess the wound shortly. [INTAKE_COMPLETE]"},
        ],
        "conversation_native": [
            {"role": "nurse",   "text": "Hola, soy MedRover. ¿Qué le trae por aquí hoy?"},
            {"role": "patient", "text": "Me corté la mano con un cuchillo mientras cocinaba. Ya dejó de sangrar pero quiero que lo revisen."},
            {"role": "nurse",   "text": "¿Puede mover los dedos normalmente? ¿Tiene entumecimiento?"},
            {"role": "patient", "text": "Sí los muevo bien. Sin entumecimiento."},
            {"role": "nurse",   "text": "¿Qué tan fuerte es el dolor del 1 al 10?"},
            {"role": "patient", "text": "Solo un 2. No está tan mal."},
            {"role": "nurse",   "text": "¿Tiene alergias o medicamentos?"},
            {"role": "patient", "text": "Sin alergias. Sin medicamentos."},
            {"role": "nurse",   "text": "Gracias. El médico limpiará y evaluará la herida pronto."},
        ],
        "status": "done",
        "checked_in_at": datetime.now(timezone.utc) - timedelta(hours=1),
    },

    # ── 11. HIGH ───────────────────────────────────────────────────────────
    {
        "name": "Carmen Flores",
        "language_code": "es", "language_name": "Spanish",
        "chief_complaint": "Severe migraine with vomiting unresponsive to medication",
        "symptoms": ["severe headache", "vomiting", "light sensitivity", "visual aura"],
        "pain_level": 9,
        "allergies": ["codeine"],
        "current_medications": ["sumatriptan", "metoclopramide"],
        "severity_score": 7,
        "risk_level": "high",
        "clinical_summary": (
            "CHIEF COMPLAINT: Severe migraine with vomiting, not responding to home medications\n"
            "HISTORY: Known migraineur. Current attack started 6 hours ago with visual aura. "
            "Took sumatriptan and metoclopramide with no relief. Multiple vomiting episodes. "
            "Photophobia present.\n"
            "PAIN LEVEL: 9/10\n"
            "ALLERGIES: Codeine\n"
            "CURRENT MEDICATIONS: Sumatriptan, Metoclopramide\n"
            "CLINICAL NOTES: Refractory migraine requiring IV treatment. "
            "Codeine allergy noted. Consider IV ketorolac and prochlorperazine."
        ),
        "conversation_english": [
            {"role": "nurse",   "text": "Hello, I am MedRover. What brings you in today?"},
            {"role": "patient", "text": "I have a terrible migraine. I have been vomiting for hours and my medication is not working."},
            {"role": "nurse",   "text": "How long has this migraine been going on and did you have any warning signs?"},
            {"role": "patient", "text": "About 6 hours. I had flashing lights in my vision before it started."},
            {"role": "nurse",   "text": "What medications did you take and how severe is the pain?"},
            {"role": "patient", "text": "Sumatriptan and metoclopramide. Nothing helped. Pain is a 9 out of 10."},
            {"role": "nurse",   "text": "Any medication allergies?"},
            {"role": "patient", "text": "Yes I am allergic to codeine."},
            {"role": "nurse",   "text": "Thank you. The doctor will see you soon. [INTAKE_COMPLETE]"},
        ],
        "conversation_native": [
            {"role": "nurse",   "text": "Hola, soy MedRover. ¿Qué le trae por aquí hoy?"},
            {"role": "patient", "text": "Tengo una migraña terrible. Llevo horas vomitando y mi medicamento no funciona."},
            {"role": "nurse",   "text": "¿Hace cuánto tiene esta migraña y tuvo alguna señal de advertencia?"},
            {"role": "patient", "text": "Unas 6 horas. Tuve luces parpadeantes en mi visión antes de que empezara."},
            {"role": "nurse",   "text": "¿Qué medicamentos tomó y qué tan fuerte es el dolor?"},
            {"role": "patient", "text": "Sumatriptán y metoclopramida. Nada ayudó. El dolor es un 9 de 10."},
            {"role": "nurse",   "text": "¿Tiene alergias a medicamentos?"},
            {"role": "patient", "text": "Sí soy alérgica a la codeína."},
            {"role": "nurse",   "text": "Gracias. El médico le atenderá pronto."},
        ],
        "status": "waiting",
        "checked_in_at": datetime.now(timezone.utc) - timedelta(minutes=15),
    },
]


def seed():
    col = _get_collection()
    now = datetime.now(timezone.utc)

    # Warn if data already exists
    existing = col.count_documents({})
    if existing > 0:
        confirm = input(f"  Collection already has {existing} documents. Add anyway? (y/n): ").strip().lower()
        if confirm != "y":
            print("  Aborted.")
            return

    for i, p in enumerate(PATIENTS):
        session_id = f"P{col.count_documents({}) + 1:03d}"
        doc = {
            "session_id":           session_id,
            "name":                 p["name"],
            "checked_in_at":        p["checked_in_at"],
            "language_code":        p["language_code"],
            "language_name":        p["language_name"],
            "chief_complaint":      p["chief_complaint"],
            "symptoms":             p["symptoms"],
            "pain_level":           p["pain_level"],
            "allergies":            p["allergies"],
            "current_medications":  p["current_medications"],
            "severity_score":       p["severity_score"],
            "risk_level":           p["risk_level"],
            "conversation_english": p["conversation_english"],
            "conversation_native":  p["conversation_native"],
            "clinical_summary":     p["clinical_summary"],
            "status":               p["status"],
            "created_at":           now,
            "updated_at":           now,
        }
        col.insert_one(doc)
        print(f"  ✓ {session_id}  {p['name']:<20}  {p['risk_level'].upper():<10}  score={p['severity_score']}")

    print(f"\n  Seeded {len(PATIENTS)} patients successfully.")


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  MedRover — Seed Database")
    print("=" * 55)
    seed()
