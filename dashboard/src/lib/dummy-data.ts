/**
 * In-memory dummy data store.
 * Replaces MongoDB — everything lives in memory and resets on server restart.
 */

export interface Patient {
  _id: string;
  name: string;
  language: string;
  languageCode: string;
  age?: number;
  country?: string;
  createdAt: string;
  updatedAt: string;
}

export interface QAPair {
  question: string;
  questionNative: string;
  answer: string;
  answerNative: string;
}

export interface RelayMessage {
  speaker: "doctor" | "patient";
  textOriginal: string;
  textTranslated: string;
  timestamp: string;
}

export interface Session {
  _id: string;
  patientId: string;
  type: "intake" | "relay";
  status: "in_progress" | "completed";
  qaPairs: QAPair[];
  clinicalSummary: string;
  symptoms: string[];
  painLevel: number;
  allergies: string[];
  currentMedications: string[];
  mentalHealthFlags: string[];
  urgencyLevel: "low" | "medium" | "high" | "critical";
  relayTranscript: RelayMessage[];
  startedAt: string;
  completedAt?: string;
}

export interface MedicinePrice {
  medicine: string;
  pharmacy: string;
  price: string;
  currency: string;
  address?: string;
  distance?: string;
  available: boolean;
  mapLink?: string;
}

export interface Prescription {
  _id: string;
  patientId: string;
  intakeSessionId: string;
  relaySessionId?: string;
  diagnosis: string;
  prescribedMedications: string[];
  instructions: string;
  followUp: string;
  additionalNotes: string;
  fullNoteText: string;
  status: "draft" | "confirmed";
  priceLookupResults: MedicinePrice[];
  priceLookupCompleted: boolean;
  createdAt: string;
  updatedAt: string;
}

// ─── Seed Data ───────────────────────────────────────────────

const PATIENT_ID = "p_001";
const INTAKE_SESSION_ID = "s_001";

export const patients: Patient[] = [
  {
    _id: PATIENT_ID,
    name: "Maria Garcia",
    language: "Spanish",
    languageCode: "es",
    age: 34,
    country: "Mexico",
    createdAt: new Date(Date.now() - 1200000).toISOString(),
    updatedAt: new Date(Date.now() - 600000).toISOString(),
  },
];

export const sessions: Session[] = [
  {
    _id: INTAKE_SESSION_ID,
    patientId: PATIENT_ID,
    type: "intake",
    status: "completed",
    qaPairs: [
      {
        question: "What are your main symptoms today?",
        questionNative: "¿Cuáles son sus síntomas principales hoy?",
        answer:
          "I have a persistent headache for three days, and I feel nauseous in the morning.",
        answerNative:
          "Tengo un dolor de cabeza persistente por tres días, y me siento con náuseas en la mañana.",
      },
      {
        question: "How long have you had these symptoms?",
        questionNative: "¿Cuánto tiempo ha tenido estos síntomas?",
        answer:
          "The headache started three days ago. The nausea started yesterday.",
        answerNative:
          "El dolor de cabeza empezó hace tres días. Las náuseas empezaron ayer.",
      },
      {
        question:
          "On a scale of 1 to 10, how severe is your pain or discomfort?",
        questionNative:
          "En una escala del 1 al 10, ¿qué tan severo es su dolor o malestar?",
        answer:
          "About a 7. The headache is very strong, especially behind my eyes.",
        answerNative:
          "Como un 7. El dolor de cabeza es muy fuerte, especialmente detrás de mis ojos.",
      },
      {
        question: "Do you have any known allergies to medications?",
        questionNative: "¿Tiene alguna alergia conocida a medicamentos?",
        answer: "I am allergic to penicillin. It gives me a rash.",
        answerNative: "Soy alérgica a la penicilina. Me da sarpullido.",
      },
      {
        question:
          "Are you currently taking any medications or supplements?",
        questionNative:
          "¿Está tomando algún medicamento o suplemento actualmente?",
        answer:
          "I take ibuprofen sometimes for the headache, and I take vitamin D daily.",
        answerNative:
          "Tomo ibuprofeno a veces para el dolor de cabeza, y tomo vitamina D diariamente.",
      },
    ],
    clinicalSummary:
      "CHIEF COMPLAINT: Persistent headache (3 days) with morning nausea (1 day)\n\nHISTORY: Patient reports a 3-day history of severe headache localized behind the eyes, with associated morning nausea beginning yesterday. No history of trauma or recent illness reported.\n\nPAIN LEVEL: 7/10\n\nALLERGIES: Penicillin (causes rash)\n\nCURRENT MEDICATIONS: Ibuprofen (PRN for headache), Vitamin D (daily)\n\nNOTES: Retroorbital headache pattern with nausea may suggest migraine, tension headache, or elevated intracranial pressure. Consider neurological exam and further workup if symptoms persist.",
    symptoms: [
      "Persistent headache (3 days)",
      "Morning nausea (1 day)",
      "Retroorbital pain",
    ],
    painLevel: 7,
    allergies: ["Penicillin"],
    currentMedications: ["Ibuprofen (PRN)", "Vitamin D (daily)"],
    mentalHealthFlags: [],
    urgencyLevel: "medium",
    relayTranscript: [],
    startedAt: new Date(Date.now() - 1200000).toISOString(),
    completedAt: new Date(Date.now() - 600000).toISOString(),
  },
];

export const prescriptions: Prescription[] = [];

// ─── Helper functions (mutate in-memory arrays) ─────────────

export function getLatestPatient() {
  return patients[patients.length - 1] || null;
}

export function getPatientById(id: string) {
  return patients.find((p) => p._id === id) || null;
}

export function getSessionsForPatient(patientId: string) {
  return {
    intake: sessions.find((s) => s.patientId === patientId && s.type === "intake") || null,
    relay: sessions.find((s) => s.patientId === patientId && s.type === "relay") || null,
  };
}

export function getPrescriptionForPatient(patientId: string) {
  return prescriptions.find((p) => p.patientId === patientId) || null;
}

export function getPrescriptionById(id: string) {
  return prescriptions.find((p) => p._id === id) || null;
}

export function upsertPrescription(data: Partial<Prescription> & { patientId: string }) {
  const existing = prescriptions.find((p) => p.patientId === data.patientId);
  if (existing) {
    Object.assign(existing, data, { updatedAt: new Date().toISOString() });
    return existing;
  }

  const newRx: Prescription = {
    _id: `rx_${Date.now()}`,
    patientId: data.patientId,
    intakeSessionId: data.intakeSessionId || INTAKE_SESSION_ID,
    diagnosis: data.diagnosis || "",
    prescribedMedications: data.prescribedMedications || [],
    instructions: data.instructions || "",
    followUp: data.followUp || "",
    additionalNotes: data.additionalNotes || "",
    fullNoteText: data.fullNoteText || "",
    status: data.status || "draft",
    priceLookupResults: data.priceLookupResults || [],
    priceLookupCompleted: data.priceLookupCompleted || false,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  prescriptions.push(newRx);
  return newRx;
}

export function updatePrescription(id: string, data: Partial<Prescription>) {
  const rx = prescriptions.find((p) => p._id === id);
  if (!rx) return null;
  Object.assign(rx, data, { updatedAt: new Date().toISOString() });
  return rx;
}
