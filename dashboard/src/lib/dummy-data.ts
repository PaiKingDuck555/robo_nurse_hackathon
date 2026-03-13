/**
 * In-memory data store.
 * Patient/Session data now comes from Railway API.
 * Only prescriptions are kept in local memory.
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
  zipcode?: string;
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
  phoneNumber?: string;
  openingHours?: string;
  prescriptionRequired?: boolean;
  genericAlternative?: string;
  genericPrice?: string;
  deliveryAvailable?: boolean;
  pharmacyType?: string;
  dosageMatch?: string;
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

// ─── In-memory prescription store ───────────────────────────

export const prescriptions: Prescription[] = [];

// ─── Prescription helpers ───────────────────────────────────

export function getPrescriptionForPatient(patientId: string) {
  return prescriptions.find((p) => p.patientId === patientId) || null;
}

export function getPrescriptionById(id: string) {
  return prescriptions.find((p) => p._id === id) || null;
}

export function upsertPrescription(
  data: Partial<Prescription> & { patientId: string }
) {
  const existing = prescriptions.find((p) => p.patientId === data.patientId);
  if (existing) {
    Object.assign(existing, data, { updatedAt: new Date().toISOString() });
    return existing;
  }

  const newRx: Prescription = {
    _id: `rx_${Date.now()}`,
    patientId: data.patientId,
    intakeSessionId: data.intakeSessionId || "",
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
