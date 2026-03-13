"use client";

import { ReactNode } from "react";
import { Activity } from "lucide-react";

interface DashboardShellProps {
  children: ReactNode;
  patientName?: string;
  patientLanguage?: string;
}

export default function DashboardShell({ children, patientName, patientLanguage }: DashboardShellProps) {
  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600">
            <Activity className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">MedRover Dashboard</h1>
            <p className="text-xs text-gray-500">Doctor Control Panel</p>
          </div>
        </div>

        {patientName && (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{patientName}</p>
              <p className="text-xs text-gray-500">{patientLanguage}</p>
            </div>
            <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
              <span className="text-sm font-semibold text-blue-700">
                {patientName.charAt(0).toUpperCase()}
              </span>
            </div>
          </div>
        )}
      </header>

      {/* 2x2 Grid */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 overflow-hidden">
        {children}
      </main>
    </div>
  );
}
