"use client";

interface ClinicalSummaryProps {
  summary: string;
}

export default function ClinicalSummary({ summary }: ClinicalSummaryProps) {
  return (
    <div className="mb-4">
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">AI Clinical Summary</h4>
      <div className="rounded-lg bg-blue-50 border border-blue-100 p-3">
        <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">
          {summary}
        </pre>
      </div>
    </div>
  );
}
