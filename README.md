# 🔎 SkillLens AI — Step-by-Step Build Guide

SkillLens AI is a Streamlit chat app where a student enters their name and WhatsApp number once,
then chats with a visual learning buddy. They can type a question or attach a screenshot of code,
an error, a diagram, or study material. Gemini analyzes the text/image and explains the likely issue
in a beginner-friendly way. One button sends a learning recap to WhatsApp using Twilio.

It uses Gemini (chat + vision) and Twilio (WhatsApp) — no OpenCV, no MediaPipe, no model training.

## 🤔 What you'll need

- Python 3.9+ installed
- Basic comfort with Python
- A Google AI Studio account for a Gemini API key
- A Twilio account for WhatsApp Sandbox access

## 📁 Project structure

```text
skilllens_ai/
├── app.py                         # 🎨 Streamlit app + chat + image handling
├── prompts.py                     # 🧠 AI personality, welcome text and recap prompts
├── requirements.txt                # 📦 Dependencies
├── .gitignore                      # 🔐 Keeps secrets out of GitHub
├── README.md                       # 📘 This build guide
└── .streamlit/
    └── secrets.toml.example        # 🔑 Template; copy to secrets.toml
```

## 🧰 Step 1 — Create the environment

```bash
python -m venv venv
```

Activate it:

- Windows PowerShell: `.\venv\Scripts\Activate.ps1`
- Windows cmd: `venv\Scripts\activate.bat`
- macOS/Linux: `source venv/bin/activate`

Install packages:

```bash
pip install -r requirements.txt
```

## 🔑 Step 2 — Get your API keys

1. Open Google AI Studio and create a Gemini API key.
2. Sign up at Twilio and copy your Account SID and Auth Token.
3. In Twilio, open Messaging → Try it out → Send a WhatsApp message.
4. Follow the Sandbox instructions and send the join code from the WhatsApp number you'll test with.
5. In Twilio Content Template Builder, create a WhatsApp text template with two variables:
   - `{{1}}` for the student's name
   - `{{2}}` for the learning recap
6. Copy the template Content SID (usually starts with `HX`).

📌 WhatsApp requires an approved template for business-initiated messages outside the customer-service window. Follow the current Twilio Sandbox/account instructions.

## 🗝️ Step 3 — Configure secrets

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in your real values.

```toml
GEMINI_API_KEY = "your-key"
TWILIO_ACCOUNT_SID = "your-sid"
TWILIO_AUTH_TOKEN = "your-token"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
TWILIO_CONTENT_SID = "HX..."
```

Never commit `.streamlit/secrets.toml` to GitHub.

## 📦 Step 4 — Packages

`requirements.txt` contains only the core packages:

```text
streamlit
google-genai
twilio
```

- `streamlit` builds the chat interface and handles image uploads.
- `google-genai` connects to Gemini for text and image understanding.
- `twilio` sends the recap to WhatsApp.

## 🧠 Step 5 — prompts.py

The prompt file keeps SkillLens's behavior separate from the app logic.

- `SYSTEM_PROMPT` defines the assistant's role, style, and approach to screenshots.
- `WELCOME_MESSAGE_TEMPLATE` is the first message shown to each student.
- `SUMMARY_REQUEST_PROMPT` asks Gemini to create a compact WhatsApp learning recap.
- `CHALLENGE_REQUEST_PROMPT` asks Gemini to create a new practice challenge.

You can tune the personality here without restructuring the application.

## 💬 Step 6 — app.py

The app follows the same compact structure as MacroSnap:

1. 🔐 Read secrets from Streamlit.
2. ♻️ Cache Gemini and Twilio clients with `@st.cache_resource`.
3. 👋 Onboard the student once per Streamlit session.
4. 🧠 Create a Gemini chat with `SYSTEM_PROMPT`.
5. 💬 Save and replay text/image messages using `st.session_state`.
6. 📸 Send text and screenshot bytes to Gemini.
7. 📝 Ask Gemini for a recap or a practice challenge.
8. 📲 Send the recap using Twilio's WhatsApp Content API.

## ▶️ Step 7 — Run it locally

```bash
streamlit run app.py
```

Open the local URL Streamlit displays (normally `http://localhost:8501`), enter your name and
WhatsApp number, then try a question or attach a screenshot.

## 🚀 Step 8 — Deploy with Streamlit Community Cloud

1. Push the project to GitHub.
2. Confirm `.streamlit/secrets.toml` is not committed.
3. Create a new app in Streamlit Community Cloud and choose `app.py`.
4. Paste the same secret values into the app's Secrets settings.
5. Deploy and test with your opted-in WhatsApp Sandbox number.

## 🌟 Portfolio description

**SkillLens AI — Multimodal Learning & Debugging Assistant**

Built a Gemini-powered Streamlit application that analyzes screenshots and text questions, provides
context-aware explanations and debugging guidance, generates personalized practice challenges,
and sends learning recaps through WhatsApp using Twilio.

## 🛡️ Before production

- Add user authentication and per-user data isolation.
- Add upload-size limits and stronger file validation.
- Add rate limiting and useful error logging.
- Tell users what information is sent to Gemini and Twilio.
- Avoid storing screenshots or phone numbers unless necessary.
