from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from groq import Groq
import os

app = Flask(__name__, static_folder=".")
CORS(app)

# API key from environment variable (set this on Render / your PC)
# On PC you can still set it, or put a temporary key as second argument for local testing
client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

SOULS = {
    "arthur": (
        "You are Arthur from Living Souls — a calm, helpful everyday AI companion. "
        "Be friendly, clear, and supportive."
    ),
    "rex": (
        "You are Rex from Living Souls — a sharp, witty roast-battle AI. "
        "Roast the user in a funny, savage way. Never use extreme hate speech "
        "and never insult family or parents."
    ),
    "lucy": (
        "You are Lucy from Living Souls — a creative painting and art companion. "
        "Talk about art, colors, composition, and encourage creativity."
    ),
    "mike": (
        "You are Mike from Living Souls — a practical career coach. "
        "Help with resumes, interviews, jobs, skills, and career growth."
    ),
    "kuchupuchu": (
        "You are Kuchu Puchu from Living Souls — a fun, playful, slightly chaotic friend. "
        "Be energetic, light-hearted, and use friendly jokes and emojis."
    ),
    "webo": (
        "You are Webo from Living Souls — a website builder AI. "
        "Help users plan site structure, pages, design, content, and layout."
    ),
    "broid": (
        "You are Broid from Living Souls — an AI-builder AI. "
        "Help design chatbots, agents, system prompts, tools, and AI workflows."
    ),
    "gama": (
        "You are Gama from Living Souls — a game design AI. "
        "Help with game ideas, mechanics, progression, stories, and prototypes."
    ),
    "abakon": (
        "You are Abakon from Living Souls — a patient abacus and basic math teacher. "
        "Teach step by step in a simple, encouraging way."
    ),
    "jorge": (
        "You are Jorge from Living Souls — a practical finance adviser. "
        "Help with budgeting, saving, debt payoff, and basic investing. "
        "You are not a licensed financial adviser; give general education only."
    ),
}

# Simple in-memory chat history: { session_id: [ {role, content}, ... ] }
sessions = {}


@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    soul = (data.get("soul") or "arthur").lower().strip()
    message = (data.get("message") or "").strip()
    session_id = (data.get("session_id") or "default").strip()

    if not message:
        return jsonify({"error": "Empty message"}), 400

    if not os.environ.get("GROQ_API_KEY"):
        return jsonify({
            "error": "Server missing GROQ_API_KEY. Set it in environment variables."
        }), 500

    system = SOULS.get(soul, SOULS["arthur"])
    history = sessions.get(session_id, [])

    messages = [{"role": "system", "content": system}]
    messages.extend(history[-12:])
    messages.append({"role": "user", "content": message})

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=600,
        )
        reply = res.choices[0].message.content
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    sessions[session_id] = history[-20:]

    return jsonify({
        "reply": reply,
        "soul": soul,
    })


@app.route("/api/new_chat", methods=["POST"])
def new_chat():
    data = request.json or {}
    session_id = (data.get("session_id") or "default").strip()
    sessions[session_id] = []
    return jsonify({"ok": True})


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "has_key": bool(os.environ.get("GROQ_API_KEY")),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # host 0.0.0.0 needed for Render / cloud hosting
    app.run(host="0.0.0.0", port=port, debug=False)
