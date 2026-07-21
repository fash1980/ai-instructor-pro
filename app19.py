import re
import html
import time
import requests
import textwrap
import streamlit as st
import pandas as pd
from supabase import create_client
from deep_translator import GoogleTranslator
from datetime import datetime, timezone
import streamlit.components.v1 as components
from groq import Groq
import streamlit as st
from types import SimpleNamespace
import os, base64, hashlib, secrets, time
import streamlit as st
import streamlit.components.v1 as components
import extra_streamlit_components as stx
from streamlit_float import float_init
from urllib.parse import quote
import json
import google.generativeai as genai

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
# ---------------- Debug State Init ----------------
if "debug_log" not in st.session_state:
    st.session_state.debug_log = []

if "debug_last" not in st.session_state:
    st.session_state.debug_last = {}

if "done_celebrated" not in st.session_state:
    st.session_state.done_celebrated = False
    
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
PARTS = ["INTRODUCTION", "SECTION 1", "SECTION 2", "SECTION 3", "CONCLUSION"]


def word_count(text):
    return len(re.findall(r"\b[\w']+\b", (text or "").strip()))


def detect_topic(text):
    m = re.search(r'essay\s+on\s+"?(.+?)"?$', (text or "").strip(), flags=re.IGNORECASE)
    return m.group(1).strip() if m else (text or "").strip('"').rstrip(".!?")


def part_word_targets(level, part):
    targets = {
        "Primary": {"INTRO": (15, 20), "BODY": (15, 20), "CONCL": (15, 20)},
        "Secondary": {"INTRO": (15, 20), "BODY": (15, 20), "CONCL": (15, 20)},
        "Higher Secondary": {"INTRO": (15, 20), "BODY": (15, 20), "CONCL": (15, 20)},
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
def floating_timer(time_text, current_part, timer_started, retry_hint=""):
    color = "#ef4444" if time_text == "0m 0s" else "#1e293b"
    timer_box = st.container()
    extra_hint_html = ""
    if retry_hint:
        extra_hint_html = f"""
        <div class="hint-card" style="margin-top:15px; background:#fff7ed; border:1px solid #fed7aa;">
            <div style="font-weight:700;">Correction Hint</div>
            <div style="margin-top:6px; color:#7c2d12;">
                {html.escape(retry_hint)}
            </div>
        </div>
        """
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
        {extra_hint_html}
        """,
        unsafe_allow_html=True,
    )

    timer_box.float("position:fixed; right:30px; top:140px; width:300px; z-index:999;")


# ---------------- AI Engines ----------------
#def ollama_chat(messages, temperature=0.7, max_tokens=300):
    #try:
        #hf_token = st.secrets["HF_API_TOKEN"]
        #hf_model = st.secrets["HF_MODEL"]

        #r = requests.post(
            #"https://router.huggingface.co/v1/chat/completions",
            #headers={
                #"Authorization": f"Bearer {hf_token}",
                #"Content-Type": "application/json",
            #},
            #json={
                #"model": hf_model,
                #"messages": messages,
                #"temperature": temperature,
                #"max_tokens": max_tokens,
            #},
            #timeout=120,
        #)

        #data = r.json()

        # save full response for debug
        #st.session_state["debug_hf_full_response"] = data

        #if "error" in data:
            #return f"⚠️ API Error: {data['error']}"

        #if "choices" not in data or not data["choices"]:
            #return f"⚠️ Error: Unexpected response: {data}"

        #choice = data["choices"][0]
        #msg = choice.get("message", {}) or {}

        #finish_reason = choice.get("finish_reason", "unknown")
        #st.session_state["debug_finish_reason"] = finish_reason
        #st.session_state["debug_message"] = msg

        #content = msg.get("content", None)
        #reasoning = msg.get("reasoning", None)

        # ---- CASE 1 : content is normal string
        #if isinstance(content, str) and content.strip():
            #return content.strip()

        # ---- CASE 2 : content is list of blocks
        #if isinstance(content, list):
            #texts = []
            #for block in content:
                #if isinstance(block, dict):
                    #txt = block.get("text")
                    #if isinstance(txt, str) and txt.strip():
                        #texts.append(txt.strip())

            #if texts:
                #return "\n".join(texts).strip()

        # ---- CASE 3 : some models return reasoning instead of content
        #if isinstance(reasoning, str) and reasoning.strip():
            #return reasoning.strip()

        # ---- CASE 4 : nothing readable found
        #return f"⚠️ Error: No readable content | finish_reason={finish_reason}"

    #except Exception as e:
        #return f"⚠️ Error: {str(e)}"
# This was LLM for Gemini
#def ollama_chat(messages, temperature=0.7, max_tokens=300):
   # try:
       # genai.configure(
           # api_key=st.secrets["GEMINI_API_KEY"]
        #)

       # model = genai.GenerativeModel(
           # "gemini-2.0-flash-lite"
       # )

      #  prompt = "\n".join(
          #  [m["content"] for m in messages]
      #  )

     #   response = model.generate_content(
          #  prompt,
           # generation_config={
               # "temperature": temperature,
              #  "max_output_tokens": max_tokens,
          #  }
      #  )

       # return response.text.strip()

  #  except Exception as e:
       # return "⚠️ AI is temporarily busy. Please wait a minute and try again."


def ollama_chat(messages, temperature=0.7, max_tokens=300):
    try:
        client = Groq(
            api_key=st.secrets["GROQ_API_KEY"]
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ Groq Error: {e}"
def translate_english_to_malay(english_text):
    if not english_text.strip():
        return ""
    try:
        return GoogleTranslator(source="en", target="ms").translate(english_text)
    except Exception:
        return english_text
def translate_malay_to_english(malay_text):
    if not malay_text.strip():
        return ""

    try:
        return GoogleTranslator(
            source="ms",
            target="en"
        ).translate(malay_text)

    except Exception:
        return malay_text
    
def build_markup_prompt(student_text, active_lang):
    return f"""
Return exactly 2 lines only.

Line 1 must start with:
MARKED:

Line 2 must start with:
CORRECTED:

Rules:
- The paragraph language is {active_lang}.
- Check spelling and grammar in {active_lang}.
- Check each and every word for spelling and use [[S]] tag to mark start of wrong spelling word and [[/S]] tag to mark the end of wrong spelling word.
- Check Grammar syntax very thoroughly and use and use [[G]] tag to mark start of wrong spelling word and [[/G]] tag to mark the end of wrong spelling word.
- Once written the refines version compare it with student written version and check if any spelling or grammar mistake remain untagged then tag them.
- Revise the whole student written paragraph 3 times so no spelling mistake is left unchecked.
- Revise the whole student written paragraph 3 times so no english grammar mistake is left unchecked.
- In MARKED, keep the student's original paragraph exactly the same, only add tags
- Every wrong word or wrong phrase must be tagged
- Do not invent errors
- Use [[S]]...[[/S]] for spelling mistakes
- Use [[G]]...[[/G]] for grammar mistakes
- Use [[S]]wrong_word[[/S]] only for spelling mistakes
- Use [[G]]wrong_phrase[[/G]] only for grammar mistakes
- A misspelled word is NEVER grammar
- For grammar, tag the full wrong phrase when possible
- CORRECTED must be the fully corrected paragraph with no tags
- No explanation
- No reasoning
- No bullets
- No markdown
- No headings
Paragraph:
{student_text}
""".strip()


def parse_marked_response(raw, student_text):
    marked_text = student_text
    corrected_text = student_text

    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    for line in lines:
        upper = line.upper()
        if upper.startswith("MARKED:"):
            marked_text = line.split(":", 1)[1].strip()
        elif upper.startswith("CORRECTED:"):
            corrected_text = line.split(":", 1)[1].strip()
    has_spelling = ("[[S]]" in marked_text) or ("[[S]" in marked_text)
    has_grammar = ("[[G]]" in marked_text) or ("[[G]" in marked_text)
    has_errors = has_spelling or has_grammar
    return {
        "marked_text": marked_text,
        "corrected_text": corrected_text,
        "has_errors": has_errors,
        "has_spelling": has_spelling,
        "has_grammar": has_grammar,
    }


def render_marked_highlighted_block(marked_text):
    safe = html.escape(marked_text)

    # accept both [[S]] and [[S]
    safe = safe.replace("[[S]]", '<span class="hl_spell">')
    safe = safe.replace("[[S]", '<span class="hl_spell">')
    safe = safe.replace("[[/S]]", "</span>")

    # accept both [[G]] and [[G]
    safe = safe.replace("[[G]]", '<span class="hl_gram">')
    safe = safe.replace("[[G]", '<span class="hl_gram">')
    safe = safe.replace("[[/G]]", "</span>")

    return f"""
<div class='msg-ai'>
  <div class='small'><b>Feedback:</b>
    <span style='color:#f97316'>Orange=Spelling</span>,
    <span style='color:#eab308'>Yellow=Grammar</span>
  </div>
  <div style='background:white; padding:12px; border-radius:10px; border:1px solid #e2e8f0; margin-top:8px; white-space:pre-wrap;'>
    {safe}
  </div>
</div>
"""
def build_retry_hint_from_marked(marked_text, current_part):
    spelling_items = re.findall(r"\[\[S\]\](.*?)\[\[/S\]\]|\[\[S\](.*?)\[\[/S\]\]", marked_text)
    grammar_items = re.findall(r"\[\[G\]\](.*?)\[\[/G\]\]|\[\[G\](.*?)\[\[/G\]\]", marked_text)

    spelling_words = []
    for a, b in spelling_items:
        val = a or b
        if val:
            spelling_words.append(val.strip())

    grammar_phrases = []
    for a, b in grammar_items:
        val = a or b
        if val:
            grammar_phrases.append(val.strip())

    hints = []

    if spelling_words:
        uniq_spell = []
        for w in spelling_words:
            if w not in uniq_spell:
                uniq_spell.append(w)
        hints.append(
            "Check the spelling of: " + ", ".join(uniq_spell[:5]) + "."
        )

    if grammar_phrases:
        uniq_gram = []
        for g in grammar_phrases:
            if g not in uniq_gram:
                uniq_gram.append(g)
        hints.append(
            "Look again at these grammar parts: " + "; ".join(uniq_gram[:3]) + "."
        )

    if not hints:
        hints.append(f"Your {current_part} looks correct. Read it once more carefully.")

    hints.append(f"Now rewrite your {current_part} in your own words and correct these mistakes.")
    return " ".join(hints)

def scan_tokens_with_hf(student_text, active_lang="English"):
    prompt = build_markup_prompt(student_text, active_lang)

    raw = ollama_chat(
        [
            {
                "role": "system",
                "content": (
                    "Return exactly 2 lines only.\n"
                    "Line 1 must start with: MARKED:\n"
                    "Line 2 must start with: CORRECTED:\n"
                    "Check only genuine spelling and grammar mistakes.\n"
                    "If the paragraph is already correct, do not tag anything.\n"
                    "Do not invent mistakes.\n"
                    "Do not mark acceptable phrases as errors.\n"
                    "Use [[S]]...[[/S]] only for clear spelling mistakes.\n"
                    "Use [[G]]...[[/G]] only for clear grammar mistakes.\n"
                    "In MARKED, keep the original paragraph exactly the same except tags.\n"
                    "In CORRECTED, give the corrected paragraph.\n"
                    "No explanation.\n"
                    "No reasoning.\n"
                    "No bullets.\n"
                    "No markdown."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.0,
        max_tokens=180
    )

    st.session_state["debug_raw_highlight"] = raw

    try:
        if raw.strip().startswith("⚠️ Error"):
            st.session_state["debug_parsed_mistakes"] = {}
            st.session_state["debug_json_error"] = raw
            return {
                "marked_text": student_text,
                "corrected_text": student_text,
                "has_errors": False,
                "has_spelling": False,
                "has_grammar": False,
            }

        parsed = parse_marked_response(raw, student_text)

        st.session_state["debug_parsed_mistakes"] = parsed
        st.session_state["debug_json_error"] = "none"
        return parsed

    except Exception as e:
        st.session_state["debug_parsed_mistakes"] = {}
        st.session_state["debug_json_error"] = str(e)
        return {
            "marked_text": student_text,
            "corrected_text": student_text,
            "has_errors": False,
            "has_spelling": False,
            "has_grammar": False,
        }

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
            #st.write("Google email from token:", google_email)
            
            prof = (
                supabase_service.table("profiles")
                .select(
                    "id, email, full_name, role, education_level, age"
                )
                .eq("email", google_email)
                .limit(1)
                .execute()
            )
            
            # Temporary debug
            #st.write("Google email from token:", google_email)
            #st.write("Matched profiles:", prof.data)
            
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

                # Public users can create Student or Teacher accounts.
                # Admin accounts must be assigned manually in Supabase.
                reg_role = st.radio(
                    "Create account as",
                    ["Student", "Teacher"],
                    horizontal=True,
                    key="reg_role"
                )
            
                reg_name = st.text_input(
                    "Full Name",
                    placeholder="Enter your full name",
                    key="reg_name"
                )
            
                # Student-specific fields
                if reg_role == "Student":
            
                    reg_age = st.number_input(
                        "Age",
                        min_value=5,
                        max_value=100,
                        value=15,
                        key="reg_age"
                    )
            
                    reg_lvl = st.selectbox(
                        "Education Level",
                        [
                            "Primary",
                            "Secondary",
                            "Higher Secondary"
                        ],
                        key="reg_lvl_form"
                    )
            
                # Teacher-specific defaults
                else:
                    reg_age = None
                    reg_lvl = None
            
                    st.info(
                        "Teacher accounts will open the Teacher Dashboard "
                        "after signing in."
                    )
            
                reg_email = st.text_input(
                    "Email",
                    key="reg_email"
                )
            
                reg_pw = st.text_input(
                    "Password",
                    type="password",
                    key="reg_pw"
                )
            
                if st.button(
                    "Create Account",
                    use_container_width=True,
                    key="create_account_button"
                ):
            
                    clean_name = reg_name.strip()
                    clean_email = reg_email.strip().lower()
            
                    if not clean_name or not clean_email or not reg_pw:
                        st.warning("Please fill in all required fields.")
            
                    elif len(reg_pw) < 6:
                        st.warning(
                            "Password must contain at least 6 characters."
                        )
            
                    else:
                        try:
                            auth_res = supabase_admin.auth.sign_up(
                                {
                                    "email": clean_email,
                                    "password": reg_pw
                                }
                            )
            
                            if not auth_res.user:
                                st.error(
                                    "Account could not be created. "
                                    "Please try again."
                                )
            
                            else:
                                profile_payload = {
                                    "id": auth_res.user.id,
                                    "full_name": clean_name,
                                    "email": clean_email,
                                    "age": reg_age,
                                    "education_level": reg_lvl,
                                    "role": reg_role.lower()
                                }
            
                                supabase_admin.table(
                                    "profiles"
                                ).upsert(
                                    profile_payload
                                ).execute()
            
                                st.success(
                                    f"{reg_role} account created successfully. "
                                    "You can now sign in."
                                )
            
                        except Exception as e:
                            st.error(f"Account creation failed: {e}")

        st.stop()

    user = st.session_state.sb_session.user
    return user.id, user.email, st.session_state.sb_session.access_token

# ---------------- Admin Dashboard ----------------

def admin_dashboard(user_email, profile):
    admin_name = profile.get("full_name") or user_email

    st.markdown(
        """
        <style>
        .admin-header {
            background: linear-gradient(135deg, #312e81, #6366f1, #9333ea);
            color: white;
            border-radius: 24px;
            padding: 36px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 20px 50px rgba(79, 70, 229, 0.20);
        }

        .admin-header h1 {
            margin: 0;
            font-size: 38px;
            font-weight: 800;
        }

        .admin-header p {
            margin-top: 10px;
            opacity: 0.9;
            font-size: 16px;
        }

        .admin-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 24px;
            padding: 35px 25px;
            text-align: center;
            min-height: 250px;
            box-shadow: 0 14px 35px rgba(15, 23, 42, 0.08);
        }

        .admin-card-icon {
            font-size: 54px;
            margin-bottom: 16px;
        }

        .admin-card-title {
            font-size: 24px;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 10px;
        }

        .admin-card-text {
            color: #64748b;
            font-size: 15px;
            margin-bottom: 22px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="admin-header">
            <h1>Admin Control Panel</h1>
            <p>
                Welcome, {html.escape(admin_name)}.
                Choose the interface you want to open.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div class="admin-card">
                <div class="admin-card-icon">👩‍🏫</div>
                <div class="admin-card-title">Teacher Dashboard</div>
                <div class="admin-card-text">
                    View classes, students, assignments and progress reports.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Enter Teacher Dashboard",
            use_container_width=True,
            key="admin_teacher_button"
        ):
            st.session_state.admin_view_mode = "teacher"
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="admin-card">
                <div class="admin-card-icon">🎓</div>
                <div class="admin-card-title">Student Dashboard</div>
                <div class="admin-card-text">
                    Open the essay-writing interface as a student.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Enter Student Dashboard",
            use_container_width=True,
            key="admin_student_button"
        ):
            st.session_state.admin_view_mode = "student"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "Logout",
        use_container_width=True,
        key="admin_logout_button"
    ):
        st.session_state.clear()
        st.rerun()

# =========================================================
# TEACHER DASHBOARD DATA
# =========================================================

def load_teacher_dashboard_data(data_client):
    """
    Load all students and their essay progress from Supabase.
    """

    try:
        students_result = (
            data_client.table("profiles")
            .select(
                "id, full_name, email, age, "
                "education_level, role"
            )
            .eq("role", "student")
            .execute()
        )

        students = students_result.data or []

    except Exception as e:
        st.error(f"Could not load students: {e}")
        students = []

    try:
        classes_result = (
            data_client.table("classes")
            .select(
                "id, user_id, topic, level, strictness, "
                "started_at, ended_at, badge, badge_score"
            )
            .order("started_at", desc=True)
            .execute()
        )

        classes = classes_result.data or []

    except Exception as e:
        st.error(f"Could not load class records: {e}")
        classes = []

    try:
        submissions_result = (
            data_client.table("submissions")
            .select(
                "id, class_id, user_id, part, "
                "word_count, late"
            )
            .execute()
        )

        submissions = submissions_result.data or []

    except Exception as e:
        st.error(f"Could not load submissions: {e}")
        submissions = []

    return students, classes, submissions


def safe_datetime(value):
    """
    Convert Supabase datetime into pandas datetime safely.
    """

    if not value:
        return pd.NaT

    try:
        return pd.to_datetime(value, utc=True)
    except Exception:
        return pd.NaT


def format_dashboard_date(value):
    """
    Format datetime for dashboard display.
    """

    dt = safe_datetime(value)

    if pd.isna(dt):
        return "Never"

    try:
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return "Never"


def build_student_progress_dataframe(
    students,
    classes,
    submissions
):
    """
    Produce one summary row per student.
    """

    progress_rows = []

    for student in students:
        student_id = student.get("id")

        student_classes = [
            item
            for item in classes
            if item.get("user_id") == student_id
        ]

        student_submissions = [
            item
            for item in submissions
            if item.get("user_id") == student_id
        ]

        total_essays = len(student_classes)

        completed_classes = [
            item
            for item in student_classes
            if item.get("ended_at")
        ]

        completed_essays = len(completed_classes)

        scores = [
            item.get("badge_score")
            for item in completed_classes
            if item.get("badge_score") is not None
        ]

        numeric_scores = []

        for score in scores:
            try:
                numeric_scores.append(float(score))
            except Exception:
                pass

        average_score = (
            round(
                sum(numeric_scores) / len(numeric_scores),
                1
            )
            if numeric_scores
            else 0
        )

        completion_rate = (
            round(
                completed_essays / total_essays * 100,
                1
            )
            if total_essays > 0
            else 0
        )

        total_paragraphs = len(student_submissions)

        late_submissions = sum(
            1
            for item in student_submissions
            if item.get("late") is True
        )

        total_words = sum(
            int(item.get("word_count") or 0)
            for item in student_submissions
        )

        started_dates = [
            safe_datetime(item.get("started_at"))
            for item in student_classes
            if item.get("started_at")
        ]

        valid_dates = [
            value
            for value in started_dates
            if not pd.isna(value)
        ]

        last_active_raw = (
            max(valid_dates)
            if valid_dates
            else pd.NaT
        )

        if total_essays == 0:
            progress_status = "Not Started"

        elif completed_essays == total_essays:
            progress_status = "Completed"

        else:
            progress_status = "In Progress"

        if total_essays == 0:
            risk_level = "No Activity"

        elif average_score < 50:
            risk_level = "High"

        elif average_score < 70:
            risk_level = "Medium"

        else:
            risk_level = "Low"

        progress_rows.append(
            {
                "Student ID": student_id,
                "Student": (
                    student.get("full_name")
                    or student.get("email")
                    or "Unknown Student"
                ),
                "Email": student.get("email") or "",
                "Level": (
                    student.get("education_level")
                    or "Not Set"
                ),
                "Essays Started": total_essays,
                "Essays Completed": completed_essays,
                "Completion Rate": completion_rate,
                "Average Score": average_score,
                "Paragraphs Submitted": total_paragraphs,
                "Total Words": total_words,
                "Late Submissions": late_submissions,
                "Status": progress_status,
                "Risk": risk_level,
                "Last Active Raw": last_active_raw,
                "Last Active": (
                    last_active_raw.strftime(
                        "%d %b %Y"
                    )
                    if not pd.isna(last_active_raw)
                    else "Never"
                )
            }
        )

    return pd.DataFrame(progress_rows)


def get_recent_student_activity(
    students,
    classes,
    limit=10
):
    """
    Build recent essay activity table.
    """

    student_lookup = {
        student.get("id"): (
            student.get("full_name")
            or student.get("email")
            or "Unknown Student"
        )
        for student in students
    }

    activity_rows = []

    for class_item in classes:
        student_id = class_item.get("user_id")

        activity_rows.append(
            {
                "Student": student_lookup.get(
                    student_id,
                    "Unknown Student"
                ),
                "Topic": (
                    class_item.get("topic")
                    or "Untitled Essay"
                ),
                "Level": (
                    class_item.get("level")
                    or "Not Set"
                ),
                "Score": (
                    class_item.get("badge_score")
                    if class_item.get("badge_score")
                    is not None
                    else "—"
                ),
                "Status": (
                    "Completed"
                    if class_item.get("ended_at")
                    else "In Progress"
                ),
                "Started": format_dashboard_date(
                    class_item.get("started_at")
                ),
                "Started Raw": safe_datetime(
                    class_item.get("started_at")
                )
            }
        )

    if not activity_rows:
        return pd.DataFrame()

    activity_df = pd.DataFrame(activity_rows)

    activity_df = activity_df.sort_values(
        by="Started Raw",
        ascending=False,
        na_position="last"
    )

    activity_df = activity_df.head(limit)

    return activity_df.drop(
        columns=["Started Raw"],
        errors="ignore"
    )


def render_metric_card(
    title,
    value,
    icon,
    description=""
):
    st.markdown(
        f"""<div class="teacher-metric-card">
<div class="teacher-metric-top">
<div class="teacher-metric-icon">
<span class="material-symbols-rounded">{html.escape(str(icon))}</span>
</div>
</div>
<div class="teacher-metric-value">{html.escape(str(value))}</div>
<div class="teacher-metric-title">{html.escape(str(title))}</div>
<div class="teacher-metric-description">{html.escape(str(description))}</div>
</div>""",
        unsafe_allow_html=True
    )


def render_teacher_dashboard(
    db,
    user_id,
    user_email,
    profile,
    admin_mode=False
):
    """
    Main teacher dashboard.
    """

    teacher_name = (
        profile.get("full_name")
        or user_email
    )

    st.markdown(
        """
        <style>
        .teacher-main-header {
            background:
                radial-gradient(
                    circle at top right,
                    rgba(255,255,255,0.20),
                    transparent 35%
                ),
                linear-gradient(
                    135deg,
                    #312e81,
                    #4f46e5,
                    #9333ea
                );
            border-radius: 26px;
            color: white;
            padding: 34px 38px;
            margin-bottom: 25px;
            box-shadow:
                0 20px 50px rgba(79,70,229,0.20);
        }

        .teacher-main-header h1 {
            margin: 4px 0 8px 0;
            font-size: 36px;
            font-weight: 800;
        }

        .teacher-main-header p {
            margin: 0;
            opacity: 0.90;
            font-size: 16px;
        }

        .teacher-header-label {
            font-size: 12px;
            letter-spacing: 1.5px;
            font-weight: 800;
            opacity: 0.80;
        }

        .teacher-metric-card {
            background: white;
            border: 1px solid #e8eaf3;
            border-radius: 20px;
            padding: 20px;
            min-height: 165px;
            box-shadow:
                0 10px 30px rgba(15,23,42,0.06);
        }

        .teacher-metric-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .teacher-metric-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 42px;
            height: 42px;
            border-radius: 13px;
            background: #eef2ff;
            color: #4f46e5;
        }

        .teacher-metric-value {
            color: #0f172a;
            font-size: 31px;
            line-height: 1.1;
            font-weight: 800;
            margin-top: 17px;
        }

        .teacher-metric-title {
            color: #334155;
            font-size: 14px;
            font-weight: 700;
            margin-top: 5px;
        }

        .teacher-metric-description {
            color: #94a3b8;
            font-size: 12px;
            margin-top: 5px;
        }

        .teacher-section-card {
            background: white;
            border: 1px solid #e8eaf3;
            border-radius: 20px;
            padding: 22px;
            margin-top: 18px;
            box-shadow:
                0 8px 25px rgba(15,23,42,0.04);
        }

        .student-detail-header {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 20px;
            margin: 15px 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # Sidebar
    # -----------------------------------------------------

    with st.sidebar:
        st.title(
            ":material/dashboard: Teacher Portal"
        )

        if admin_mode:
            if st.button(
                ":material/arrow_back: Back to Admin",
                use_container_width=True,
                key="teacher_back_to_admin"
            ):
                st.session_state.admin_view_mode = "admin"
                st.rerun()

            st.divider()

        st.write(
            f":material/person: **Welcome, "
            f"{teacher_name}**"
        )

        st.caption(user_email)

        st.divider()

        teacher_page = st.radio(
            "Teacher Navigation",
            [
                "Overview",
                "Students",
                "Student Details",
                "Recent Activity"
            ],
            label_visibility="collapsed",
            key="teacher_page_navigation"
        )

        st.divider()

        if st.button(
            ":material/refresh: Refresh Data",
            use_container_width=True,
            key="refresh_teacher_data"
        ):
            st.rerun()

        if st.button(
            ":material/logout: Logout",
            use_container_width=True,
            key="teacher_dashboard_logout"
        ):
            st.session_state.clear()
            st.rerun()

    # For the current demo, service client is used so the
    # admin/teacher dashboard can read all student records.
    data_client = supabase_service

    students, classes, submissions = (
        load_teacher_dashboard_data(data_client)
    )

    progress_df = build_student_progress_dataframe(
        students,
        classes,
        submissions
    )

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    st.markdown(
    f"""<div class="teacher-main-header">
<div class="teacher-header-label">
AI INSTRUCTOR PRO
</div>

<h1>Teacher Dashboard</h1>

<p>
Welcome, {html.escape(teacher_name)}.
Monitor student participation, essay completion,
performance and writing activity.
</p>

</div>""",
    unsafe_allow_html=True,
)

    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------

    total_students = len(progress_df)

    active_students = 0

    if (
        not progress_df.empty
        and "Essays Started" in progress_df.columns
    ):
        active_students = int(
            (progress_df["Essays Started"] > 0).sum()
        )

    total_completed = (
        int(progress_df["Essays Completed"].sum())
        if not progress_df.empty
        else 0
    )

    scored_students = (
        progress_df[
            progress_df["Average Score"] > 0
        ]
        if not progress_df.empty
        else pd.DataFrame()
    )

    average_score = (
        round(
            scored_students["Average Score"].mean(),
            1
        )
        if not scored_students.empty
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_metric_card(
            "Total Students",
            total_students,
            "groups",
            "Registered student accounts"
        )

    with c2:
        render_metric_card(
            "Active Students",
            active_students,
            "person_check",
            "Students who started an essay"
        )

    with c3:
        render_metric_card(
            "Essays Completed",
            total_completed,
            "task_alt",
            "Completed essay sessions"
        )

    with c4:
        render_metric_card(
            "Average Score",
            f"{average_score}%",
            "monitoring",
            "Average completed essay score"
        )

    # -----------------------------------------------------
    # Overview Page
    # -----------------------------------------------------

    if teacher_page == "Overview":
        st.markdown("## Class Overview")

        if progress_df.empty:
            st.info(
                "No student accounts were found."
            )

        else:
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.markdown("### Completion by Student")

                completion_chart = (
                    progress_df[
                        [
                            "Student",
                            "Completion Rate"
                        ]
                    ]
                    .set_index("Student")
                    .sort_values(
                        "Completion Rate",
                        ascending=False
                    )
                )

                st.bar_chart(
                    completion_chart,
                    use_container_width=True
                )

            with chart_col2:
                st.markdown("### Average Scores")

                score_chart = (
                    progress_df[
                        [
                            "Student",
                            "Average Score"
                        ]
                    ]
                    .set_index("Student")
                    .sort_values(
                        "Average Score",
                        ascending=False
                    )
                )

                st.bar_chart(
                    score_chart,
                    use_container_width=True
                )

            st.markdown("### Students Requiring Attention")

            attention_df = progress_df[
                progress_df["Risk"].isin(
                    [
                        "High",
                        "Medium",
                        "No Activity"
                    ]
                )
            ]

            if attention_df.empty:
                st.success(
                    "No students are currently flagged."
                )

            else:
                st.dataframe(
                    attention_df[
                        [
                            "Student",
                            "Level",
                            "Essays Started",
                            "Essays Completed",
                            "Average Score",
                            "Late Submissions",
                            "Risk",
                            "Last Active"
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True
                )

    # -----------------------------------------------------
    # Students Page
    # -----------------------------------------------------

    elif teacher_page == "Students":
        st.markdown("## All Students")

        if progress_df.empty:
            st.info("No students found.")

        else:
            filter_col1, filter_col2 = st.columns(2)

            with filter_col1:
                available_levels = sorted(
                    progress_df["Level"]
                    .dropna()
                    .unique()
                    .tolist()
                )

                selected_level = st.selectbox(
                    "Filter by Education Level",
                    ["All"] + available_levels,
                    key="teacher_level_filter"
                )

            with filter_col2:
                selected_status = st.selectbox(
                    "Filter by Status",
                    [
                        "All",
                        "Not Started",
                        "In Progress",
                        "Completed"
                    ],
                    key="teacher_status_filter"
                )

            filtered_df = progress_df.copy()

            if selected_level != "All":
                filtered_df = filtered_df[
                    filtered_df["Level"]
                    == selected_level
                ]

            if selected_status != "All":
                filtered_df = filtered_df[
                    filtered_df["Status"]
                    == selected_status
                ]

            display_columns = [
                "Student",
                "Email",
                "Level",
                "Essays Started",
                "Essays Completed",
                "Completion Rate",
                "Average Score",
                "Paragraphs Submitted",
                "Late Submissions",
                "Risk",
                "Last Active"
            ]

            st.dataframe(
                filtered_df[display_columns],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Completion Rate":
                        st.column_config.ProgressColumn(
                            "Completion",
                            min_value=0,
                            max_value=100,
                            format="%.1f%%"
                        ),
                    "Average Score":
                        st.column_config.NumberColumn(
                            "Average Score",
                            format="%.1f%%"
                        )
                }
            )

            csv_data = filtered_df[
                display_columns
            ].to_csv(index=False)

            st.download_button(
                "Download Student Progress CSV",
                data=csv_data,
                file_name="student_progress.csv",
                mime="text/csv",
                use_container_width=True
            )

    # -----------------------------------------------------
    # Student Details Page
    # -----------------------------------------------------

    elif teacher_page == "Student Details":
        st.markdown("## Individual Student Report")

        if progress_df.empty:
            st.info("No students found.")

        else:
            student_options = (
                progress_df["Student"]
                .dropna()
                .tolist()
            )

            selected_student_name = st.selectbox(
                "Select Student",
                student_options,
                key="teacher_selected_student"
            )

            selected_row = progress_df[
                progress_df["Student"]
                == selected_student_name
            ].iloc[0]

            selected_student_id = selected_row[
                "Student ID"
            ]

            st.markdown(
    f"""<div class="student-detail-header">
<h3 style="margin:0;">
{html.escape(str(selected_row["Student"]))}
</h3>
<div style="margin-top:8px; color:#64748b;">
{html.escape(str(selected_row["Email"]))}
&nbsp; • &nbsp;
{html.escape(str(selected_row["Level"]))}
</div>
</div>""",
    unsafe_allow_html=True
)

            d1, d2, d3, d4 = st.columns(4)

            d1.metric(
                "Essays Started",
                int(selected_row["Essays Started"])
            )

            d2.metric(
                "Essays Completed",
                int(selected_row["Essays Completed"])
            )

            d3.metric(
                "Average Score",
                f"{selected_row['Average Score']}%"
            )

            d4.metric(
                "Total Words",
                int(selected_row["Total Words"])
            )

            selected_classes = [
                item
                for item in classes
                if item.get("user_id")
                == selected_student_id
            ]

            if not selected_classes:
                st.info(
                    "This student has not started an essay."
                )

            else:
                essay_rows = []

                for item in selected_classes:
                    essay_rows.append(
                        {
                            "Topic": (
                                item.get("topic")
                                or "Untitled Essay"
                            ),
                            "Level": (
                                item.get("level")
                                or "Not Set"
                            ),
                            "Score": (
                                item.get("badge_score")
                                if item.get("badge_score")
                                is not None
                                else "—"
                            ),
                            "Badge": (
                                item.get("badge")
                                or "—"
                            ),
                            "Status": (
                                "Completed"
                                if item.get("ended_at")
                                else "In Progress"
                            ),
                            "Started": format_dashboard_date(
                                item.get("started_at")
                            ),
                            "Completed": format_dashboard_date(
                                item.get("ended_at")
                            )
                        }
                    )

                st.markdown("### Essay History")

                st.dataframe(
                    pd.DataFrame(essay_rows),
                    use_container_width=True,
                    hide_index=True
                )

            selected_submissions = [
                item
                for item in submissions
                if item.get("user_id")
                == selected_student_id
            ]

            if selected_submissions:
                st.markdown("### Writing Activity")

                submission_rows = []

                for item in selected_submissions:
                    submission_rows.append(
                        {
                            "Essay Session": (
                                item.get("class_id")
                                or ""
                            ),
                            "Section": (
                                item.get("part")
                                or ""
                            ),
                            "Word Count": (
                                item.get("word_count")
                                or 0
                            ),
                            "Late": (
                                "Yes"
                                if item.get("late")
                                else "No"
                            )
                        }
                    )

                st.dataframe(
                    pd.DataFrame(submission_rows),
                    use_container_width=True,
                    hide_index=True
                )

    # -----------------------------------------------------
    # Recent Activity Page
    # -----------------------------------------------------

    elif teacher_page == "Recent Activity":
        st.markdown("## Recent Student Activity")

        recent_df = get_recent_student_activity(
            students,
            classes,
            limit=20
        )

        if recent_df.empty:
            st.info(
                "No essay activity has been recorded."
            )

        else:
            st.dataframe(
                recent_df,
                use_container_width=True,
                hide_index=True
            )
# ---------------- Main App ----------------

user_id, user_email, access_token = auth_gate()
db = user_client(access_token)

# Fetch complete profile including role
try:
    profile_res = (
        db.table("profiles")
        .select(
            "id, full_name, email, role, "
            "education_level, age"
        )
        .eq("id", user_id)
        .single()
        .execute()
    )

    profile = profile_res.data or {}

except Exception as e:
    st.error(f"Could not load profile: {e}")
    st.stop()


# Read role from Supabase
user_role = (
    profile.get("role")
    or "student"
).strip().lower()


# Save education level for student interface
if "level" not in st.session_state:
    st.session_state.level = (
        profile.get("education_level")
        or "Secondary"
    )


# ---------------- Admin Routing ----------------

if user_role == "admin":

    if "admin_view_mode" not in st.session_state:
        st.session_state.admin_view_mode = "admin"

    # Show admin selection screen
    if st.session_state.admin_view_mode == "admin":
        admin_dashboard(
            user_email=user_email,
            profile=profile
        )
        st.stop()

    # Teacher interface will be added next
    elif st.session_state.admin_view_mode == "teacher":
        render_teacher_dashboard(
            db=db,
            user_id=user_id,
            user_email=user_email,
            profile=profile,
            admin_mode=True
        )
    
        st.stop()

    # Student mode continues into existing student app below
    elif st.session_state.admin_view_mode == "student":
        pass


# Teacher routing temporarily
elif user_role == "teacher":
    render_teacher_dashboard(
        db=db,
        user_id=user_id,
        user_email=user_email,
        profile=profile,
        admin_mode=False
    )

    st.stop()


# Student role continues into existing student interface below


# Sidebar
with st.sidebar:
    st.title(":material/settings: Class Settings")

    # Only visible when admin opened student mode
    if user_role == "admin":
        if st.button(
            ":material/arrow_back: Back to Admin",
            use_container_width=True,
            key="student_back_to_admin"
        ):
            st.session_state.admin_view_mode = "admin"
            st.rerun()

        st.divider()

    st.write(
        f":material/person: **Welcome, {user_email}**"
    )
    

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
    #st.markdown("### 🐞 Debug Info")
    #st.write("Raw:", st.session_state.get("debug_raw_highlight", "none"))
    #st.write("Parsed:", st.session_state.get("debug_parsed_mistakes", {}))
    #st.write("Parse status:", st.session_state.get("debug_json_error", "none"))
    #st.write("HF full response:", st.session_state.get("debug_hf_full_response", {}))
    
    #st.write("Finish reason:", st.session_state.get("debug_finish_reason", "none"))
    #st.write("Message:", st.session_state.get("debug_message", {}))
    #if st.session_state.debug_last:
        #st.json(st.session_state.debug_last)
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

            # NEW
            "attempt_counts": {},              # track attempts per section
            "latest_feedback_hint": {},        # hint text for current section
            "section_passed": {},              # whether current section is correct
            "needs_retry": False,              # whether to keep same section open
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
        st.session_state.done_celebrated = False
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
    retry_hint = st.session_state.latest_feedback_hint.get(current_part, "")
    floating_timer(
        format_mmss(remaining),
        current_part,
        st.session_state.timer_started,
        retry_hint=retry_hint
    )

    # Layout (right column not needed anymore, but kept for spacing if you want)
    main_col, side_col = st.columns([3.2, 1.1], gap="large")

    with main_col:
        # ✅ CHANGE 2: Step-by-step teaching logic (teach current part only once)
        current_step_key = f"taught_{current_part}"
        if current_step_key not in st.session_state:
            with st.spinner(f"Teaching you how to write the {current_part}..."):
                if st.session_state.strictness == 0:
                    sentence_rule = "You may write the full paragraph for them if needed, with as many sentences as needed."
                elif st.session_state.strictness == 1:
                    sentence_rule = "Under the heading of Example Sentences, Write around 8-10 example sentences before ending."
                elif st.session_state.strictness == 2:
                    sentence_rule = "Under the heading of Example Sentences, Write at most 5-6 example sentences before ending."
                else:
                    sentence_rule = "Under the heading of Example Sentences, Write at most 2-4 example sentences before ending."
                teaching_prompt = (
                    f"You are an expert English Tutor for school students. "
                    f"The student is writing an essay on '{st.session_state.topic}'. "
                    f"If the {current_part} is Introduction then only explain them in a separate paragraph the main idea or focus of the essay. "
                    f"If the {current_part} is Introduction then only Give 3-5 specific points or themes they can mention for this topic under the heading Themes. "
                    f"They are now writing the {current_part} for a {st.session_state.level} level essay. "
                    f"Explain briefly what a good {current_part} should include in simple school {st.session_state.level} language. "
                    f"Do NOT use the term 'thesis statement'. Instead, say that the last sentence of the introduction "
                    f"Be like a teacher and tell what each {current_part} should contain according to {st.session_state.level} "
                    f"{sentence_rule} "
                    f"Keep the guidance clear, student-friendly, and simple english "
                    f"End by saying exactly: 'Now, please write your {current_part}'"
                )
                lesson = ollama_chat(
                [{ "role": "user", "content": teaching_prompt }],
                temperature=0.3,
                max_tokens=160
                )
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
            # Student can use only these two languages
            # 1. Language selection
            active_lang = st.radio(
                "Choose your writing / speaking language",
                ["Bahasa Melayu", "English"],
                horizontal=True,
                key=f"active_lang_{st.session_state.part_i}"
            )
            
            # 2. Two text areas
            lang_col1, lang_col2 = st.columns(2)
            
            with lang_col1:
                malay_text = st.text_area(
                    f"Bahasa Melayu | Target: {min_w}-{max_w} words",
                    height=220,
                    key=f"malay_input_{st.session_state.part_i}",
                    placeholder="Taip atau gunakan mikrofon untuk Bahasa Melayu..."
                )
            
            with lang_col2:
                english_text = st.text_area(
                    f"English | Target: {min_w}-{max_w} words",
                    height=220,
                    key=f"english_input_{st.session_state.part_i}",
                    placeholder="Type or use the microphone for English..."
                )
            
            # 3. MICROPHONE COMPONENT YAHAN PASTE KARNA HAI
            speech_language_code = (
                "ms-MY"
                if active_lang == "Bahasa Melayu"
                else "en-US"
            )
            
            speech_target_placeholder = (
                "Taip atau gunakan mikrofon untuk Bahasa Melayu..."
                if active_lang == "Bahasa Melayu"
                else "Type or use the microphone for English..."
            )
            
            components.html(
                f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
            body {{
                margin: 0;
                background: transparent;
                font-family: Arial, sans-serif;
            }}
            
            .voice-row {{
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .mic-btn {{
                border: none;
                border-radius: 12px;
                padding: 11px 18px;
                background: #6366f1;
                color: white;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
            }}
            
            .mic-btn.listening {{
                background: #dc2626;
            }}
            
            .stop-btn {{
                display: none;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 11px 18px;
                background: white;
                color: #334155;
                cursor: pointer;
            }}
            
            .status {{
                color: #64748b;
                font-size: 14px;
            }}
            </style>
            </head>
            
            <body>
            <div class="voice-row">
                <button id="micBtn" class="mic-btn">
                    🎤 Start Speaking
                </button>
            
                <button id="stopBtn" class="stop-btn">
                    ⏹ Stop
                </button>
            
                <span id="status" class="status">
                    Speak in {active_lang}
                </span>
            </div>
            
            <script>
            (function() {{
                const SpeechRecognition =
                    window.SpeechRecognition ||
                    window.webkitSpeechRecognition;
            
                const micBtn =
                    document.getElementById("micBtn");
            
                const stopBtn =
                    document.getElementById("stopBtn");
            
                const status =
                    document.getElementById("status");
            
                if (!SpeechRecognition) {{
                    micBtn.disabled = true;
                    status.innerText =
                        "Use Chrome or Edge for microphone input.";
                    return;
                }}
            
                const recognition =
                    new SpeechRecognition();
            
                recognition.lang =
                    "{speech_language_code}";
            
                recognition.continuous = true;
                recognition.interimResults = false;
            
                function findTargetTextarea() {{
                    const parentDoc = window.parent.document;

                    const malayBox = parentDoc.querySelector(
                        'textarea[placeholder="Taip atau gunakan mikrofon untuk Bahasa Melayu..."]'
                    );

                    const englishBox = parentDoc.querySelector(
                        'textarea[placeholder="Type or use the microphone for English..."]'
                    );

                    // Dynamically check which radio button is checked in the main window
                    const selectedRadio = parentDoc.querySelector('input[name*="active_lang"]:checked');
                    const selectedValue = selectedRadio ? selectedRadio.value : "";

                    if (selectedLanguage === "English") {{
                        return englishBox;
                    }}

                    return malayBox;
                }}
                
               
                
                
            
                function setTextareaValue(
                    textarea,
                    newText
                ) {{
                    const setter =
                        Object.getOwnPropertyDescriptor(
                            window.parent.HTMLTextAreaElement.prototype,
                            "value"
                        ).set;
            
                    setter.call(
                        textarea,
                        newText
                    );
            
                    textarea.dispatchEvent(
                        new Event(
                            "input",
                            {{ bubbles: true }}
                        )
                    );
            
                    textarea.dispatchEvent(
                        new Event(
                            "change",
                            {{ bubbles: true }}
                        )
                    );
                }}
            
                micBtn.onclick = function() {{
                    try {{
                        recognition.start();
            
                        micBtn.classList.add(
                            "listening"
                        );
            
                        micBtn.innerText =
                            "🔴 Listening...";
            
                        stopBtn.style.display =
                            "inline-block";
            
                        status.innerText =
                            "Speak in {active_lang}";
                    }}
                    catch (error) {{
                        status.innerText =
                            "Microphone is already active.";
                    }}
                }};
            
                stopBtn.onclick = function() {{
                    recognition.stop();
                }};
            
                recognition.onresult = function(event) {{
                    let spokenText = "";
            
                    for (
                        let i = event.resultIndex;
                        i < event.results.length;
                        i++
                    ) {{
                        if (event.results[i].isFinal) {{
                            spokenText +=
                                event.results[i][0]
                                .transcript + " ";
                        }}
                    }}
            
                    const textarea =
                        findTargetTextarea();
            
                    if (!textarea) {{
                        status.innerText =
                            "Writing box not found.";
                        return;
                    }}
            
                    const oldText =
                        textarea.value.trim();
            
                    const newText =
                        oldText
                            ? oldText + " " +
                              spokenText.trim()
                            : spokenText.trim();
            
                    setTextareaValue(
                        textarea,
                        newText
                    );
            
                    status.innerText =
                        "Speech added to the selected box.";
                }};
            
                recognition.onerror = function(event) {{
                    status.innerText =
                        "Microphone error: " +
                        event.error;
                }};
            
                recognition.onend = function() {{
                    micBtn.classList.remove(
                        "listening"
                    );
            
                    micBtn.innerText =
                        "🎤 Start Speaking";
            
                    stopBtn.style.display =
                        "none";
                }};
            }})();
            </script>
            </body>
            </html>
                """,
                height=65
            )
            
            # 4. Translation and selected student text logic
            if active_lang == "Bahasa Melayu":
                student_text = malay_text
            
                english_translation = (
                    translate_malay_to_english(malay_text)
                    if malay_text.strip()
                    else ""
                )
            
                st.caption("English translation:")
                st.info(
                    english_translation
                    if english_translation
                    else "English translation will appear here."
                )
            
            else:
                student_text = english_text
            
                malay_translation = (
                    translate_english_to_malay(english_text)
                    if english_text.strip()
                    else ""
                )
            
                st.caption("Bahasa Melayu translation:")
                st.info(
                    malay_translation
                    if malay_translation
                    else "Bahasa Melayu translation will appear here."
                )
            
            # 5. Submit button
            submitted = st.form_submit_button(
                "Submit Paragraph"
            )
            
           
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
                # Send the ORIGINAL typed text to AI checker
                text_for_checking = student_text
        
                # Store active language safely before rerun
                st.session_state.pending_lang = active_lang
        
                # Stop timer + store submission safely
                st.session_state.timer_started = False
                st.session_state.pending_text = text_for_checking
                st.session_state.is_processing = True
                st.rerun()

                # ---------------- PHASE B: heavy processing runs AFTER rerun, with autorefresh OFF ----------------
        if st.session_state.is_processing and st.session_state.pending_text is not None:
            student_text = st.session_state.pending_text
            late = remaining <= 0

            with st.status("Tutor is reviewing your work...", expanded=True) as status:
                st.write("🔍 Scanning for mistakes...")
                st.write("TEXT SENT TO AI:", student_text)
                analysis = scan_tokens_with_hf(
                    student_text,
                    st.session_state.get("pending_lang", "English")
                )
                marked_text = analysis["marked_text"]
                corrected = analysis["corrected_text"]

                st.write("STUDENT TEXT:", student_text)
                st.write("TOKEN ANALYSIS:", analysis)

                st.session_state.debug_last = {
                    "raw_response": st.session_state.get("debug_raw_highlight", "not available"),
                    "parsed_mistakes": st.session_state.get("debug_parsed_mistakes", {}),
                    "json_error": st.session_state.get("debug_json_error", "none"),
                    "hf_full_response": st.session_state.get("debug_hf_full_response", {}),
                }

                

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
            # Track attempts
            st.session_state.attempt_counts[current_part] = st.session_state.attempt_counts.get(current_part, 0) + 1
            
            # Always keep the student's submitted attempt in chat
            st.session_state.chat.append({"role": "user", "content": student_text})
            
            # Always show highlighted mistakes
            st.session_state.chat.append(
                {
                    "role": "ai_html",
                    "content": render_marked_highlighted_block(marked_text)
                }
            )
            
            if analysis.get("has_errors", False):
                # Build retry hint from mistakes only
                retry_hint = build_retry_hint_from_marked(marked_text, current_part)
                st.session_state.latest_feedback_hint[current_part] = retry_hint
                st.session_state.section_passed[current_part] = False
                st.session_state.needs_retry = True
            
                # Teacher asks to rewrite same section again
                st.session_state.chat.append(
                    {
                        "role": "ai",
                        "content": (
                            f"Please rewrite your **{current_part}** again. "
                            f"Correct the highlighted spelling and grammar mistakes. "
                            f"Use the hint box below the timer."
                        )
                    }
                )
            
                # IMPORTANT: do not move to next section
                st.session_state.part_start_time = None
                st.session_state.timer_started = False
            
            else:
                # Section passed
                st.session_state.latest_feedback_hint[current_part] = ""
                st.session_state.section_passed[current_part] = True
                st.session_state.needs_retry = False
            
                # Now only show refined version
                st.session_state.corrected_parts[current_part] = corrected
                st.session_state.chat.append(
                    {"role": "ai", "content": f"**Refined Version:**\n\n{corrected}"}
                )
            
                # Advance section only now
                old_i = st.session_state.part_i

                st.session_state.corrected_parts[current_part] = corrected
                st.session_state.chat.append(
                    {"role": "ai", "content": f"**Refined Version:**\n\n{corrected}"}
                )
                
                st.session_state.pop(f"malay_input_{old_i}", None)
                st.session_state.pop(f"english_input_{old_i}", None)
                st.session_state.pop(f"input_{old_i}", None)
                st.session_state.pop(f"translated_{old_i}", None)
                st.session_state.pop(f"active_lang_{old_i}", None)
                
                st.session_state.part_i += 1
                st.session_state.part_start_time = None
                st.session_state.timer_started = False
            
                if st.session_state.part_i >= len(PARTS):
                    st.session_state.step = "DONE"

            # Clear locks BEFORE rerun
            st.session_state.pending_text = None
            st.session_state.is_processing = False

            st.rerun()


# ---------------- STEP 3: Done ----------------
elif st.session_state.step == "DONE":
    if not st.session_state.done_celebrated:
        st.balloons()
        st.session_state.done_celebrated = True

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
            low = re.sub(r"(?im)^\s*here\s+is\s+the\s+corrected.*?:\s*$", "", low)
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
            # keep login session + profile settings
            keep_keys = {
                "sb_session": st.session_state.get("sb_session"),
                "level": st.session_state.get("level"),
                "strictness": st.session_state.get("strictness", 2),
            }
        
            st.session_state.clear()
        
            for k, v in keep_keys.items():
                st.session_state[k] = v
        
            st.rerun()

    with c2:
        if st.button("Logout", use_container_width=True):
            try:
                supabase_admin.auth.sign_out()
            except Exception:
                pass
            st.session_state.clear()
            st.rerun()
