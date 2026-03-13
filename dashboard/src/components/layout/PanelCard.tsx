"use client";

import { ReactNode } from "react";
import clsx from "clsx";

interface PanelCardProps {
  title: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  headerRight?: ReactNode;
}

export default function PanelCard({ title, icon, children, className, headerRight }: PanelCardProps) {
  return (
    <div
      className={clsx(
        "flex flex-col rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden",
        className
      )}
    >
      <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50/50 px-5 py-3">
        <div className="flex items-center gap-2">
          {icon && <span className="text-blue-600">{icon}</span>}
          <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">{title}</h2>
        </div>
        {headerRight}
      </div>
      <div className="flex-1 overflow-y-auto p-5">{children}</div>
    </div>
  );
}
