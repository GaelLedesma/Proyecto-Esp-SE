from flask import Flask, request, send_file, make_response
import numpy as np
import soundfile as sf
import whisper
import requests
from gtts import gTTS
from flask_socketio import SocketIO
from difflib import get_close_matches
import subprocess
import os
import time
from pathlib import Path
from collections import deque

from constants import *
from kb_data import kb_base, equivalentes, system_prompt

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading", logger=False, engineio_logger=False)
app.config['JSON_AS_ASCII'] = False

@socketio.on("connect")
def handle_connect():
    print("🔌 Cliente conectado via WebSocket")

@socketio.on("disconnect")
def handle_disconnect():
    print("❌ Cliente desconectado")

audio_chunks = []
modoIA_flag = True
modo_kb = False
ultima_respuesta = ""
contexto_historial = []
modo_contexto = False


# ================= KB =================
colores_css = {
    "azul": "#3498db",
    "rojo": "#e74c3c",
    "amarillo": "#f1c40f",
    "morado": "#9b59b6"
}
kb = {}
for (a, b), rel in kb_base.items():
    kb[(a, b)] = rel
    kb[(b, a)] = rel

def normalizar_palabra(palabra, entidades):
    palabra = palabra.lower().strip()

    if palabra in equivalentes:
        return equivalentes[palabra]

    if palabra in entidades:
        return palabra

    matches = get_close_matches(palabra, list(entidades), n=1, cutoff=0.45)
    return matches[0] if matches else None

def buscar_relacion(texto):
    texto = texto.lower()
    tokens = texto.split()

    entidades = set([e for par in kb.keys() for e in par])

    normalizados = []
    for t in tokens:
        n = normalizar_palabra(t, entidades)
        if n:
            normalizados.append(n)

    # quitar duplicados preservando orden
    vistos = set()
    normalizados_unicos = []
    for n in normalizados:
        if n not in vistos:
            vistos.add(n)
            normalizados_unicos.append(n)

    for i in range(len(normalizados_unicos)):
        for j in range(i + 1, len(normalizados_unicos)):
            p1, p2 = normalizados_unicos[i], normalizados_unicos[j]
            rel = kb.get((p1, p2))
            if rel:
                return p1, p2, rel

    return None
def buscar_relacion_profunda(p1, p2, max_depth=3):

    queue = deque([(p1, [], 0)])

    visited = set()

    while queue:

        current, path, depth = queue.popleft()

        if depth > max_depth:

            continue

        if current == p2:

            return path

        visited.add(current)

        for (a, b), rel in kb.items():

            if a == current and b not in visited:

                queue.append((b, path + [(a, b, rel)], depth + 1))

    return None

# Nueva función: responder_pregunta_kb
def responder_pregunta_kb(texto):
    texto = texto.lower()
    entidades = set([e for par in kb.keys() for e in par])

    stopwords = {"ay", "hay", "entre", "y", "es", "son", "de", "a", "el", "la", "los", "las", "un", "una"}

    normalizados = []
    for t in texto.replace("¿", "").replace("?", "").split():
        if t in stopwords:
            continue

        n = normalizar_palabra(t, entidades)
        if n and n not in normalizados:
            normalizados.append(n)

    if len(normalizados) < 2:
        return None

    p1, p2 = normalizados[0], normalizados[1]
    rel = kb.get((p1, p2))

    if "pareja" in texto:
        if rel == "pareja":
            return f"Sí, {p1} y {p2} son pareja"
        return f"No, {p1} y {p2} no son pareja"

    if "amor" in texto or "ama" in texto:
        if rel == "amor":
            return f"Sí, {p1} siente amor por {p2}"
        return f"No, no se registra amor entre {p1} y {p2}"

    if "enemigo" in texto or "enemigos" in texto:
        if rel == "enemigos" or rel == "archienemigos":
            return f"Sí, {p1} y {p2} son enemigos"
        return f"No, {p1} y {p2} no son enemigos"

    return None

def responder_kb(user_text, respuesta):
    global ultima_respuesta
    ultima_respuesta = respuesta

    print("\n📡 Enviando respuesta KB:")
    print(f"🗣 Usuario: {user_text}")
    print(f"📚 KB: {respuesta}\n")

    audio_url = ""

    try:
        tmp_mp3 = BASE_DIR / f"response_tmp_{int(time.time()*1000)}.mp3"
        tmp_wav = BASE_DIR / f"response_tmp_{int(time.time()*1000)}.wav"

        tts = gTTS(respuesta, lang='es')
        tts.save(str(tmp_mp3))

        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", str(tmp_mp3),
            "-ar", "16000",
            "-ac", "1",
            "-sample_fmt", "s16",
            str(tmp_wav)
        ], capture_output=True, text=True)

        if result.returncode == 0 and tmp_wav.exists():
            os.replace(str(tmp_mp3), str(RESPONSE_MP3))
            os.replace(str(tmp_wav), str(RESPONSE_WAV))

            audio_url = f"http://192.168.100.3/audio_response?t={int(time.time())}"
        else:
            audio_url = ""

    except Exception as e:
        print("❌ Error audio KB:", e)
        audio_url = ""

    socketio.emit("respuesta", {
        "text": user_text,
        "ai_response": respuesta,
        "is_code": False,
        "audio_url": audio_url
    })

    return {
        "text": user_text,
        "ai_response": respuesta,
        "is_code": False,
        "audio_url": audio_url
    }

# ================= AUDIO =================

@app.route("/audio", methods=["POST"])
def receive_audio():
    global audio_chunks
    data = request.data
    if len(data) > 0:
        audio_chunks.append(data)
    return {"status": "ok"}

@app.route("/finalizar", methods=["POST"])
def finalizar():
    global modoIA_flag
    data = request.get_json(silent=True)

    if data and "modoIA" in data:
        modoIA_flag = bool(data["modoIA"])
    # 🔥 BORRAR audios ANTES de procesar nueva pregunta
    try:
        if RESPONSE_MP3.exists():
            RESPONSE_MP3.unlink()
        if RESPONSE_WAV.exists():
            RESPONSE_WAV.unlink()
        print("🧹 Audios previos eliminados antes de procesar")
    except Exception as e:
        print("⚠️ Error limpiando audios previos:", e)
    return procesar()

@app.route("/finalizar_contexto", methods=["POST"])
def finalizar_contexto():
    global modo_contexto
    modo_contexto = True
    return finalizar()

@app.route("/procesar", methods=["GET"])
def procesar():
    global audio_chunks, ultima_respuesta, modo_contexto

    if len(audio_chunks) == 0:
        return {"error": "No hay audio"}

    raw = b''.join(audio_chunks)
    audio_chunks = []

    audio = np.frombuffer(raw, dtype=np.int32).astype(np.float32)
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val

    sf.write("audio.wav", audio, 16000)

    result = model.transcribe("audio.wav", language="es")
    user_text = result["text"]
    user_text_lower = user_text.lower()

    # ===== COLORES =====
    for color, hex_val in colores_css.items():
        if color in user_text_lower:
            respuesta_color = f"{color}: {hex_val}"

            print("\n🎨 Color detectado:")
            print(respuesta_color)

            socketio.emit("respuesta", {
                "text": user_text,
                "ai_response": respuesta_color,
                "is_code": False,
                "color": hex_val,
                "audio_url": ""
            })

            return {
                "text": user_text,
                "ai_response": respuesta_color,
                "is_code": False,
                "color": hex_val,
                "audio_url": ""
            }

    # ===== KB =====
    global modo_kb

    if not modo_kb:
        if "modo conocimiento" in user_text_lower:
            modo_kb = True
            return responder_kb(user_text, "Modo base de conocimiento activado. Di dos personajes.")

    if "salir" in user_text_lower:
        modo_kb = False
        return responder_kb(user_text, "Saliendo del modo conocimiento")

    if modo_kb:
        respuesta_pregunta = responder_pregunta_kb(user_text_lower)
        if respuesta_pregunta:
            return responder_kb(user_text, respuesta_pregunta)
        match = buscar_relacion(user_text_lower)

        if match:
            p1, p2, rel = match
            return responder_kb(user_text, f"{p1} y {p2}: {rel}")
        else:
            entidades = set([e for par in kb.keys() for e in par])
            normalizados = []

            for t in user_text_lower.split():
                n = normalizar_palabra(t, entidades)
                if n:
                    normalizados.append(n)

            if len(normalizados) >= 2:
                p1, p2 = normalizados[0], normalizados[1]

                camino = buscar_relacion_profunda(p1, p2)

                if camino:
                    texto = f"{p1} está relacionado con {p2} a través de "
                    texto += " → ".join([f"{a}-{b}" for (a,b,_) in camino])
                    return responder_kb(user_text, texto)

            return responder_kb(user_text, "No encontrado en la base de conocimiento")

    # ===== IA =====

    if modo_contexto and len(contexto_historial) > 0:
        contexto_texto = "\n".join(contexto_historial[-6:])
        full_prompt = f"{system_prompt}\n{contexto_texto}\nUsuario: {user_text}\nAsistente:"
    else:
        full_prompt = f"{system_prompt}\nUsuario: {user_text}\nAsistente:"

    ai_response = ""

    if modoIA_flag:
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": full_prompt,
                    "stream": False
                }
            )

            data = response.json()
            ai_response = data.get("response", "")

            print("\n🧠 Respuesta IA:")
            print(ai_response)

        except Exception as e:
            print("❌ Error con Ollama:", e)
            ai_response = ""

    ultima_respuesta = ai_response

    if modo_contexto and ai_response:
        ai_response = ai_response.strip() + " contexto"

    if modo_contexto:
        contexto_historial.append(f"Usuario: {user_text}")
        contexto_historial.append(f"Asistente: {ai_response}")

    # ===== AUDIO FIX SIMPLE =====
    audio_url = ""

    if ai_response:
        try:
            # 🔥 generar archivos temporales (evita conflictos con ESP leyendo)
            tmp_mp3 = BASE_DIR / f"response_tmp_{int(time.time()*1000)}.mp3"
            tmp_wav = BASE_DIR / f"response_tmp_{int(time.time()*1000)}.wav"

            print("🧪 Generando audio temporal...")

            # generar MP3
            tts = gTTS(ai_response, lang='es')
            tts.save(str(tmp_mp3))

            if not tmp_mp3.exists():
                raise Exception("No se generó MP3 temporal")

            print(f"🎧 MP3 temporal listo ({tmp_mp3.stat().st_size} bytes)")

            # convertir a WAV
            result = subprocess.run([
                "ffmpeg", "-y",
                "-i", str(tmp_mp3),
                "-ar", "16000",
                "-ac", "1",
                "-sample_fmt", "s16",
                str(tmp_wav)
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print("FFMPEG STDERR:")
                print(result.stderr)
                raise Exception("FFMPEG falló")

            # esperar WAV válido
            timeout = 8
            start = time.time()
            while True:
                if tmp_wav.exists():
                    size = tmp_wav.stat().st_size
                    if size > 1000:
                        print(f"✅ WAV temporal listo ({size} bytes)")
                        break
                if time.time() - start > timeout:
                    raise Exception("Timeout esperando WAV temporal")
                time.sleep(0.1)

            # 🔥 REEMPLAZO ATÓMICO (clave)
            os.replace(str(tmp_mp3), str(RESPONSE_MP3))
            os.replace(str(tmp_wav), str(RESPONSE_WAV))

            print("📢 Audio final actualizado (atomic replace)")

            audio_url = f"http://192.168.100.3/audio_response?t={int(time.time())}"

        except Exception as e:
            print("❌ Error audio:", e)
            audio_url = ""

            # limpiar temporales si fallan
            try:
                if 'tmp_mp3' in locals() and tmp_mp3.exists():
                    tmp_mp3.unlink()
                if 'tmp_wav' in locals() and tmp_wav.exists():
                    tmp_wav.unlink()
            except Exception:
                pass

    print("\n📡 Enviando respuesta IA:")
    print(f"🗣 Usuario: {user_text}")
    print(f"🤖 IA: {ai_response}")
    print(f"🔊 Audio URL: {audio_url}\n")

    socketio.emit("respuesta", {
        "text": user_text,
        "ai_response": ai_response,
        "audio_url": audio_url
    })

    modo_contexto = False

    return {
        "text": user_text,
        "ai_response": ai_response,
        "audio_url": audio_url
    }

# ================= GET AUDIO =================

@app.route("/audio_response", methods=["GET"])
def audio_response():
    # si el WAV ya existe, lo mandamos
    if RESPONSE_WAV.exists():
        response = make_response(send_file(str(RESPONSE_WAV), mimetype="audio/wav"))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # si no existe el WAV pero sí el MP3, lo generamos aquí y esperamos
    if RESPONSE_MP3.exists():
        print("⚠️ response.wav no existe, intentando generarlo desde response.mp3")

        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", str(RESPONSE_MP3),
            "-ar", "16000",
            "-ac", "1",
            "-sample_fmt", "s16",
            str(RESPONSE_WAV)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print("FFMPEG STDERR:")
            print(result.stderr)
            return {"error": "audio no listo"}, 404

        timeout = 5
        start = time.time()
        while True:
            if RESPONSE_WAV.exists() and RESPONSE_WAV.stat().st_size > 1000:
                response = make_response(send_file(str(RESPONSE_WAV), mimetype="audio/wav"))
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            if time.time() - start > timeout:
                break
            time.sleep(0.1)

    print("❌ response.wav no existe y no pudo generarse")
    return {"error": "audio no listo"}, 404

@app.route("/ultima_respuesta", methods=["GET"])
def obtener_respuesta():
    return {"respuesta": ultima_respuesta}

if __name__ == "__main__":
    print("🚀 Server listo")
    socketio.run(app, host="0.0.0.0", port=5001)