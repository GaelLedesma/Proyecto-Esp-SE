import { io } from "socket.io-client";

export const socket = io("http://192.168.100.18:5001", {
  transports: ["websocket"],
});
