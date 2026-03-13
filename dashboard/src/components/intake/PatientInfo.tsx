"use client";

import { User, Globe, Calendar } from "lucide-react";

interface PatientInfoProps {
  name: string;
  language: string;
  age?: number;
  country?: string;
}

export default function PatientInfo({ name, language, age, country }: PatientInfoProps) {
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 flex-shrink-0">
        <User className="h-5 w-5 text-blue-700" />
      </div>
      <div className="min-w-0">
        <h3 className="text-base font-semibold text-gray-900">{name}</h3>
        <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <Globe className="h-3 w-3" />
            {language}
          </span>
          {age && (
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {age} years old
            </span>
          )}
          {country && <span>{country}</span>}
        </div>
      </div>
    </div>
  );
}
