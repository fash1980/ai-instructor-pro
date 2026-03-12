import re
import html
import time
import requests
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timezone
import streamlit.components.v1 as components
from types import SimpleNamespace
import os, base64, hashlib, secrets, time
import streamlit as st
import streamlit.components.v1 as components
import extra_streamlit_components as stx
from streamlit_float import float_init
from urllib.parse import quote
import json
DEBUG_AUTH = True
def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def make_pkce_pair():
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


# ---------------- Optional: Live refresh helper ----------------
# If missing: pip install streamlit-autorefresh
try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except Exception:
    HAS_AUTOREFRESH = False


# ---------------- Page Config ----------------
st.set_page_config(page_title="AI Instructor Pro | English Tutor", layout="wide", page_icon="✍️")
float_init()

# ---------------- Supabase Setup ----------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_ROLE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
supabase_admin = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_service = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def user_client(access_token: str):
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(access_token)
    return client


# ---------------- UI Styling ----------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded');


/* Main Background and Font */
.stApp {
    background: #fdfdff;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
@import url("https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0");

.ms {
  font-family: "Material Symbols Rounded";
  font-weight: normal;
  font-style: normal;
  font-size: 20px;
  line-height: 1;
  display: inline-block;
  vertical-align: middle;
}
/* The Hero Header - More Modern Gradient */
.hero-container {
    background:
        radial-gradient(circle, rgba(255,255,255,0.15) 1px, transparent 1px),
        linear-gradient(135deg,#6366f1,#9333ea);
    background-size: 20px 20px, cover;
    border-radius: 24px;
    padding: 40px;
    text-align: center;
    color: white;
}
/* Wrapper for login area */
.auth-wrapper {
    max-width: 520px;
    margin: 28px auto 0 auto;
}

/* Make Streamlit link button prettier */
.stLinkButton a {
    display: flex !important;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: 14px 18px !important;
    border-radius: 16px !important;
    background: white !important;
    color: #0f172a !important;
    border: 1px solid #e2e8f0 !important;
    text-decoration: none !important;
    font-weight: 600 !important;
    font-size: 17px !important;
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.06);
    transition: all 0.2s ease;
    margin-top: 18px !important;
}

.stLinkButton a:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 30px rgba(99, 102, 241, 0.16);
    border-color: #c7d2fe !important;
    background: #f8faff !important;
}
/* Centering the Login Box */
.auth-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    max-width: 500px;
    margin: 0 auto;
}

/* Styled Google Button */
.google-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: 100%;
    padding: 10px;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    background: white;
    cursor: pointer;
    margin-bottom: 20px;
    text-decoration: none;
    color: #1e293b;
    font-weight: 500;
}

/* User Message - Aligned right like a chat app */
.msg-user {
    background: #ffffff;
    border-radius: 20px 20px 4px 20px;
    padding: 1.2rem;
    margin: 1rem 0 1rem auto;
    box-shadow: 0 4px 15px rgba(0,0,0,0.04);
    border: 1px solid #f1f5f9;
    max-width: 80%;
}

/* AI Message - Glassmorphism feel */
.msg-ai {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(8px);
    border-left: 6px solid #8b5cf6;
    border-radius: 4px 20px 20px 20px;
    padding: 1.2rem;
    margin: 1rem auto 1rem 0;
    box-shadow: 0 8px 30px rgba(0,0,0,0.05);
    max-width: 85%;
}

/* Timer Card - Elevated Look */
.timer-card {
    background: white;
    border: none;
    border-radius: 24px;
    padding: 30px;
    text-align: center;
    box-shadow: 0 20px 40px rgba(0,0,0,0.06);
}

.timer-big {
    font-size: 52px;
    font-weight: 800;
    background: linear-gradient(to bottom, #1e293b, #64748b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
}

/* Hints - Soft Blue */
.hint-card {
    margin-top: 15px;
    background: #f0f7ff;
    border-radius: 20px;
    padding: 20px;
    border: 1px solid #dbeafe;
}

/* Buttons - Modern Rounded */
.stButton button {
    border-radius: 12px !important;
    background-color: #6366f1 !important;
    color: white !important;
    border: none !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    transition: transform 0.2s ease !important;
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(99, 102, 241, 0.3) !important;
}

/* ✅ Sticky timer wrapper (REPLACES the nth-child column selector) */
.floating-timer {
    position: fixed;
    right: 30px;
    top: 120px;
    width: 300px;
    z-index: 9999;
    backdrop-filter: blur(10px);
}

/* Highlight colors (ensure present for your rendered highlighted block) */
.hl_spell {
    background: rgba(249, 115, 22, 0.35);
    padding: 0 3px;
    border-radius: 6px;
}
.hl_gram {
    background: rgba(234, 179, 8, 0.35);
    padding: 0 3px;
    border-radius: 6px;
}
</style>
""",
    unsafe_allow_html=True
)
debug_box = st.empty()

# ---------------- Constants & Helpers ----------------
PARTS = ["INTRODUCTION", "BODY 1", "BODY 2", "BODY 3", "CONCLUSION"]


def word_count(text):
    return len(re.findall(r"\b[\w']+\b", (text or "").strip()))


def detect_topic(text):
    m = re.search(r'essay\s+on\s+"?(.+?)"?$', (text or "").strip(), flags=re.IGNORECASE)
    return m.group(1).strip() if m else (text or "").strip('"').rstrip(".!?")


def part_word_targets(level, part):
    targets = {
        "Primary": {"INTRO": (10, 20), "BODY": (60, 85), "CONCL": (40, 60)},
        "Secondary": {"INTRO": (10, 20), "BODY": (110, 145), "CONCL": (70, 95)},
        "Higher Secondary": {"INTRO": (10, 20), "BODY": (160, 210), "CONCL": (100, 135)},
    }
    lvl = targets.get(level, targets["Primary"])
    if "INTRODUCTION" in part:
        return lvl["INTRO"]
    if "BODY" in part:
        return lvl["BODY"]
    return lvl["CONCL"]


def get_timer_seconds(level, strictness):
    times = {"Primary": 120, "Secondary": 120, "Higher Secondary": 120}
    multiplier = 1.0 - (strictness * 0.1)
    return int(times.get(level, 300) * multiplier)


def format_mmss(seconds: int) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds//60}m {seconds%60}s"


# ---------------- Floating Timer Overlay ----------------
def floating_timer(time_text, current_part, timer_started):
    color = "#ef4444" if time_text == "0m 0s" else "#1e293b"
    timer_box = st.container()

    timer_box.markdown(
        f"""
        <div class="timer-card">
            <div style="font-weight:700;">⏱ Time Left</div>
            <div class="timer-big" style="color:{color};">{time_text}</div>
        </div>

        <div class="hint-card">
            <div style="font-weight:700;">Tutor Hint</div>
            <div>Make sure your <b>{current_part}</b> is clear and concise.</div>
            <div style="margin-top:6px; color:#334155;">
                {"Timer is running." if timer_started else "Timer starts when typing."}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    timer_box.float("position:fixed; right:30px; top:140px; width:300px; z-index:999;")


# ---------------- AI Engines ----------------
def ollama_chat(messages, temperature=0.7, max_tokens=300):
    try:
        hf_token = st.secrets["HF_API_TOKEN"]
        hf_model = st.secrets["HF_MODEL"]

        r = requests.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {hf_token}",
                "Content-Type": "application/json",
            },
            json={
                "model": hf_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=120,
        )

        data = r.json()

        # save full response for debug
        st.session_state["debug_hf_full_response"] = data

        if "error" in data:
            return f"⚠️ API Error: {data['error']}"

        if "choices" not in data:
            return f"⚠️ Error: Unexpected response: {data}"

        msg = data["choices"][0].get("message", {})

        content = msg.get("content")

        # ---- CASE 1 : content is normal string
        if isinstance(content, str):
            return content.strip()

        # ---- CASE 2 : content is list of blocks
        if isinstance(content, list):
            texts = []

            for block in content:
                if isinstance(block, dict):
                    if "text" in block:
                        texts.append(block["text"])
                    elif block.get("type") == "text" and "text" in block:
                        texts.append(block["text"])

            return "\n".join(texts).strip()

        return "⚠️ Error: No readable content"

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def tokenize_with_spans(text):
    tokens = []
    for m in re.finditer(r"\w+|[^\w\s]", text):
        tokens.append({
            "token": m.group(0),
            "start": m.start(),
            "end": m.end()
        })
    return tokens

def tokenize_with_spans(text):
    tokens = []
    for m in re.finditer(r"\w+|[^\w\s]", text):
        tokens.append({
            "token": m.group(0),
            "start": m.start(),
            "end": m.end()
        })
    return tokens

def build_token_prompt(student_text, tokens):
    numbered_tokens = "\n".join(
        [f"{i}: {t['token']}" for i, t in enumerate(tokens)]
    )

    return f"""
You are a strict proofreader.

The student typed this paragraph:
{student_text}

Here is the numbered token list:
{numbered_tokens}

Return ONLY valid JSON in this exact format:
{{
  "spelling_token_indexes": [0, 3],
  "grammar_token_ranges": [[4, 7], [10, 12]],
  "corrected_text": "Corrected full paragraph here"
}}

Rules:
- Return JSON only
- No markdown
- No explanation
- spelling_token_indexes must contain indexes of individual misspelled tokens
- grammar_token_ranges must contain [start_index, end_index] inclusive
- corrected_text must be the full corrected paragraph
- Use only indexes from the numbered token list
""".strip()

def render_token_highlighted_block(text, tokens, spelling_token_indexes, grammar_token_ranges):
    char_labels = [None] * len(text)

    for idx in spelling_token_indexes:
        tok = tokens[idx]
        for i in range(tok["start"], tok["end"]):
            if 0 <= i < len(char_labels):
                char_labels[i] = "spell"

    for start_idx, end_idx in grammar_token_ranges:
        for idx in range(start_idx, end_idx + 1):
            tok = tokens[idx]
            for i in range(tok["start"], tok["end"]):
                if 0 <= i < len(char_labels) and char_labels[i] != "spell":
                    char_labels[i] = "gram"

    parts = []
    current_label = None
    buffer = []

    for i, ch in enumerate(text):
        label = char_labels[i]

        if label != current_label:
            if buffer:
                segment = html.escape("".join(buffer))
                if current_label == "spell":
                    parts.append(f'<span class="hl_spell">{segment}</span>')
                elif current_label == "gram":
                    parts.append(f'<span class="hl_gram">{segment}</span>')
                else:
                    parts.append(segment)
            buffer = [ch]
            current_label = label
        else:
            buffer.append(ch)

    if buffer:
        segment = html.escape("".join(buffer))
        if current_label == "spell":
            parts.append(f'<span class="hl_spell">{segment}</span>')
        elif current_label == "gram":
            parts.append(f'<span class="hl_gram">{segment}</span>')
        else:
            parts.append(segment)

    highlighted_html = "".join(parts)

    return f"""
<div class='msg-ai'>
  <div class='small'><b>Feedback:</b>
    <span style='color:#f97316'>Orange=Spelling</span>,
    <span style='color:#eab308'>Yellow=Grammar</span>
  </div>
  <div style='background:white; padding:12px; border-radius:10px; border:1px solid #e2e8f0; margin-top:8px; white-space:pre-wrap;'>
    {highlighted_html}
  </div>
</div>
"""

# ---------------- Auth Logic ----------------



def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def make_pkce_pair():
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


from urllib.parse import quote
import time


def auth_gate():
    if "sb_session" not in st.session_state:
        st.session_state.sb_session = None

    # Read token returned from external frontend login page
    params = st.query_params
    access_token = params.get("access_token", None)

    if isinstance(access_token, list):
        access_token = access_token[0] if access_token else None

    # If token came from Google frontend login page
    if access_token and not st.session_state.sb_session:
        try:
            user_res = supabase_admin.auth.get_user(access_token)
    
            if not user_res or not user_res.user:
                st.error("Invalid Google login token.")
                st.stop()
    
            user = user_res.user
            google_email = user.email


            google_email = (user.email or "").strip().lower()
            st.write("Google email from token:", google_email)
            
            prof = (
                supabase_service.table("profiles")
                .select("id, email, full_name")
                .eq("email", google_email)
                .limit(1)
                .execute()
            )
            
            # Temporary debug
            st.write("Google email from token:", google_email)
            st.write("Matched profiles:", prof.data)
            
            if not prof.data:
                st.error("No account found for this Google email. Please sign up first using the Sign Up form.")
                st.stop()
    
            # Existing account found → allow login
            st.session_state.sb_session = SimpleNamespace(
                access_token=access_token,
                user=user
            )
            
            st.query_params.clear()
            st.rerun()
    
        except Exception as e:
            st.error(f"Google login failed: {e}")
            st.stop()

    # If not logged in, show auth UI
    if not st.session_state.sb_session:
        st.markdown(
            '<div class="hero-container"><h1 style="margin:0;">🎓 AI Instructor Pro</h1>'
            '<p style="opacity:0.9;">The smartest way to master English essays</p></div>',
            unsafe_allow_html=True,
        )

        # Google login button now opens external login page
        st.markdown('<div class="auth-wrapper">', unsafe_allow_html=True)

        st.link_button(
            "🌐 Continue with Google",
            "https://fash1980.github.io/ai-instructor-pro/login.html",
            use_container_width=True,
        )
        
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("🔐 User Sign In / Sign Up", expanded=True):
            tab_login, tab_signup = st.tabs(["Sign In", "Sign Up"])

            with tab_login:
                email = st.text_input("Email", key="login_email")
                pw = st.text_input("Password", type="password", key="login_pw")

                if st.button("Sign In", use_container_width=True):
                    try:
                        res = supabase_admin.auth.sign_in_with_password(
                            {"email": email, "password": pw}
                        )
                        st.session_state.sb_session = res.session
                        st.rerun()
                    except Exception as e:
                        st.error(f"Invalid email or password: {e}")

            with tab_signup:
                reg_name = st.text_input("Full Name", placeholder="Enter your name", key="reg_name")
                reg_age = st.number_input("Age", min_value=5, max_value=100, value=15, key="reg_age")
                reg_lvl = st.selectbox(
                    "Education Level",
                    ["Primary", "Secondary", "Higher Secondary"],
                    key="reg_lvl_form",
                )
                reg_email = st.text_input("Email", key="reg_email")
                reg_pw = st.text_input("Password", type="password", key="reg_pw")

                if st.button("Create Account", use_container_width=True):
                    if reg_name and reg_email and reg_pw:
                        try:
                            auth_res = supabase_admin.auth.sign_up(
                                {"email": reg_email, "password": reg_pw}
                            )

                            if auth_res.user:
                                supabase_admin.table("profiles").upsert(
                                    {
                                        "id": auth_res.user.id,
                                        "full_name": reg_name,
                                        "email": reg_email,
                                        "age": reg_age,
                                        "education_level": reg_lvl,
                                    }
                                ).execute()

                                st.success("Account created! You can now Sign In.")

                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    else:
                        st.warning("Please fill in all fields")

        st.stop()

    user = st.session_state.sb_session.user
    return user.id, user.email, st.session_state.sb_session.access_token


# ---------------- Main App ----------------
user_id, user_email, access_token = auth_gate()
db = user_client(access_token)

# Fetch user profile data to get the saved level
if "level" not in st.session_state:
    try:
        profile_res = (
            db.table("profiles").select("education_level").eq("id", user_id).single().execute()
        )
        if profile_res.data:
            st.session_state.level = profile_res.data["education_level"]
        else:
            st.session_state.level = "Secondary"  # Default if profile not found
    except Exception:
        st.session_state.level = "Secondary"


# Sidebar
with st.sidebar:
    st.title(":material/settings: Class Settings")
    st.write(f":material/person: **Welcome, {user_email}**")

    # Use the saved level as the default index
    level_list = ["Primary", "Secondary", "Higher Secondary"]
    # 2. Get the index of the user's saved level
    try:
        default_idx = level_list.index(st.session_state.level)
    except Exception:
        default_idx = 1  # Default to Secondary if something goes wrong

    # 3. Render the selectbox but DISABLE it so they can't change it
    st.session_state.level = st.selectbox(
        "Education Level",
        level_list,
        index=default_idx,
        disabled=True,  # <--- THIS LOCKS THE DROP DOWN
        help="This level is fixed based on your profile settings.",
    )

    st.session_state.strictness = st.slider("Strictness Level", 0, 3, 2)

    # ✅ Refined step-by-step Tutor Hint box (matches current_part)
    current_part_for_hint = None
    if "step" in st.session_state and st.session_state.step == "COLLECT_PART":
        try:
            current_part_for_hint = PARTS[st.session_state.part_i]
        except Exception:
            current_part_for_hint = None

    if current_part_for_hint:
        min_w_hint, max_w_hint = part_word_targets(st.session_state.level, current_part_for_hint)
        taught_key = f"taught_{current_part_for_hint}"
        taught_state = st.session_state.get(taught_key, False)

        st.markdown(
            f"""
            <div style="font-weight:800; margin-bottom:6px;">
            <span class="material-symbols-rounded">lightbulb</span> Step Tutor Hint
            </div>
              <div style="font-size:14px; color:#0f172a;">
                <b>Now writing:</b> {current_part_for_hint}<br>
                <b>Target:</b> {min_w_hint}-{max_w_hint} words<br>
                <b>Lesson:</b> {"Given <span class='material-symbols-rounded' style='color:#22c55e;'>check_circle</span>" if taught_state else "Coming now..."}
              </div>
              <div style="margin-top:10px; font-size:13px; color:#334155;">
                Follow the tutor’s points for this section. Don’t write the full essay at once.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    elif "step" in st.session_state and st.session_state.step == "ASK_TOPIC":
        st.markdown(
            """
            <div class="hint-card" style="margin-top:10px;">
              <div style="font-weight:800; margin-bottom:6px;">
<span class="material-symbols-rounded" style="color:#6366f1; vertical-align:middle;">psychology</span>
Step Tutor Hint
</div>
              <div style="font-size:14px; color:#0f172a;">
                Enter your essay topic to begin. You will be taught section-by-section.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button(":material/history_edu: View Past Progress", use_container_width=True):
        try:
            res = (
                db.table("classes")
                .select("*")
                .eq("user_id", user_id)
                .order("started_at", desc=True)
                .execute()
            )
            if res.data:
                st.dataframe(pd.DataFrame(res.data)[["topic", "level", "badge_score"]])
            else:
                st.info("No history yet.")
        except Exception:
            st.info("No history yet.")

    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ---------------- State Init ----------------
if "step" not in st.session_state:
    st.session_state.update(
        {
            "step": "ASK_TOPIC",
            "chat": [],
            "corrected_parts": {},
            "part_i": 0,
            "topic": "",
            "class_id": None,

            # Timer state
            "timer_started": False,
            "part_start_time": None,

            "is_processing": False,
            "pending_text": None,
        "is_teaching": False,
        }
    )


# Header
st.markdown(
f"""
<div class="hero-container">
<h2 style="margin:0;font-size:38px;font-weight:800;">AI Instructor Pro</h2>
<div style="opacity:0.9;margin-top:6px;">
AI-Powered Essay Writing Coach
</div>
</div>
""",
unsafe_allow_html=True
)


# ---------------- STEP 1: Ask Topic ----------------
if st.session_state.step == "ASK_TOPIC":
    topic_in = st.text_input("Enter your essay topic:", placeholder="e.g. Write an essay on 'Water Conservation'")
    if st.button("Start My Class"):
        topic = detect_topic(topic_in)
        st.session_state.topic = topic

        # Create DB Class Record
        try:
            res = (
                db.table("classes")
                .insert(
                    {
                        "user_id": user_id,
                        "topic": topic,
                        "level": st.session_state.level,
                        "strictness": st.session_state.strictness,
                        "started_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )
            st.session_state.class_id = res.data[0]["id"]
        except Exception:
            st.session_state.class_id = None

        # ✅ CHANGE 1: Do NOT ask AI to plan whole essay
        # Just acknowledge start (step-by-step teaching will happen inside the loop)
        st.session_state.chat.append(
            {
                "role": "ai",
                "content": f"Great! Let's start our lesson on **{topic}**. We will write this essay step-by-step.",
            }
        )

        st.session_state.step = "COLLECT_PART"
        st.session_state.part_i = 0

        # Reset timer for first part
        st.session_state.timer_started = False
        st.session_state.part_start_time = None

        st.rerun()


# ---------------- STEP 2: Collect Parts ----------------
elif st.session_state.step == "COLLECT_PART":
    current_part = PARTS[st.session_state.part_i]
    min_w, max_w = part_word_targets(st.session_state.level, current_part)
    max_sec = get_timer_seconds(st.session_state.level, st.session_state.strictness)

    # ✅ Teaching state guard (prevents autorefresh from cancelling the Ollama call)
    current_step_key = f"taught_{current_part}"
    st.session_state.is_teaching = current_step_key not in st.session_state

    # ✅ START TIMER ONLY AFTER teaching is done
    if (not st.session_state.timer_started) and (not st.session_state.is_processing) and (not st.session_state.is_teaching):
        st.session_state.timer_started = True
        st.session_state.part_start_time = time.time()

    # Live refresh every 1s (DISABLE during teaching + processing)
    if HAS_AUTOREFRESH and (not st.session_state.is_processing) and (not st.session_state.is_teaching):
        st_autorefresh(interval=1000, key=f"refresh_{st.session_state.part_i}")

    # ✅ TIMER LOGIC (compute remaining safely)
    if st.session_state.part_start_time:
        elapsed = time.time() - st.session_state.part_start_time
    else:
        elapsed = 0
    remaining = max(0, max_sec - int(elapsed))

    # ✅ SHOW FLOATING TIMER (streamlit-float)
    floating_timer(format_mmss(remaining), current_part, st.session_state.timer_started)

    # Layout (right column not needed anymore, but kept for spacing if you want)
    main_col, side_col = st.columns([3.2, 1.1], gap="large")

    with main_col:
        # ✅ CHANGE 2: Step-by-step teaching logic (teach current part only once)
        current_step_key = f"taught_{current_part}"
        if current_step_key not in st.session_state:
            with st.spinner(f"Teaching you how to write the {current_part}..."):
                teaching_prompt = (
                    f"You are an expert English Tutor for school students. "
                    f"The student is writing an essay on '{st.session_state.topic}'. "
                    f"They are now writing the {current_part} for a {st.session_state.level} level essay. "
                    f"Explain briefly what a good introduction should include in simple school-level language. "
                    f"Do NOT use the term 'thesis statement'. Instead, say that the last sentence of the introduction "
                    f"should clearly show the main idea or focus of the essay. "
                    f"Give 2-3 specific points or themes they can mention for this topic. "
                    f"Do NOT write the paragraph for them. "
                    f"Keep the guidance clear, student-friendly, and not too academic. "
                    f"End by saying exactly: 'Now, please write your INTRODUCTION.'"
                )
                lesson = ollama_chat([{ "role": "user", "content": teaching_prompt }])
                st.session_state.chat.append({"role": "ai", "content": lesson})
                st.session_state[current_step_key] = True
                st.rerun()  # show lesson before the user types

        # Chat History
        for m in st.session_state.chat:
            if m["role"] == "ai_html":
                st.markdown(m["content"], unsafe_allow_html=True)
                continue

            role = "You" if m["role"] == "user" else "Tutor"
            div = "msg-user" if m["role"] == "user" else "msg-ai"
            safe = html.escape(m["content"]).replace("\n", "<br>")
            st.markdown(f"<div class='{div}'><b>{role}</b><br>{safe}</div>", unsafe_allow_html=True)

        st.markdown(f"### Writing: {current_part}")

        with st.form(key=f"write_form_{st.session_state.part_i}", clear_on_submit=False):
                    # 2. Add this HTML/JS block for the LIVE COUNTER
            components.html(f"""
                <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet">
                <div style="font-family: sans-serif; color: #64748b; font-size: 14px; margin-bottom: 5px;">
                    Word Count: <span id="wordCount">0</span> / {min_w}
                </div>
            
                <div id="pasteWarning" style="
                    display:none;
                    margin-top:8px;
                    padding:10px 12px;
                    border-radius:10px;
                    background:#eefcf3;
                    border:1px solid #c7f0d8;
                    color:#166534;
                    font-size:14px;
                    font-family:sans-serif;
                ">
                    <span class="material-symbols-rounded" style="vertical-align:middle;">edit</span>
                    Please type in your own words so you can improve your writing skills.
                </div>
            
                <script>
                    function attachHandlers() {{
                        const textareas = parent.document.querySelectorAll('textarea');
                        if (!textareas || textareas.length === 0) return;
            
                        const textarea = textareas[textareas.length - 1];
                        const display = document.getElementById('wordCount');
                        const warning = document.getElementById('pasteWarning');
            
                        function countWords() {{
                            const text = textarea.value.trim();
                            const count = text ? text.split(/\\s+/).length : 0;
                            display.innerText = count;
                        }}
            
                        function showWarning() {{
                            warning.style.display = 'block';
                            clearTimeout(window.__pasteWarnTimer);
                            window.__pasteWarnTimer = setTimeout(() => {{
                                warning.style.display = 'none';
                            }}, 3000);
                        }}
            
                        if (!textarea.dataset.handlersAttached) {{
                            textarea.addEventListener('input', countWords);
            
                            textarea.addEventListener('paste', function(e) {{
                                e.preventDefault();
                                showWarning();
                            }});
            
                            textarea.addEventListener('drop', function(e) {{
                                e.preventDefault();
                                showWarning();
                            }});
            
                            textarea.addEventListener('keydown', function(e) {{
                                if ((e.ctrlKey || e.metaKey) && (e.key === 'v' || e.key === 'V')) {{
                                    e.preventDefault();
                                    showWarning();
                                }}
                            }});
            
                            textarea.dataset.handlersAttached = "true";
                        }}
            
                        countWords();
                    }}
            
                    setTimeout(attachHandlers, 300);
                </script>
            """, height=95)
            student_text = st.text_area(
                f"Target: {min_w}-{max_w} words",
                height=220,
                key=f"input_{st.session_state.part_i}",
                placeholder="Start typing here...",
            )

            #st.caption(f"Word count: {word_count(student_text)} / min {min_w}")

            submitted = st.form_submit_button("Submit Paragraph")

        # Warnings (outside form is fine)
        if remaining <= 10 and remaining > 0:
            st.warning("⚠️ Hurry! Only a few seconds left.")
        if remaining <= 0:
            st.error("⏳ Time is up! Please submit your paragraph now.")

        # ---------------- PHASE A: queue submission quickly (NO OLLAMA CALLS HERE) ----------------
        if submitted and (not st.session_state.is_processing):
            if word_count(student_text) < min_w:
                st.error(f"Write more! Min {min_w} words.")
            else:
                # Stop timer + store submission safely
                st.session_state.timer_started = False
                st.session_state.pending_text = student_text
                st.session_state.is_processing = True
                st.rerun()

                # ---------------- PHASE B: heavy processing runs AFTER rerun, with autorefresh OFF ----------------
        if st.session_state.is_processing and st.session_state.pending_text is not None:
            student_text = st.session_state.pending_text
            late = remaining <= 0

            with st.status("Tutor is reviewing your work...", expanded=True) as status:
                st.write("🔍 Scanning for mistakes...")

                analysis = scan_tokens_with_hf(student_text)
                tokens = analysis["tokens"]
                spelling_token_indexes = analysis["spelling_token_indexes"]
                grammar_token_ranges = analysis["grammar_token_ranges"]
                corrected = analysis["corrected_text"]

                st.write("STUDENT TEXT:", student_text)
                st.write("TOKEN ANALYSIS:", analysis)

                with debug_box.container():
                    st.warning("DEBUG MODE")
                    st.write("Raw response:", st.session_state.get("debug_raw_highlight", "not available"))
                    st.write("Parsed mistakes:", st.session_state.get("debug_parsed_mistakes", {}))
                    st.write("JSON error:", st.session_state.get("debug_json_error", "none"))
                    st.write("HF full response:", st.session_state.get("debug_hf_full_response", {}))

                with st.sidebar:
                    st.markdown("### Debug")
                    st.write("Raw:", st.session_state.get("debug_raw_highlight", "none"))
                    st.write("Parsed:", st.session_state.get("debug_parsed_mistakes", {}))
                    st.write("JSON error:", st.session_state.get("debug_json_error", "none"))
                    st.write("HF full response:", st.session_state.get("debug_hf_full_response", {}))

                st.write("✍️ Refining your paragraph...")

                # DB save
                if st.session_state.class_id:
                    try:
                        payload = {
                            "class_id": st.session_state.class_id,
                            "user_id": user_id,
                            "part": current_part,
                            "student_text": student_text,
                            "corrected_text": corrected,
                            "word_count": word_count(student_text),
                            "late": late,
                        }
                        db.table("submissions").insert(payload).execute()
                    except Exception:
                        st.warning("Note: Saved locally (DB Sync Issue)")

                status.update(label="Feedback Ready!", state="complete", expanded=False)

            # Chat updates
            st.session_state.chat.append({"role": "user", "content": student_text})
            st.session_state.chat.append(
                {
                    "role": "ai_html",
                    "content": render_token_highlighted_block(
                        student_text,
                        tokens,
                        spelling_token_indexes,
                        grammar_token_ranges
                    )
                }
            )
            st.session_state.corrected_parts[current_part] = corrected
            st.session_state.chat.append({"role": "ai", "content": f"**Refined Version:**\n\n{corrected}"})

            # Advance part
            st.session_state.part_i += 1
            st.session_state.part_start_time = None
            if st.session_state.part_i >= len(PARTS):
                st.session_state.step = "DONE"

            # Clear locks BEFORE rerun
            st.session_state.pending_text = None
            st.session_state.is_processing = False

            st.rerun()


# ---------------- STEP 3: Done ----------------
elif st.session_state.step == "DONE":
    st.balloons()
    st.success("🎉 Essay Complete! Clapping for you!")

    # Update End Time & Badge
    if st.session_state.class_id:
        try:
            db.table("classes").update(
                {
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                    "badge": "Excellent",
                    "badge_score": 90,
                }
            ).eq("id", st.session_state.class_id).execute()
        except Exception:
            pass

    # Build final essay in correct order
    # Build final essay in correct order (CLEAN)
    def clean_paragraph(text: str) -> str:
        if not text:
            return ""

        lines = (text or "").splitlines()
        out = []
        skipping_bullets = False

        for ln in lines:
            s = ln.strip()
            if not s:
                # keep paragraph spacing
                out.append("")
                continue

            low = s.lower()
            re.sub(r"(?im)^\s*here('?s)?\s+a?\s*corrected\s+version\s+of.*?:\s*$", "", low)
            re.sub(r"(?im)^\s*here\s+is\s+the\s+corrected.*?:\s*$", "", low)
            re.sub(r"(?im)^\s*here('?s)?\s+the\s+corrected\s+paragraph\s*:?\s*$", "", low)
            re.sub(r"(?im)^\s*(introduction|conclusion|body\s*\d+)\s*:\s*$", "", low)
            # ---- Remove meta / instruction headers ----
            
            if low.startswith("here is the corrected"):
                continue
            if low.startswith("here's the corrected"):
                continue
            if low.startswith("i corrected the following"):
                skipping_bullets = True
                continue
            if low.startswith("i made the following"):
                skipping_bullets = True
                continue
            if low.startswith("changes made include"):
                skipping_bullets = True
                continue
            if low.startswith("corrected errors"):
                skipping_bullets = True
                continue

            # ---- Remove section labels like "BODY 3:" / "INTRODUCTION:" etc ----
            if re.match(r"^(introduction|conclusion|body\s*\d+)\s*:", low):
                continue

            # ---- Skip bullet lists that come after those meta headings ----
            if skipping_bullets:
                if s.startswith(("-", "•", "*")):
                    continue
                # if we reach a normal sentence, stop skipping bullets
                skipping_bullets = False

            out.append(s)

        cleaned = "\n".join(out)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned


    clean_essay = "\n\n".join(
        [clean_paragraph(st.session_state.corrected_parts.get(part, "")) for part in PARTS]
    ).strip()


    st.markdown("## Final Essay")
    st.write(clean_essay)
    # Build "Essay with Instructions" (uses chat history)
    def chat_to_text(chat):
        out = []
        for m in chat:
            role = m.get("role", "")
            content = m.get("content", "")

            if role == "ai_html":
                # strip HTML tags so it becomes readable in txt
                content = re.sub(r"<[^>]+>", "", content)
                content = html.unescape(content)

            if role == "user":
                out.append(f"STUDENT:\n{content}\n")
            elif role in ("ai", "ai_html"):
                out.append(f"TUTOR:\n{content}\n")
        return "\n".join(out).strip()

    essay_with_instructions = (
        f"TOPIC: {st.session_state.topic}\n"
        f"LEVEL: {st.session_state.level}\n"
        f"STRICTNESS: {st.session_state.strictness}\n"
        + ("=" * 60) + "\n\n"
        + "LESSON + FEEDBACK LOG\n\n"
        + chat_to_text(st.session_state.chat)
        + "\n\n" + ("=" * 60) + "\n\n"
        + "CLEAN FINAL ESSAY\n\n"
        + clean_essay
    )

    # ✅ Two download options
    d1, d2 = st.columns(2)

    with d1:
        st.download_button(
            "Download Clean Version (Only Essay)",
            clean_essay,
            file_name="essay_clean.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with d2:
        st.download_button(
            "Download Essay with Instructions",
            essay_with_instructions,
            file_name="essay_with_instructions.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # Optional: logout + new lesson
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Start New Lesson", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    with c2:
        if st.button("Logout", use_container_width=True):
            try:
                supabase_admin.auth.sign_out()
            except Exception:
                pass
            st.session_state.clear()
            st.rerun()

















































