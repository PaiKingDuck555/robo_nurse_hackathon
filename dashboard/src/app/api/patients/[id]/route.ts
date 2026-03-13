import { NextRequest, NextResponse } from "next/server";
import {
  getPatientById,
  getSessionsForPatient,
  getPrescriptionForPatient,
} from "@/lib/dummy-data";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  const patient = getPatientById(id);
  if (!patient) {
    return NextResponse.json({ error: "Patient not found" }, { status: 404 });
  }

  const { intake, relay } = getSessionsForPatient(id);
  const prescription = getPrescriptionForPatient(id);

  return NextResponse.json({
    patient,
    intakeSession: intake,
    relaySession: relay,
    prescription,
  });
}
