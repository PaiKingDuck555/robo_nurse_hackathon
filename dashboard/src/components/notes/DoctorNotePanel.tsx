"use client";

import { useState, useEffect } from "react";
import NoteEditor from "./NoteEditor";
import NoteActions from "./NoteActions";

interface DoctorNotePanelProps {
  patient: any;
  intakeSession: any;
  relaySession: any;
  prescription: any;
  onStatusChange: (status: "draft" | "confirmed") => void;
}

export default function DoctorNotePanel({
  patient,
  intakeSession,
  relaySession,
  prescription,
  onStatusChange,
}: DoctorNotePanelProps) {
  const [noteText, setNoteText] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [prescriptionId, setPrescriptionId] = useState<string | null>(null);
  const [isConfirmed, setIsConfirmed] = useState(false);

  // Sync with prescription data from server
  useEffect(() => {
    if (prescription) {
      setNoteText(prescription.fullNoteText || "");
      setPrescriptionId(prescription._id);
      setIsConfirmed(prescription.status === "confirmed");
    }
  }, [prescription]);

  const handleGenerate = async () => {
    if (!patient?._id) return;

    setIsGenerating(true);
    try {
      const res = await fetch("/api/notes/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patientId: patient._id }),
      });
      const data = await res.json();
      if (data.prescription) {
        setNoteText(data.prescription.fullNoteText || "");
        setPrescriptionId(data.prescription._id);
        setIsConfirmed(false);
        onStatusChange("draft");
      }
    } catch (err) {
      console.error("Failed to generate note:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!prescriptionId) return;

    setIsSaving(true);
    try {
      await fetch(`/api/notes/${prescriptionId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fullNoteText: noteText, status: "draft" }),
      });
    } catch (err) {
      console.error("Failed to save note:", err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleConfirm = async () => {
    if (!prescriptionId) return;

    setIsSaving(true);
    try {
      await fetch(`/api/notes/${prescriptionId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fullNoteText: noteText, status: "confirmed" }),
      });
      setIsConfirmed(true);
      onStatusChange("confirmed");
    } catch (err) {
      console.error("Failed to confirm note:", err);
    } finally {
      setIsSaving(false);
    }
  };

  if (!patient || !intakeSession) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <p className="text-sm">Waiting for patient intake data to generate a note...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full gap-3">
      <NoteActions
        onGenerate={handleGenerate}
        onSave={handleSave}
        onConfirm={handleConfirm}
        isGenerating={isGenerating}
        isSaving={isSaving}
        hasNote={noteText.length > 0}
        isConfirmed={isConfirmed}
        canGenerate={!!patient && !!intakeSession}
      />
      <div className="flex-1 min-h-0">
        <NoteEditor
          value={noteText}
          onChange={setNoteText}
          disabled={isConfirmed}
        />
      </div>
    </div>
  );
}
