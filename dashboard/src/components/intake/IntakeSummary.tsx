"use client";

import PatientInfo from "./PatientInfo";
import UrgencyBadge from "./UrgencyBadge";
import SymptomList from "./SymptomList";
import ClinicalSummary from "./ClinicalSummary";
import TranscriptView from "./TranscriptView";
import { Loader2 } from "lucide-react";

interface IntakeSummaryProps {
  patient: any;
  session: any;
  isLoading: boolean;
}

export default function IntakeSummary({ patient, session, isLoading }: IntakeSummaryProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-2">
        <Loader2 className="h-6 w-6 animate-spin" />
        <p className="text-sm">Loading patient data...</p>
      </div>
    );
  }

  if (!patient || !session) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-2">
        <p className="text-sm">Waiting for robot to complete patient intake...</p>
        <p className="text-xs">Data will appear automatically when a session is recorded.</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <div className="flex items-start justify-between">
        <PatientInfo
          name={patient.name}
          language={patient.language}
          age={patient.age}
          country={patient.country}
        />
        <UrgencyBadge level={session.urgencyLevel || "medium"} />
      </div>

      <SymptomList
        symptoms={session.symptoms || []}
        painLevel={session.painLevel || 0}
        allergies={session.allergies || []}
        medications={session.currentMedications || []}
        mentalHealthFlags={session.mentalHealthFlags || []}
      />

      {session.clinicalSummary && (
        <ClinicalSummary summary={session.clinicalSummary} />
      )}

      {session.qaPairs && session.qaPairs.length > 0 && (
        <TranscriptView qaPairs={session.qaPairs} />
      )}
    </div>
  );
}
