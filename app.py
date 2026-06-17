import streamlit as st
import json
import os
from main import match_schemes, get_latest_info, decide_next_step

# ---------------------------
# API KEY (Streamlit Cloud)
# ---------------------------
api_key = st.secrets["OPENAI_API_KEY"]

# ---------------------------
# Load schemes.json
# ---------------------------
def load_schemes():
    schemes_path = os.path.join(os.path.dirname(__file__), 'schemes.json')
    try:
        with open(schemes_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading schemes: {e}")
        return []

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="RASTA Agent", page_icon="🇵🇰", layout="wide")

# ---------------------------
# Language toggle
# ---------------------------
lang_choice = st.radio("Language / زبان", ["English", "اردو"], horizontal=True)

UI = {
    "English": {
        "title": "RASTA Agent 🇵🇰",
        "description": "**Your personal assistant to find matching Pakistani welfare schemes.**",
        "teach_mode": "Teach mode",
        "examples_label": "Examples:",
        "ex_1": "Income kam hai",
        "ex_2": "Main student hoon",
        "ex_3": "Karobar shuru karna hai",
        "start_over": "Start over",
        "chat_input": "Describe your situation...",
        "err_no_data": "No schemes data found.",
        "spinner_chat": "Thinking...",
        "spinner_scheme": "Finding the best schemes for you...",
        "matched_schemes": "Matched Schemes",
        "why_eligible": "Why Eligible:",
        "docs_needed": "Documents Needed:",
        "how_to_apply": "How to Apply:",
        "official_source": "Official Source:",
        "latest_info": "Latest Info on {scheme} (From the Web)",
        "no_match": "No matching schemes found for your situation.",
        "teach_debug": "Teach Mode Debug Info",
        "err_occurred": "An error occurred: ",
        "initial_greeting": "Hello! I can help you find government schemes. Tell me your situation."
    },
    "اردو": {
        "title": "راستہ ایجنٹ 🇵🇰",
        "description": "**پاکستانی فلاحی سکیموں کو تلاش کرنے کے لیے آپ کا ذاتی معاون۔**",
        "teach_mode": "سکھانے کا موڈ",
        "examples_label": "مثالیں:",
        "ex_1": "میری آمدنی کم ہے",
        "ex_2": "میں طالب علم ہوں",
        "ex_3": "کاروبار شروع کرنا ہے",
        "start_over": "دوبارہ شروع کریں",
        "chat_input": "اپنی صورتحال بتائیں...",
        "err_no_data": "کوئی ڈیٹا موجود نہیں",
        "spinner_chat": "سوچ رہا ہے...",
        "spinner_scheme": "سکیمیں تلاش کر رہا ہے...",
        "matched_schemes": "مماثل سکیمیں",
        "why_eligible": "اہلیت:",
        "docs_needed": "دستاویزات:",
        "how_to_apply": "درخواست کا طریقہ:",
        "official_source": "سرکاری ذریعہ:",
        "latest_info": "{scheme} پر تازہ معلومات",
        "no_match": "کوئی سکیم نہیں ملی",
        "teach_debug": "سکھانے کا موڈ ڈیٹا",
        "err_occurred": "خرابی: ",
        "initial_greeting": "ہیلو! اپنی صورتحال بتائیں۔"
    }
}

t = UI[lang_choice]
lang_param = "Urdu" if lang_choice == "اردو" else "English"

# ---------------------------
# RTL SUPPORT
# ---------------------------
if lang_choice == "اردو":
    st.markdown("""
        <style>
        .rtl-text {
            direction: rtl;
            text-align: right;
        }
        </style>
    """, unsafe_allow_html=True)

    def render(text):
        return f"<div class='rtl-text'>{text}</div>"
else:
    def render(text):
        return text

# ---------------------------
# TITLE
# ---------------------------
st.title(t["title"])
st.write(t["description"])

# ---------------------------
# CONTROLS
# ---------------------------
col1, col2 = st.columns(2)

with col1:
    teach_mode = st.checkbox(t["teach_mode"])

with col2:
    if st.button(t["start_over"]):
        st.session_state.messages = [
            {"role": "assistant", "content": t["initial_greeting"]}
        ]
        st.rerun()

# ---------------------------
# EXAMPLES
# ---------------------------
st.write(t["examples_label"])
c1, c2, c3, _ = st.columns([1,1,1,2])

if c1.button(t["ex_1"]):
    st.session_state.preset = t["ex_1"]
if c2.button(t["ex_2"]):
    st.session_state.preset = t["ex_2"]
if c3.button(t["ex_3"]):
    st.session_state.preset = t["ex_3"]

# ---------------------------
# SESSION INIT
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": t["initial_greeting"]}
    ]

# ---------------------------
# CHAT DISPLAY
# ---------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(render(msg["content"]))

# ---------------------------
# INPUT
# ---------------------------
user_input = st.chat_input(t["chat_input"])

if "preset" in st.session_state:
    user_input = st.session_state.preset
    del st.session_state.preset

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # ---------------------------
    # DECISION STEP (FIXED)
    # ---------------------------
    with st.spinner(t["spinner_chat"]):
        decision = decide_next_step(
            st.session_state.messages,
            api_key,
            language=lang_param
        )

    # ---------------------------
    # ASK MODE
    # ---------------------------
    if decision.get("action") == "ask":
        question = decision.get("question")

        st.session_state.messages.append({"role": "assistant", "content": question})

        with st.chat_message("assistant"):
            st.markdown(render(question))

    # ---------------------------
    # RECOMMEND MODE
    # ---------------------------
    elif decision.get("action") == "recommend":
        summary = decision.get("summary", "")

        msg = f"Got it! Finding schemes...\n\n{summary}"

        st.session_state.messages.append({"role": "assistant", "content": msg})

        with st.chat_message("assistant"):
            st.markdown(render(msg))

        schemes = load_schemes()

        if not schemes:
            st.error(t["err_no_data"])
        else:
            with st.spinner(t["spinner_scheme"]):

                matches = match_schemes(
                    summary,
                    schemes,
                    api_key,
                    language=lang_param
                )

                if matches:
                    st.subheader(t["matched_schemes"])

                    cols = st.columns(min(len(matches), 3))

                    for i, m in enumerate(matches):
                        with cols[i % 3]:
                            st.markdown(f"""
                            ### {m.get('scheme_name')}

                            **{t['why_eligible']}** {m.get('why_eligible')}  

                            **{t['docs_needed']}** {m.get('documents_needed')}  

                            **{t['how_to_apply']}** {m.get('how_to_apply')}  

                            **{t['official_source']}** {m.get('official_source')}
                            """)

                    top_scheme = matches[0]["scheme_name"]

                    st.subheader(t["latest_info"].format(scheme=top_scheme))

                    latest_info = get_latest_info(
                        top_scheme,
                        api_key,
                        language=lang_param
                    )

                    st.info(latest_info)

                else:
                    st.info(t["no_match"])
