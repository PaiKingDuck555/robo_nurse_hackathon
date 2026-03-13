import { NextRequest, NextResponse } from "next/server";
import {
  getPatientById,
  getSessionsForPatient,
  upsertPrescription,
} from "@/lib/dummy-data";
import { generateDoctorNote } from "@/lib/claude";

export async function POST(request: NextRequest) {
  const { patientId } = await request.json();

  if (!patientId) {
    return NextResponse.json({ error: "patientId is required" }, { status: 400 });
  }

  const patient = getPatientById(patientId);
  if (!patient) {
    return NextResponse.json({ error: "Patient not found" }, { status: 404 });
  }

  const { intake, relay } = getSessionsForPatient(patientId);
  if (!intake) {
    return NextResponse.json({ error: "No completed intake session found" }, { status: 404 });
  }

  const note = await generateDoctorNote(
    intake.clinicalSummary || "",
    relay?.relayTranscript || [],
    patient.name,
    patient.language
  );

  const prescription = upsertPrescription({
    patientId,
    intakeSessionId: intake._id,
    relaySessionId: relay?._id,
    ...note,
    status: "draft",
  });

  return NextResponse.json({ prescription });
}
