import json
import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client as TwilioClient

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
    CHALLENGE_REQUEST_PROMPT,
)

MODEL_NAME = "gemini-3.8-flash"

st.set_page_config(
    page_title="SkillLens AI",
    page_icon="🔎",
    layout="wide",
)

# ✨ A small custom theme to make the app feel like a real product.
st.markdown("""
<style>
    .stApp {
        background:
          radial-gradient(circle at 8% 0%, rgba(99,102,241,.16), transparent 30%),
          radial-gradient(circle at 92% 8%, rgba(14,165,233,.12), transparent 28%),
          #0b1020;
    }
    .hero {
        padding: 1.4rem 1.6rem;
        border: 1px solid rgba(255,255,255,.12);
        border-radius: 22px;
        background: linear-gradient(120deg, rgba(99,102,241,.23), rgba(14,165,233,.08));
        margin-bottom: 1rem;
    }
    .hero h1 { margin-bottom: .25rem; }
    .hero p { color: #c3cbe0; margin-bottom: .25rem; }
    .tag {
        display: inline-block;
        padding: .25rem .65rem;
        margin-right: .35rem;
        border-radius: 999px;
        background: rgba(129,140,248,.17);
        color: #dbeafe;
        font-size: .78rem;
    }
    div[data-testid="stChatMessage"] {
        border: 1px solid rgba(255,255,255,.07);
        border-radius: 16px;
        padding: .6rem;
    }
</style>
""", unsafe_allow_html=True)

# 🔐 Read credentials from Streamlit secrets.
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = st.secrets["TWILIO_WHATSAPP_FROM"]
TWILIO_CONTENT_SID = st.secrets["TWILIO_CONTENT_SID"]


@st.cache_resource
def get_gemini_client():
    """Create the Gemini client once and reuse it across Streamlit reruns."""
    return genai.Client(api_key=GEMINI_API_KEY)


@st.cache_resource
def get_twilio_client():
    """Create the Twilio client once and reuse it across Streamlit reruns."""
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


gemini_client = get_gemini_client()
twilio_client = get_twilio_client()


def render_message(message):
    """Render text and uploaded images from the saved conversation."""
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.markdown(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"], caption="🖼️ Uploaded screenshot")


def add_message(role, kind, content):
    """Save a message and immediately render it."""
    st.session_state.messages.append(
        {"role": role, "kind": kind, "content": content}
    )
    render_message(st.session_state.messages[-1])


def ask_gemini(parts):
    """Send text and/or image parts to the current Gemini chat."""
    try:
        response = st.session_state.chat.send_message(parts)
        return response.text or "I couldn't create a text response. Try asking another way."
    except Exception as error:
        return f"⚠️ Sorry, something went wrong: {error}"


def clean_whatsapp_text(text):
    """Keep the summary compact and safe to place in a WhatsApp template."""
    if not text:
        return "No learning recap is available yet."
    text = " ".join(text.split())
    return text[:1400] + "..." if len(text) > 1400 else text


def send_whatsapp(to_number, user_name, summary):
    """Send a template-based WhatsApp message using Twilio Content API."""
    try:
        content_variables = json.dumps(
            {
                "1": user_name,
                "2": clean_whatsapp_text(summary),
            },
            ensure_ascii=False,
        )
        message = twilio_client.messages.create(
            from_=(
                TWILIO_WHATSAPP_FROM
                if TWILIO_WHATSAPP_FROM.startswith("whatsapp:")
                else f"whatsapp:{TWILIO_WHATSAPP_FROM}"
            ),
            to=(
                to_number
                if to_number.startswith("whatsapp:")
                else f"whatsapp:{to_number}"
            ),
            content_sid=TWILIO_CONTENT_SID,
            content_variables=content_variables,
        )
        return True, message.sid
    except Exception as error:
        return False, str(error)


def make_learning_recap():
    """Ask Gemini to summarize the conversation for WhatsApp."""
    return ask_gemini([SUMMARY_REQUEST_PROMPT])


def create_next_challenge():
    """Ask Gemini for a short practice question based on the current chat."""
    return ask_gemini([CHALLENGE_REQUEST_PROMPT])


# 🧑‍🎓 Step 1: first-time onboarding.
if "onboarded" not in st.session_state:
    st.markdown("""
    <div class="hero">
      <span class="tag">✨ MULTIMODAL AI</span>
      <span class="tag">🧠 PERSONAL LEARNING</span>
      <span class="tag">📲 WHATSAPP RECAPS</span>
      <h1>🔎 SkillLens AI</h1>
      <p>Show it what you're stuck on. Understand the reason. Make your next move.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("👋 Let's set up your learning space")
    with st.form("onboarding_form"):
        name = st.text_input("✨ What should we call you?", placeholder="Your name")
        whatsapp_number = st.text_input(
            "📱 WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
            help="Use the same number that has joined your Twilio WhatsApp Sandbox.",
        )
        level = st.selectbox(
            "🎓 Your current level",
            ["Beginner", "Intermediate", "Advanced"],
        )
        submitted = st.form_submit_button("Let's get started 🚀", use_container_width=True)

    if submitted:
        if not name.strip() or not whatsapp_number.strip():
            st.warning("⚠️ Please enter both your name and WhatsApp number.")
        elif not whatsapp_number.strip().startswith("+"):
            st.warning("📱 Add the country code, for example +91XXXXXXXXXX.")
        else:
            st.session_state.name = name.strip()
            st.session_state.whatsapp_number = whatsapp_number.strip()
            st.session_state.level = level
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT.format(
                        name=st.session_state.name,
                        level=st.session_state.level,
                    )
                ),
            )
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()
    st.stop()


# 🎨 Step 2: main app header and action button.
header_col, button_col = st.columns([5, 2], vertical_alignment="center")
with header_col:
    st.markdown("""
    <div class="hero">
      <span class="tag">🔎 SCREENSHOT UNDERSTANDING</span>
      <span class="tag">🧠 EXPLAIN • DEBUG • REVIEW</span>
      <h1>SkillLens AI</h1>
      <p>Your visual learning buddy — from confusion to clarity.</p>
    </div>
    """, unsafe_allow_html=True)

with button_col:
    send_disabled = len(st.session_state.messages) < 2
    if st.button(
        "📤 Send recap to WhatsApp",
        disabled=send_disabled,
        use_container_width=True,
    ):
        with st.spinner("🧠 Preparing your learning recap..."):
            summary = make_learning_recap()
        success, info = send_whatsapp(
            st.session_state.whatsapp_number,
            st.session_state.name,
            summary,
        )
        if success:
            st.success("Sent! Check your WhatsApp 📲")
        else:
            st.error(f"Couldn't send the recap: {info}")

st.caption(
    f"👋 Hi {st.session_state.name}! · 🎓 {st.session_state.level} level · "
    f"📱 Recaps go to {st.session_state.whatsapp_number}"
)

# 🧭 Step 3: quick-start cards.
if not st.session_state.messages:
    st.markdown("### ✨ What do you want help with today?")
    q1, q2, q3, q4 = st.columns(4)
    quick_starters = [
        ("🐞 Debug", "Help me understand and fix this error."),
        ("🧠 Explain", "Explain this concept in simple beginner-friendly steps."),
        ("🔍 Review", "Review this code or project and suggest the most useful improvement."),
        ("🎯 Practice", "Create a small practice challenge based on what I am learning."),
    ]
    for col, (label, prompt) in zip([q1, q2, q3, q4], quick_starters):
        with col:
            if st.button(label, use_container_width=True):
                add_message("user", "text", prompt)
                with st.spinner("🔎 SkillLens is thinking..."):
                    answer = ask_gemini([prompt])
                add_message("assistant", "text", answer)
                st.rerun()

# 💬 Step 4: replay conversation history after every Streamlit rerun.
if not st.session_state.messages:
    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name),
    )
else:
    for message in st.session_state.messages:
        render_message(message)

# 📎 Step 5: one chat box for text and screenshots.
user_input = st.chat_input(
    "Ask a question or attach a screenshot… 💬",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type or "image/jpeg",
            )
        )

    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append(
            "Please inspect this image. Identify what it shows, explain the likely issue "
            "or concept in beginner-friendly language, and suggest a useful next step."
        )

    with st.spinner("🔎 Reading the screenshot and thinking it through..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)


# ⚡ Step 6: extra smart actions.
# ⚡ Step 6: extra smart actions.
if st.session_state.messages:
    st.markdown("---")
    st.markdown("### ⚡ Keep the learning going")
    recap_col, challenge_col = st.columns(2)

    with recap_col:
        if st.button("📝 Create learning recap", use_container_width=True):
            with st.spinner("🧠 Turning this chat into useful notes..."):
                st.session_state.recap_result = make_learning_recap()

    with challenge_col:
        if st.button("🎯 Give me a practice challenge", use_container_width=True):
            with st.spinner("🧩 Creating a challenge for your level..."):
                st.session_state.challenge_result = create_next_challenge()

    # Display persisted outputs from session state
    if "recap_result" in st.session_state:
        st.markdown("#### 📌 Your recap")
        st.info(st.session_state.recap_result)

    if "challenge_result" in st.session_state:
        st.markdown("#### 🧩 Your next challenge")
        st.info(st.session_state.challenge_result)

st.caption("🔎 SkillLens AI · Built with Streamlit + Gemini + Twilio")
