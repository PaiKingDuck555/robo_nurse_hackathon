import { NextRequest, NextResponse } from "next/server";
import {
  fetchWaitingPatients,
  transformToPatient,
  transformToIntakeSession,
} from "@/lib/railway";
import { getPrescriptionForPatient } from "@/lib/dummy-data";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const latest = searchParams.get("latest");

  if (latest === "true") {
    try {
      const waiting = await fetchWaitingPatients();

      if (!waiting || waiting.length === 0) {
        return NextResponse.json({
          patient: null,
          intakeSession: null,
          relaySession: null,
          prescription: null,
        });
      }

      // First patient is highest severity (Railway sorts by severity_score desc)
      const rs = waiting[0];
      const patient = transformToPatient(rs);
      const intakeSession = transformToIntakeSession(rs);
      const prescription = getPrescriptionForPatient(patient._id);

      return NextResponse.json({
        patient,
        intakeSession,
        relaySession: null,
        prescription,
      });
    } catch (err: any) {
      console.error("Failed to fetch from Railway:", err.message);
      return NextResponse.json(
        { error: "Failed to fetch patient data from Railway" },
        { status: 502 }
      );
    }
  }

  // List all waiting patients
  try {
    const waiting = await fetchWaitingPatients();
    const patients = waiting.map(transformToPatient);
    return NextResponse.json({ patients });
  } catch (err: any) {
    console.error("Failed to fetch from Railway:", err.message);
    return NextResponse.json(
      { error: "Failed to fetch patients from Railway" },
      { status: 502 }
    );
  }
}
