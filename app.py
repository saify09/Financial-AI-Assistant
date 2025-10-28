from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import markdown2, os, traceback  # 👈 added markdown2

# ✅ Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# ✅ Initialize OpenAI client safely
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Missing OPENAI_API_KEY in .env file")

client = OpenAI(api_key=api_key)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate_narrative():
    try:
        data = request.get_json(force=True)
        scenario = data.get("scenario", "").strip()
        history = data.get("history", [])
        title = data.get("title", "").strip()

        if not scenario:
            return jsonify({"error": "Missing 'scenario' text"}), 400

        # 🕒 Real-time date and time (Pakistan timezone)
        current_datetime = datetime.now().strftime("%A, %B %d, %Y – %I:%M %p")
        timezone = "GMT+5"

        # 🧠 Adaptive System Prompt (Encourage elegant formatting)
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are **Financial AI Assistant**, created by **Saifuddin Hanif**. "
                    f"You provide advanced financial and business insights with clarity, reasoning, and elegance.\n\n"
                    f"### 🧩 Writing Rules\n"
                    f"- Use **bold**, *italic*, and clear section titles like **Overview**, **Financial Impact**, **Risks**, **Opportunities**, and **Recommendations**.\n"
                    f"- Do NOT use Markdown syntax like ### or ``` — instead, use bold or italic formatting for headings.\n"
                    f"- Structure content professionally with readable spacing and smooth flow.\n"
                    f"- Avoid robotic or templated tone — write naturally but precisely.\n"
                    f"- Adapt automatically: use structured sections for reports, and smooth paragraphs for general answers.\n"
                    f"- Never give overly short or summarized responses unless asked.\n\n"
                    f"### 👤 Creator Background\n"
                    f"Saifuddin Hanif (born 11 January 2006) is a young, hardworking developer with expertise in **Python, Django, PyTorch, Docker, Streamlit, HTML, CSS, and Data Science**. "
                    f"He builds projects that merge AI and real-world applications, including a Weapon Detection Web App and this Financial Narrative Generator.\n\n"
                    f"### 🧠 Behavior Rules\n"
                    f"- Be analytical, empathetic, and factually consistent.\n"
                    f"- Always write with a professional, human-like voice.\n\n"
                    f"### 🕒 Context\n"
                    f"Today's actual date and time is: **{current_datetime} ({timezone})**.\n"
                    f"Reference time or trends accurately when relevant."
                ),
            }
        ]

        # 🧾 Include chat history
        for msg in history:
            if msg.get("user"):
                messages.append({"role": "user", "content": msg["user"]})
            if msg.get("assistant"):
                messages.append({"role": "assistant", "content": msg["assistant"]})

        messages.append({"role": "user", "content": scenario})

        # 🧮 Token management
        prompt_length = sum(len(m["content"]) for m in messages)
        max_output_tokens = max(1200, min(4000, 6000 - int(prompt_length / 2)))

        print("➡️ Sending request to OpenAI...")

        # 🧾 Generate rich response
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.85,
            top_p=0.95,
            max_tokens=max_output_tokens,
        )

        print("✅ OpenAI response received.")
        reply = response.choices[0].message.content.strip()

        # ✨ Convert Markdown / Text to clean HTML for frontend display
        reply_html = markdown2.markdown(
            reply, extras=["fenced-code-blocks", "tables", "break-on-newline"]
        )

        # 🏷️ Generate title if missing
        if not title:
            title_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You create short, professional titles summarizing financial scenarios. "
                            "Return only the title text."
                        ),
                    },
                    {"role": "user", "content": scenario},
                ],
                temperature=0.6,
                max_tokens=20,
            )
            title = title_response.choices[0].message.content.strip()

        return jsonify({"title": title, "reply": reply_html})

    except Exception as e:
        print("❌ ERROR in /api/generate:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🚀 Financial Narrative Generator running at http://127.0.0.1:5000")
    app.run(debug=True)
