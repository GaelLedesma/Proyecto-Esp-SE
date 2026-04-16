import React from "react";

type ChatSession = {
  id: string;
  title: string;
  date: string;
};

type Props = {
  sessions: ChatSession[];
  currentId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
};

export default function Sidebar({
  sessions,
  currentId,
  onSelect,
  onNew,
}: Props) {
  return (
    <div
      style={{
        width: "260px",
        background: "#202123",
        color: "white",
        display: "flex",
        flexDirection: "column",
        padding: "10px",
        borderRight: "1px solid #333",
      }}
    >
      {/* Nuevo chat */}
      <button
        onClick={onNew}
        style={{
          padding: "10px",
          background: "#10a37f",
          border: "none",
          borderRadius: "8px",
          color: "white",
          cursor: "pointer",
          marginBottom: "10px",
        }}
      >
        + Nuevo chat
      </button>

      {/* Lista */}
      <div style={{ overflowY: "auto", flex: 1 }}>
        {sessions.map((s) => (
          <div
            key={s.id}
            onClick={() => onSelect(s.id)}
            style={{
              padding: "10px",
              borderRadius: "8px",
              marginBottom: "6px",
              cursor: "pointer",
              background: currentId === s.id ? "#343541" : "transparent",
            }}
          >
            <div style={{ fontSize: "14px" }}>{s.title}</div>
            <div style={{ fontSize: "11px", color: "#aaa" }}>{s.date}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
