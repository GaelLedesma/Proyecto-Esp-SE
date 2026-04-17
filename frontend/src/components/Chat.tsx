import { useEffect, useRef, useState } from "react";
import { socket } from "../lib/socket";
import Sidebar from "./Sidebar";
import Codigo from "./Codigo";

type ChatMessage = {
  text: string;
  ai_response: string;
  is_code: boolean;
  audio_url?: string;
  color?: string;
};

type ChatSession = {
  id: string;
  title: string;
  date: string;
  messages: ChatMessage[];
};

export default function Chat() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);

  const [currentId, setCurrentId] = useState<string | null>(null);
  const [typingMessage, setTypingMessage] = useState<ChatMessage | null>(null);
  const [displayedText, setDisplayedText] = useState("");
  const [chatColor, setChatColor] = useState("#10a37f");

  const bottomRef = useRef<HTMLDivElement | null>(null);

  const currentSession = sessions.find((s) => s.id === currentId);

  const limpiarTexto = (text: string) => {
    if (!text) return "";

    let t = text;

    // remove triple backticks and optional language labels
    t = t.replace(/```[a-zA-Z]*\n?/g, "");
    t = t.replace(/```/g, "");

    // remove inline backticks
    t = t.replace(/`/g, "");

    // convert escaped newlines to real newlines
    t = t.replace(/\\n/g, "\n");

    // trim whitespace
    t = t.trim();

    // remove wrapping quotes (single or double)
    t = t.replace(/^"+|"+$/g, "");
    t = t.replace(/^'+|'+$/g, "");

    return t;
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("chat_sessions");
      if (saved) {
        setSessions(JSON.parse(saved));
      }
    }
  }, []);

  // 🔥 SOCKET
  useEffect(() => {
    socket.on("respuesta", (data: ChatMessage) => {
      if ((data as any).color) {
        setChatColor((data as any).color);
      }
      let sessionId = currentId;

      // crear sesión si no existe
      if (!sessionId) {
        sessionId = Date.now().toString();

        const newSession: ChatSession = {
          id: sessionId,
          title: data.text.slice(0, 25),
          date: new Date().toLocaleDateString(),
          messages: [],
        };

        setSessions((prev) => [newSession, ...prev]);
        setCurrentId(sessionId);
      }

      // agregar mensaje usuario
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? {
                ...s,
                messages: [...s.messages, { ...data, ai_response: "" }],
              }
            : s,
        ),
      );

      setTypingMessage(data);
    });

    return () => {
      socket.off("respuesta");
    };
  }, [currentId]);

  // 🔥 TYPING
  useEffect(() => {
    if (!typingMessage || !currentId) return;

    let index = 0;
    setDisplayedText("");

    const interval = setInterval(() => {
      index++;
      setDisplayedText(typingMessage.ai_response.slice(0, index));

      if (index >= typingMessage.ai_response.length) {
        clearInterval(interval);

        setSessions((prev) =>
          prev.map((s) =>
            s.id === currentId
              ? {
                  ...s,
                  messages: s.messages.map((m, i) =>
                    i === s.messages.length - 1 ? typingMessage : m,
                  ),
                }
              : s,
          ),
        );

        setTypingMessage(null);
      }
    }, 20);

    return () => clearInterval(interval);
  }, [typingMessage, currentId]);

  // 🔥 SCROLL
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [sessions]);

  // 🔥 SAVE
  useEffect(() => {
    localStorage.setItem("chat_sessions", JSON.stringify(sessions));
  }, [sessions]);

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        fontFamily: "'Sora', sans-serif",
      }}
    >
      {/* SIDEBAR */}
      <Sidebar
        sessions={sessions}
        currentId={currentId}
        onSelect={setCurrentId}
        onNew={() => setCurrentId(null)}
      />

      {/* CHAT */}
      <div
        style={{
          flex: 1,
          background: "#343541",
          display: "flex",
          flexDirection: "column",
          color: "white",
        }}
      >
        <div style={{ padding: "16px", borderBottom: "1px solid #444" }}>
          Chat
        </div>

        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
          }}
        >
          {currentSession?.messages.map((msg, i) => (
            <div key={i}>
              {/* USER */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                }}
              >
                <div
                  style={{
                    background: chatColor,
                    padding: "12px 16px",
                    borderRadius: "16px",
                    maxWidth: "70%",
                    fontSize: "14px",
                    lineHeight: "1.5",
                  }}
                >
                  {msg.text}
                </div>
              </div>

              {/* AI */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-start",
                }}
              >
                <div
                  style={
                    msg.is_code
                      ? {
                          maxWidth: "70%",
                          padding: 0,
                          background: "transparent",
                          color: "initial",
                        }
                      : {
                          background: "#444654",
                          padding: "12px 16px",
                          borderRadius: "16px",
                          maxWidth: "70%",
                          position: "relative",
                          fontSize: "14px",
                          lineHeight: "1.5",
                        }
                  }
                >
                  {typingMessage && i === currentSession.messages.length - 1 ? (
                    msg.is_code ? (
                      // 🔥 SI ES CÓDIGO → NO typing
                      <Codigo code={limpiarTexto(typingMessage.ai_response)} />
                    ) : (
                      <span style={{ whiteSpace: "pre-wrap" }}>
                        {limpiarTexto(displayedText)}▌
                      </span>
                    )
                  ) : msg.is_code ? (
                    <Codigo code={limpiarTexto(msg.ai_response)} />
                  ) : (
                    <span
                      style={{
                        fontFamily: "'Sora', sans-serif",
                        whiteSpace: "pre-wrap",
                      }}
                    >
                      {limpiarTexto(msg.ai_response)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}

          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}
