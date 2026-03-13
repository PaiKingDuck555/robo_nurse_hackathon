import { createServer } from "http";
import { Server } from "socket.io";

const httpServer = createServer();
const io = new Server(httpServer, {
  cors: {
    origin: ["http://localhost:3000", "http://localhost:3001"],
    methods: ["GET", "POST"],
  },
});

// Track rooms: roomId -> { doctor?: socketId, robot?: socketId }
const rooms: Record<string, { doctor?: string; robot?: string }> = {};

io.on("connection", (socket) => {
  console.log(`[Signaling] Client connected: ${socket.id}`);

  socket.on("join-room", ({ roomId, role }: { roomId: string; role: "doctor" | "robot" }) => {
    socket.join(roomId);

    if (!rooms[roomId]) rooms[roomId] = {};
    rooms[roomId][role] = socket.id;

    const peersInRoom = Object.values(rooms[roomId]).filter(Boolean).length;

    socket.emit("room-joined", { role, peersInRoom });
    socket.to(roomId).emit("peer-joined", { role });

    console.log(`[Signaling] ${role} joined room ${roomId} (${peersInRoom} peers)`);
  });

  socket.on("offer", ({ roomId, signal }: { roomId: string; signal: any }) => {
    socket.to(roomId).emit("offer", { signal });
  });

  socket.on("answer", ({ roomId, signal }: { roomId: string; signal: any }) => {
    socket.to(roomId).emit("answer", { signal });
  });

  socket.on("ice-candidate", ({ roomId, candidate }: { roomId: string; candidate: any }) => {
    socket.to(roomId).emit("ice-candidate", { candidate });
  });

  socket.on("leave-room", ({ roomId }: { roomId: string }) => {
    socket.leave(roomId);
    socket.to(roomId).emit("peer-left");

    // Clean up room tracking
    if (rooms[roomId]) {
      for (const role of ["doctor", "robot"] as const) {
        if (rooms[roomId][role] === socket.id) {
          delete rooms[roomId][role];
        }
      }
      if (!rooms[roomId].doctor && !rooms[roomId].robot) {
        delete rooms[roomId];
      }
    }

    console.log(`[Signaling] Client left room ${roomId}`);
  });

  socket.on("disconnect", () => {
    // Clean up all rooms this socket was in
    for (const [roomId, room] of Object.entries(rooms)) {
      for (const role of ["doctor", "robot"] as const) {
        if (room[role] === socket.id) {
          delete room[role];
          socket.to(roomId).emit("peer-left");
        }
      }
      if (!room.doctor && !room.robot) {
        delete rooms[roomId];
      }
    }

    console.log(`[Signaling] Client disconnected: ${socket.id}`);
  });
});

const PORT = 3001;
httpServer.listen(PORT, () => {
  console.log(`[Signaling] Server running on http://localhost:${PORT}`);
});
