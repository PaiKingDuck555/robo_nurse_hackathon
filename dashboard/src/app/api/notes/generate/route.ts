import { NextRequest, NextResponse } from "next/server";
import { upsertPrescription } from "@/lib/dummy-data";
import { generateDoctorNote } from "@/lib/claude";
import {
  fetchWaitingPatients,
  transformToPatient,
  transformToIntakeSession,
} from "@/lib/railway";

export async function POST(request: NextRequest) {
  const { patientId } = await request.json();

  if (!patientId) {
    return NextResponse.json(
      { error: "patientId is required" },
      { status: 400 }
    );
  }

  try {
    // Fetch all waiting patients and find the one matching patientId
    const waiting = await fetchWaitingPatients();
    const railwaySession = waiting.find((s) => s.session_id === patientId);

    if (!railwaySession) {
      return NextResponse.json(
        { error: "Patient not found in Railway" },
        { status: 404 }
      );
    }

    const patient = transformToPatient(railwaySession);
    const intake = transformToIntakeSession(railwaySession);

    // Build relay transcript from the intake conversation_english
    // (the nurse-patient intake conversation acts as context)
    const intakeConversationAsTranscript = railwaySession.conversation_english.map(
      (turn, i) => ({
        speaker: turn.role === "nurse" ? "doctor" : "patient",
        textOriginal:
          railwaySession.conversation_native[i]?.text || turn.text,
        textTranslated: turn.text,
      })
    );

    // Use relay transcript from the session if available, otherwise use intake conversation
    const relayTranscript = intake.relayTranscript?.length
      ? intake.relayTranscript
      : intakeConversationAsTranscript;

    const note = await generateDoctorNote(
      intake.clinicalSummary || "",
      relayTranscript,
      patient.name,
      patient.language
    );

    const prescription = upsertPrescription({
      patientId,
      intakeSessionId: intake._id,
      ...note,
      status: "draft",
    });

    return NextResponse.json({ prescription });
  } catch (err: any) {
    console.error("Doctor note generation failed:", err);
    return NextResponse.json(
      { error: err.message || "Failed to generate doctor note" },
      { status: 500 }
    );
  }
}
