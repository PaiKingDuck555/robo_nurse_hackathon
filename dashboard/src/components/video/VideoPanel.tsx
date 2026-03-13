"use client";

import VideoStream from "./VideoStream";
import CallControls from "./CallControls";
import { useWebRTC } from "@/hooks/useWebRTC";

interface VideoPanelProps {
  patientId?: string;
}

export default function VideoPanel({ patientId }: VideoPanelProps) {
  const roomId = patientId ? `patient-${patientId}` : null;
  const { remoteStream, status, isMuted, connect, disconnect, toggleMute } = useWebRTC(roomId);

  return (
    <div className="flex flex-col h-full gap-3">
      <div className="flex-1 min-h-0">
        <VideoStream stream={remoteStream} />
      </div>
      <CallControls
        status={status}
        isMuted={isMuted}
        onConnect={connect}
        onDisconnect={disconnect}
        onToggleMute={toggleMute}
      />
    </div>
  );
}
