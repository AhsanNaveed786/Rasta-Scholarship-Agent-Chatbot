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
# Language selection
# ---------------------------
lang_choice = st.radio("Language / زبان", ["English", "اردو"], horizontal=True)

t = {
    "English": {
        "chat_input": "Describe your situation...",
        "spinner_chat": "Thinking...",
        "spinner_scheme": "Finding schemes...",
        "matched_schemes": "Matched Schemes",
        "no_match": "No matching schemes found.",
        "err_no_data": "No schemes data found.",
        "initial_greeting": "Hello! Tell me about your situation."
    },
    "اردو": {
        "chat_input": "اپنی صورتحال بتائیں...",
        "spinner_chat": "سوچ رہا ہے...",
        "spinner_scheme": "سکیمیں تلاش کر رہا ہے...",
        "matched_schemes": "مماثل سکیمیں",
        "no_match": "کوئی سکیم نہیں ملی",
        "err_no_data": "کوئی ڈیٹا موجود نہیں",
        "initial_greeting": "ہیلو! اپنی صورتحال بتائیں۔"
    }
}

lang_param = "Urdu" if lang_choice == "اردو" else "English"


# ---------------------------
# Session init
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": t[lang_choice]["initial_greeting"]}
    ]


# ---------------------------
# Show chat history
# ---------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ---------------------------
# Input box
# ---------------------------
user_input = st.chat_input(t[lang_choice]["chat_input"])

if user_input:
    # user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # ---------------------------
    # AI DECISION STEP (FIXED)
    # ---------------------------
    with st.spinner(t[lang_choice]["spinner_chat"]):
        decision = decide_next_step(
            st.session_state.messages,
            api_key,
            language=lang_param
        )

    # ---------------------------
    # ASK MODE
    # ---------------------------
    if decision.get("action") == "ask":
        question = decision.get("question", "Could you provide more details?")
        st.session_state.messages.append({"role": "assistant", "content": question})

        with st.chat_message("assistant"):
            st.markdown(question)

    # ---------------------------
    # RECOMMEND MODE
    # ---------------------------
    elif decision.get("action") == "recommend":
        summary = decision.get("summary", "")

        summary_msg = f"Got it! Finding best schemes...\n\n{summary}"
        st.session_state.messages.append({"role": "assistant", "content": summary_msg})

        with st.chat_message("assistant"):
            st.markdown(summary_msg)

        # Load schemes
        schemes = load_schemes()

        if not schemes:
            st.error(t[lang_choice]["err_no_data"])
        else:
            with st.spinner(t[lang_choice]["spinner_scheme"]):

                # ---------------------------
                # MATCH SCHEMES (FIXED)
                # ---------------------------
                matches = match_schemes(
                    summary,
                    schemes,
                    api_key,
                    language=lang_param
                )

                if matches:
                    st.subheader(t[lang_choice]["matched_schemes"])

                    cols = st.columns(min(len(matches), 3))

                    for i, match in enumerate(matches):
                        with cols[i % 3]:
                            st.markdown(f"""
                            ### {match.get('scheme_name')}

                            **Why Eligible:**  
                            {match.get('why_eligible')}

                            **Documents Needed:**  
                            {match.get('documents_needed')}

                            **How to Apply:**  
                            {match.get('how_to_apply')}

                            **Official Source:**  
                            {match.get('official_source', '')}
                            """)

                    # ---------------------------
                    # LATEST INFO (FIXED)
                    # ---------------------------
                    top_scheme = matches[0].get("scheme_name")

                    st.markdown("### Latest Info")
                    latest_info = get_latest_info(
                        top_scheme,
                        api_key,
                        language=lang_param
                    )

                    st.info(latest_info)

                else:
                    st.info(t[lang_choice]["no_match"])
