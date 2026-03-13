"use client";

import { Sparkles, Save, CheckCircle, Loader2 } from "lucide-react";
import clsx from "clsx";

interface NoteActionsProps {
  onGenerate: () => void;
  onSave: () => void;
  onConfirm: () => void;
  isGenerating: boolean;
  isSaving: boolean;
  hasNote: boolean;
  isConfirmed: boolean;
  canGenerate: boolean;
}

export default function NoteActions({
  onGenerate,
  onSave,
  onConfirm,
  isGenerating,
  isSaving,
  hasNote,
  isConfirmed,
  canGenerate,
}: NoteActionsProps) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={onGenerate}
        disabled={isGenerating || !canGenerate}
        className={clsx(
          "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
          isGenerating || !canGenerate
            ? "bg-gray-100 text-gray-400 cursor-not-allowed"
            : "bg-blue-600 text-white hover:bg-blue-700"
        )}
      >
        {isGenerating ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <Sparkles className="h-3.5 w-3.5" />
        )}
        {isGenerating ? "Generating..." : "Generate Note"}
      </button>

      {hasNote && !isConfirmed && (
        <>
          <button
            onClick={onSave}
            disabled={isSaving}
            className="flex items-center gap-1.5 rounded-lg bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200 transition-colors"
          >
            {isSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
            Save Draft
          </button>
          <button
            onClick={onConfirm}
            className="flex items-center gap-1.5 rounded-lg bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 transition-colors"
          >
            <CheckCircle className="h-3.5 w-3.5" />
            Confirm
          </button>
        </>
      )}

      {isConfirmed && (
        <span className="flex items-center gap-1.5 text-xs font-medium text-green-600">
          <CheckCircle className="h-3.5 w-3.5" />
          Confirmed
        </span>
      )}
    </div>
  );
}
