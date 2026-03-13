"use client";

import { MapPin, Check, X, ExternalLink } from "lucide-react";

interface MedicineCardProps {
  medicine: string;
  pharmacy: string;
  price: string;
  currency: string;
  address?: string;
  distance?: string;
  available: boolean;
  mapLink?: string;
}

export default function MedicineCard({
  medicine,
  pharmacy,
  price,
  currency,
  address,
  distance,
  available,
  mapLink,
}: MedicineCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 p-3 hover:border-blue-200 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h4 className="text-sm font-semibold text-gray-900">{medicine}</h4>
          <p className="text-xs text-gray-500">{pharmacy}</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-bold text-gray-900">
            {price} {currency}
          </p>
          {available ? (
            <span className="inline-flex items-center gap-0.5 text-xs text-green-600">
              <Check className="h-3 w-3" />
              In Stock
            </span>
          ) : (
            <span className="inline-flex items-center gap-0.5 text-xs text-red-500">
              <X className="h-3 w-3" />
              Unavailable
            </span>
          )}
        </div>
      </div>

      {(address || distance) && (
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span className="flex items-center gap-1 truncate">
            <MapPin className="h-3 w-3 flex-shrink-0" />
            {address || "Address not available"}
          </span>
          <div className="flex items-center gap-2 ml-2 flex-shrink-0">
            {distance && <span>{distance}</span>}
            {mapLink && (
              <a
                href={mapLink}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-0.5 text-blue-600 hover:text-blue-800"
              >
                <ExternalLink className="h-3 w-3" />
                Map
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
