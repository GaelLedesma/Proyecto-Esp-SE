import { useState } from "react";
import Prism from "prismjs";

import "prismjs/components/prism-python";
import "prismjs/components/prism-javascript";
import "prismjs/components/prism-typescript";

// IMPORTAR LENGUAJES (puedes agregar más)

type Props = {
  code: string;
};

export default function Codigo({ code }: Props) {
  const [copiado, setCopiado] = useState(false);
  const [expandido, setExpandido] = useState(false);
  const limpio = code
    .replace(/```[a-zA-Z]*\n?/g, "")
    .replace(/```/g, "")
    .replace(/`/g, "")
    .trim();

  // 🔥 DETECTAR LENGUAJE BÁSICO
  const detectarLenguaje = (code: string) => {
    if (code.includes("def ") || code.includes("print(")) return "python";
    if (code.includes("function") || code.includes("=>")) return "javascript";
    if (code.includes(": string") || code.includes("interface"))
      return "typescript";
    return "javascript";
  };

  const lenguaje = detectarLenguaje(limpio);

  const copiar = () => {
    navigator.clipboard.writeText(limpio);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 1500);
  };

  return (
    <div
      style={{
        borderRadius: "12px",
        border: "1px solid #333",
        overflow: "hidden",
        marginTop: "8px",
        background: "#1e1e1e",
      }}
    >
      {/* HEADER */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "6px 10px",
          background: "#2a2b32",
          borderBottom: "1px solid #333",
          fontSize: "12px",
          color: "#aaa",
        }}
      >
        <span>{lenguaje}</span>

        <div style={{ display: "flex", gap: "8px" }}>
          {/* EXPANDIR */}
          <button
            onClick={() => setExpandido(!expandido)}
            style={{
              background: "transparent",
              border: "1px solid #555",
              color: "#ddd",
              padding: "2px 8px",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "11px",
            }}
          >
            {expandido ? "−" : "+"}
          </button>

          {/* COPIAR ICONO */}
          <button
            onClick={copiar}
            style={{
              background: "transparent",
              border: "1px solid #555",
              color: "#ddd",
              padding: "2px 8px",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "11px",
            }}
          >
            {copiado ? "✔" : "📋"}
          </button>
        </div>
      </div>

      {/* CODE */}
      <pre
        className={`language-${lenguaje}`}
        style={{
          margin: 0,
          padding: "16px",
          overflowX: "auto",
          maxHeight: expandido ? "none" : "200px",
          fontSize: "13px",
          lineHeight: "1.6",
        }}
      >
        <code
          className={`language-${lenguaje}`}
          dangerouslySetInnerHTML={{
            __html: Prism.highlight(
              limpio,
              Prism.languages[lenguaje] || Prism.languages.javascript,
              lenguaje,
            ),
          }}
        />
      </pre>
    </div>
  );
}
