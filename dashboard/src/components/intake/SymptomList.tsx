"use client";

import { AlertCircle, Pill, ShieldAlert } from "lucide-react";

interface SymptomListProps {
  symptoms: string[];
  painLevel: number;
  allergies: string[];
  medications: string[];
  mentalHealthFlags: string[];
}

export default function SymptomList({
  symptoms,
  painLevel,
  allergies,
  medications,
  mentalHealthFlags,
}: SymptomListProps) {
  return (
    <div className="space-y-3 mb-4">
      {/* Symptoms */}
      <div>
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Symptoms</h4>
        <ul className="space-y-1">
          {symptoms.map((s, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
              <AlertCircle className="h-3.5 w-3.5 text-orange-500 mt-0.5 flex-shrink-0" />
              {s}
            </li>
          ))}
        </ul>
      </div>

      {/* Pain Level */}
      <div>
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Pain Level</h4>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${painLevel * 10}%`,
                backgroundColor:
                  painLevel <= 3 ? "#22c55e" : painLevel <= 6 ? "#eab308" : painLevel <= 8 ? "#f97316" : "#ef4444",
              }}
            />
          </div>
          <span className="text-sm font-semibold text-gray-700">{painLevel}/10</span>
        </div>
      </div>

      {/* Allergies */}
      {allergies.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Allergies</h4>
          <div className="flex flex-wrap gap-1.5">
            {allergies.map((a, i) => (
              <span key={i} className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700">
                <ShieldAlert className="h-3 w-3" />
                {a}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Medications */}
      {medications.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Current Medications</h4>
          <div className="flex flex-wrap gap-1.5">
            {medications.map((m, i) => (
              <span key={i} className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                <Pill className="h-3 w-3" />
                {m}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Mental Health Flags */}
      {mentalHealthFlags.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Mental Health Flags</h4>
          <div className="flex flex-wrap gap-1.5">
            {mentalHealthFlags.map((f, i) => (
              <span key={i} className="inline-flex items-center gap-1 rounded-full bg-purple-50 px-2 py-0.5 text-xs font-medium text-purple-700">
                {f}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
