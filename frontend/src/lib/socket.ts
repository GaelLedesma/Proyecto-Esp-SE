import { io } from "socket.io-client";

export const socket = io("http://172.20.10.7:5001", {
  transports: ["websocket"],
});
