"use client";

import MedicineCard from "./MedicineCard";

interface PricingResult {
  medicine: string;
  pharmacy: string;
  price: string;
  currency: string;
  address?: string;
  distance?: string;
  available: boolean;
  mapLink?: string;
}

interface PricingTableProps {
  results: PricingResult[];
}

export default function PricingTable({ results }: PricingTableProps) {
  if (results.length === 0) {
    return null;
  }

  // Group by medicine
  const grouped = results.reduce<Record<string, PricingResult[]>>((acc, r) => {
    if (!acc[r.medicine]) acc[r.medicine] = [];
    acc[r.medicine].push(r);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([medicine, items]) => (
        <div key={medicine}>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            {medicine}
          </h3>
          <div className="space-y-2">
            {items.map((item, i) => (
              <MedicineCard key={i} {...item} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
