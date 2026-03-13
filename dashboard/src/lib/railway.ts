/**
 * Railway API client — fetches live patient data from the Python FastAPI backend.
 */

import type { Patient, Session, QAPair } from "./dummy-data";

const BASE_URL =
  process.env.RAILWAY_API_URL ||
  "https://robonursehackathon-production.up.railway.app";

// ─── Raw Railway response types ─────────────────────────────

interface RailwayConversationTurn {
  role: "nurse" | "patient";
  text: string;
}

export interface RailwaySession {
  session_id: string;
  name: string;
  checked_in_at: string;
  language_code: string;
  language_name: string;
  chief_complaint: string;
  symptoms: string[];
  pain_level: number;
  allergies: string[];
  current_medications: string[];
  severity_score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  conversation_english: RailwayConversationTurn[];
  conversation_native: RailwayConversationTurn[];
  clinical_summary: string;
  zipcode?: string;
}

// ─── API helpers ────────────────────────────────────────────

export async function fetchWaitingPatients(): Promise<RailwaySession[]> {
  const res = await fetch(`${BASE_URL}/waiting`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Railway /waiting failed: ${res.status}`);
  return res.json();
}

export async function fetchSessionSummary(
  sessionId: string
): Promise<RailwaySession> {
  const res = await fetch(`${BASE_URL}/session/${sessionId}/summary`, {
    cache: "no-store",
  });
  if (!res.ok)
    throw new Error(`Railway /session/${sessionId}/summary failed: ${res.status}`);
  return res.json();
}

export async function fetchPatientsByName(
  name: string
): Promise<RailwaySession[]> {
  const res = await fetch(
    `${BASE_URL}/patients?name=${encodeURIComponent(name)}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error(`Railway /patients?name= failed: ${res.status}`);
  return res.json();
}

export async function relayDoctorMessage(
  sessionId: string,
  text: string
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/relay/${sessionId}/doctor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`Railway relay/doctor failed: ${res.status}`);
  return res.json();
}

export async function relayPatientMessage(
  sessionId: string,
  text: string
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/relay/${sessionId}/patient`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`Railway relay/patient failed: ${res.status}`);
  return res.json();
}

export async function updateSessionStatus(
  sessionId: string,
  status: string
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/session/${sessionId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok)
    throw new Error(`Railway session status update failed: ${res.status}`);
  return res.json();
}

// ─── Transform Railway → Dashboard shapes ───────────────────

function buildQAPairs(
  english: RailwayConversationTurn[],
  native: RailwayConversationTurn[]
): QAPair[] {
  const pairs: QAPair[] = [];

  for (let i = 0; i < english.length - 1; i += 2) {
    const nurseEn = english[i];
    const patientEn = english[i + 1];
    const nurseNat = native[i];
    const patientNat = native[i + 1];

    if (nurseEn?.role === "nurse" && patientEn?.role === "patient") {
      pairs.push({
        question: nurseEn.text,
        questionNative: nurseNat?.text || nurseEn.text,
        answer: patientEn.text,
        answerNative: patientNat?.text || patientEn.text,
      });
    }
  }

  return pairs;
}

function mapRiskToUrgency(
  risk: string
): "low" | "medium" | "high" | "critical" {
  switch (risk) {
    case "critical":
      return "critical";
    case "high":
      return "high";
    case "medium":
      return "medium";
    default:
      return "low";
  }
}

export function transformToPatient(rs: RailwaySession): Patient {
  return {
    _id: rs.session_id,
    name: rs.name,
    language: rs.language_name,
    languageCode: rs.language_code,
    createdAt: rs.checked_in_at,
    updatedAt: rs.checked_in_at,
  };
}

export function transformToIntakeSession(rs: RailwaySession): Session {
  return {
    _id: rs.session_id,
    patientId: rs.session_id,
    type: "intake",
    status: "completed",
    qaPairs: buildQAPairs(
      rs.conversation_english,
      rs.conversation_native
    ),
    clinicalSummary: rs.clinical_summary,
    symptoms: rs.symptoms,
    painLevel: rs.pain_level,
    allergies: rs.allergies,
    currentMedications: rs.current_medications,
    mentalHealthFlags: [],
    zipcode: rs.zipcode,
    urgencyLevel: mapRiskToUrgency(rs.risk_level),
    relayTranscript: [],
    startedAt: rs.checked_in_at,
    completedAt: rs.checked_in_at,
  };
}
