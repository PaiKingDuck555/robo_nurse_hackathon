import { NextRequest, NextResponse } from "next/server";
import { getPrescriptionForPatient } from "@/lib/dummy-data";
import {
  fetchWaitingPatients,
  transformToPatient,
  transformToIntakeSession,
} from "@/lib/railway";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const waiting = await fetchWaitingPatients();
    const railwaySession = waiting.find((s) => s.session_id === id);

    if (!railwaySession) {
      return NextResponse.json({ error: "Patient not found" }, { status: 404 });
    }

    const patient = transformToPatient(railwaySession);
    const intakeSession = transformToIntakeSession(railwaySession);
    const prescription = getPrescriptionForPatient(id);

    return NextResponse.json({
      patient,
      intakeSession,
      relaySession: null,
      prescription,
    });
  } catch (err: any) {
    console.error("Failed to fetch patient from Railway:", err.message);
    return NextResponse.json(
      { error: "Failed to fetch patient data" },
      { status: 502 }
    );
  }
}
