"use client";

import clsx from "clsx";

const urgencyConfig = {
  low: { label: "Low", bg: "bg-green-100", text: "text-green-800", dot: "bg-green-500" },
  medium: { label: "Medium", bg: "bg-yellow-100", text: "text-yellow-800", dot: "bg-yellow-500" },
  high: { label: "High", bg: "bg-orange-100", text: "text-orange-800", dot: "bg-orange-500" },
  critical: { label: "Critical", bg: "bg-red-100", text: "text-red-800", dot: "bg-red-500" },
};

interface UrgencyBadgeProps {
  level: "low" | "medium" | "high" | "critical";
}

export default function UrgencyBadge({ level }: UrgencyBadgeProps) {
  const config = urgencyConfig[level];
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        config.bg,
        config.text
      )}
    >
      <span className={clsx("h-1.5 w-1.5 rounded-full", config.dot)} />
      {config.label} Urgency
    </span>
  );
}
