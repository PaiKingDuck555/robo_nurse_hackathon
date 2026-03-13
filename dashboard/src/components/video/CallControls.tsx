"use client";

import { Phone, PhoneOff, Mic, MicOff } from "lucide-react";
import clsx from "clsx";

type ConnectionStatus = "disconnected" | "connecting" | "connected";

interface CallControlsProps {
  status: ConnectionStatus;
  isMuted: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
  onToggleMute: () => void;
}

export default function CallControls({ status, isMuted, onConnect, onDisconnect, onToggleMute }: CallControlsProps) {
  return (
    <div className="flex items-center justify-between">
      {/* Status indicator */}
      <div className="flex items-center gap-2">
        <span
          className={clsx("h-2 w-2 rounded-full", {
            "bg-gray-400": status === "disconnected",
            "bg-yellow-400 animate-pulse": status === "connecting",
            "bg-green-500": status === "connected",
          })}
        />
        <span className="text-xs text-gray-500 capitalize">{status}</span>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2">
        {status === "connected" && (
          <button
            onClick={onToggleMute}
            className={clsx(
              "flex h-8 w-8 items-center justify-center rounded-full transition-colors",
              isMuted ? "bg-red-100 text-red-600 hover:bg-red-200" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            )}
          >
            {isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </button>
        )}

        {status === "disconnected" ? (
          <button
            onClick={onConnect}
            className="flex items-center gap-1.5 rounded-full bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 transition-colors"
          >
            <Phone className="h-3.5 w-3.5" />
            Connect
          </button>
        ) : (
          <button
            onClick={onDisconnect}
            className="flex items-center gap-1.5 rounded-full bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 transition-colors"
          >
            <PhoneOff className="h-3.5 w-3.5" />
            End
          </button>
        )}
      </div>
    </div>
  );
}
