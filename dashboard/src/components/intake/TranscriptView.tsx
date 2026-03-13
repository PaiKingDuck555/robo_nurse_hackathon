"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, MessageSquare } from "lucide-react";
import clsx from "clsx";

interface QAPair {
  question: string;
  questionNative: string;
  answer: string;
  answerNative: string;
}

interface TranscriptViewProps {
  qaPairs: QAPair[];
}

export default function TranscriptView({ qaPairs }: TranscriptViewProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wide hover:text-gray-700 transition-colors"
      >
        {isOpen ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <MessageSquare className="h-3.5 w-3.5" />
        Full Transcript ({qaPairs.length} exchanges)
      </button>

      <div
        className={clsx(
          "overflow-hidden transition-all duration-200",
          isOpen ? "max-h-[2000px] mt-2" : "max-h-0"
        )}
      >
        <div className="space-y-3">
          {qaPairs.map((pair, i) => (
            <div key={i} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <div className="mb-2">
                <p className="text-xs font-medium text-blue-600 mb-0.5">Q{i + 1}: {pair.question}</p>
                <p className="text-xs text-gray-400 italic">{pair.questionNative}</p>
              </div>
              <div>
                <p className="text-sm text-gray-800">{pair.answer}</p>
                <p className="text-xs text-gray-400 italic mt-0.5">{pair.answerNative}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
