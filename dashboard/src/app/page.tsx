"use client";

import { useState } from "react";
import DashboardShell from "@/components/layout/DashboardShell";
import PanelCard from "@/components/layout/PanelCard";
import IntakeSummary from "@/components/intake/IntakeSummary";
import VideoPanel from "@/components/video/VideoPanel";
import DoctorNotePanel from "@/components/notes/DoctorNotePanel";
import PriceLookupPanel from "@/components/pricing/PriceLookupPanel";
import { usePatientData } from "@/hooks/usePatientData";
import { ClipboardList, Video, FileText, DollarSign } from "lucide-react";

export default function Dashboard() {
  const { patient, intakeSession, relaySession, prescription, isLoading, mutate } = usePatientData();
  const [noteStatus, setNoteStatus] = useState<"draft" | "confirmed">("draft");

  return (
    <DashboardShell
      patientName={patient?.name}
      patientLanguage={patient?.language}
    >
      {/* Top Left: Patient Intake Summary */}
      <PanelCard title="Patient Intake Summary" icon={<ClipboardList className="h-4 w-4" />}>
        <IntakeSummary
          patient={patient}
          session={intakeSession}
          isLoading={isLoading}
        />
      </PanelCard>

      {/* Top Right: Live Video Feed */}
      <PanelCard title="Live Video Feed" icon={<Video className="h-4 w-4" />}>
        <VideoPanel patientId={patient?._id} />
      </PanelCard>

      {/* Bottom Left: Doctor Note */}
      <PanelCard title="Doctor Note" icon={<FileText className="h-4 w-4" />}>
        <DoctorNotePanel
          patient={patient}
          intakeSession={intakeSession}
          relaySession={relaySession}
          prescription={prescription}
          onStatusChange={(status) => {
            setNoteStatus(status);
            mutate();
          }}
        />
      </PanelCard>

      {/* Bottom Right: Medicine Price Lookup */}
      <PanelCard title="Medicine Price Lookup" icon={<DollarSign className="h-4 w-4" />}>
        <PriceLookupPanel
          prescription={prescription}
          noteConfirmed={noteStatus === "confirmed" || prescription?.status === "confirmed"}
          onLookupComplete={() => mutate()}
        />
      </PanelCard>
    </DashboardShell>
  );
}
