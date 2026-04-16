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

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading", logger=False, engineio_logger=False)
app.config['JSON_AS_ASCII'] = False

@socketio.on("connect")
def handle_connect():
    print("🔌 Cliente conectado via WebSocket")

@socketio.on("disconnect")
def handle_disconnect():
    print("❌ Cliente desconectado")

model = whisper.load_model("base")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:1.7b"

audio_chunks = []
modoIA_flag = True
modo_kb = False
ultima_respuesta = ""

BASE_DIR = Path(__file__).resolve().parent
RESPONSE_MP3 = BASE_DIR / "response.mp3"
RESPONSE_WAV = BASE_DIR / "response.wav"

# ================= KB =================

kb_base = {
    ("harry", "hermione"): "amigos",
    ("harry", "ron"): "mejores amigos",
    ("harry", "voldemort"): "archienemigos",
    ("harry", "dumbledore"): "mentor",
    ("harry", "snape"): "relación compleja",
    ("harry", "draco"): "rivales",
    ("harry", "sirius"): "ahijado y padrino",
    ("harry", "hagrid"): "protector",
    ("harry", "luna"): "amigos",
    ("harry", "ginny"): "pareja",
    ("harry", "neville"): "compañeros",
    ("hermione", "ron"): "pareja",
    ("hermione", "hagrid"): "amigos",
    ("hermione", "draco"): "enemigos",
    ("hermione", "ginny"): "amigas",
    ("ron", "ginny"): "hermanos",
    ("ron", "dumbledore"): "aliados",
    ("ron", "draco"): "enemigos",
    ("voldemort", "dumbledore"): "enemigos",
    ("voldemort", "bellatrix"): "aliados",
    ("voldemort", "snape"): "alianza tensa",
    ("snape", "lily"): "amor",
    ("snape", "dumbledore"): "aliados secretos",
    ("draco", "lucius"): "padre e hijo",
    ("draco", "narcissa"): "madre e hijo",
    ("sirius", "lupin"): "amigos",
    ("fred", "george"): "hermanos gemelos",
    ("james", "lily"): "pareja",
    ("james", "snape"): "enemigos",
    ("cedric", "harry"): "rivales amistosos",
}

kb = {}
for (a, b), rel in kb_base.items():
    kb[(a, b)] = rel
    kb[(b, a)] = rel

def normalizar_palabra(palabra, entidades):
    palabra = palabra.lower().strip()

    equivalentes = {
        # harry
        "hari": "harry",
        "jari": "harry",
        "ari": "harry",
        "harri": "harry",
        "jarry": "harry",
        "hary": "harry",
        "hary": "harry",

        # hermione
        "hermio": "hermione",
        "ermio": "hermione",
        "ermione": "hermione",
        "hermion": "hermione",
        "hermionee": "hermione",
        "mione": "hermione",

        # ron
        "rom": "ron",
        "roon": "ron",

        # voldemort
        "voldemor": "voldemort",
        "boldemort": "voldemort",
        "volde": "voldemort",

        # dumbledore
        "dumbladore": "dumbledore",
        "dumbeldore": "dumbledore",
        "dumbledor": "dumbledore",
        "dumbador": "dumbledore",

        # sirius
        "siriu": "sirius",
        "sirius": "sirius",

        # snape
        "esneip": "snape",
        "sneip": "snape",

        # hagrid
        "jagrid": "hagrid",
        "agrid": "hagrid",

        # draco
        "drako": "draco",

        # ginny
        "gini": "ginny",
        "gini": "ginny",

        # lupin
        "lupen": "lupin",

        # neville
        "nevil": "neville",

        # bellatrix
        "belatrix": "bellatrix",

        # lucius
        "lusius": "lucius",

        # narcissa
        "narsisa": "narcissa",

        # cedric
        "cedrik": "cedric",
    }

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

def responder_kb(user_text, respuesta):
    global ultima_respuesta
    ultima_respuesta = respuesta

    print("\n📡 Enviando respuesta KB:")
    print(f"🗣 Usuario: {user_text}")
    print(f"📚 KB: {respuesta}\n")

    socketio.emit("respuesta", {
        "text": user_text,
        "ai_response": respuesta,
        "is_code": False,
        "audio_url": ""
    })

    return {
        "text": user_text,
        "ai_response": respuesta,
        "is_code": False,
        "audio_url": ""
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

    return procesar()

@app.route("/procesar", methods=["GET"])
def procesar():
    global audio_chunks, ultima_respuesta

    if len(audio_chunks) == 0:
        return {"error": "No hay audio"}

    raw = b''.join(audio_chunks)
    audio_chunks = []

    audio = np.frombuffer(raw, dtype=np.int32).astype(np.float32)
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val

    sf.write("audio.wav", audio, 16000)

    result = model.transcribe("audio.wav")
    user_text = result["text"]
    user_text_lower = user_text.lower()

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
        match = buscar_relacion(user_text_lower)

        if match:
            p1, p2, rel = match
            return responder_kb(user_text, f"{p1} y {p2}: {rel}")
        else:
            return responder_kb(user_text, "No encontrado en la base de conocimiento")

    # ===== IA =====

    # 🔥 prompt completo restaurado
    system_prompt = (
        "Eres un asistente de voz inteligente integrado en un dispositivo.\n"
        "Responde SIEMPRE en español.\n"
        "\n"
        "Reglas:\n"
        "- Responde de forma breve, clara y natural (máximo 1-2 frases).\n"
        "- No inventes código.\n"
        "- Solo responde con código si el usuario dice explícitamente la palabra 'codigo'.\n"
        "- Si generas código, devuelve SOLO el código sin explicaciones.\n"
        "- Si NO es código, responde como una persona normal, sin mencionar que eres una IA.\n"
        "- Evita respuestas largas o técnicas innecesarias.\n"
        "\n"
        "Contexto:\n"
        "- El usuario habla por voz.\n"
        "- La respuesta puede convertirse en audio, así que debe sonar natural.\n"
    )

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

            audio_url = f"http://192.168.100.3:5001/audio_response?t={int(time.time())}"

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