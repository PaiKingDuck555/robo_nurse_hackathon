import { NextRequest, NextResponse } from "next/server";
import {
  patients,
  getLatestPatient,
  getSessionsForPatient,
  getPrescriptionForPatient,
} from "@/lib/dummy-data";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const latest = searchParams.get("latest");

  if (latest === "true") {
    const patient = getLatestPatient();

    if (!patient) {
      return NextResponse.json({
        patient: null,
        intakeSession: null,
        relaySession: null,
        prescription: null,
      });
    }

    const { intake, relay } = getSessionsForPatient(patient._id);
    const prescription = getPrescriptionForPatient(patient._id);

    return NextResponse.json({
      patient,
      intakeSession: intake,
      relaySession: relay,
      prescription,
    });
  }

  return NextResponse.json({ patients });
}
