import streamlit as st
import json
import os
from main import match_schemes, get_latest_info, decide_next_step

api_key = st.secrets["OPENAI_API_KEY"]

def load_schemes():
    schemes_path = os.path.join(os.path.dirname(__file__), 'schemes.json')
    try:
        with open(schemes_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading schemes: {e}")
        return []

st.set_page_config(page_title="RASTA Agent", page_icon="🇵🇰", layout="wide")

# Language toggle
lang_choice = st.radio("Language / زبان", ["English", "اردو"], horizontal=True, key="lang_choice")

# UI strings dictionary
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
        "initial_greeting": "Hello! I can help you find government schemes. To get started, please tell me a little bit about your situation (e.g. your income, location, or if you are a student)."
    },
    "اردو": {
        "title": "راستہ ایجنٹ 🇵🇰",
        "description": "**پاکستانی فلاحی سکیموں کو تلاش کرنے کے لیے آپ کا ذاتی معاون۔**",
        "teach_mode": "سکھانے کا موڈ (Teach mode)",
        "examples_label": "مثالیں:",
        "ex_1": "میری آمدنی کم ہے",
        "ex_2": "میں طالب علم ہوں",
        "ex_3": "کاروبار شروع کرنا ہے",
        "start_over": "دوبارہ شروع کریں (Start over)",
        "chat_input": "اپنی پریشانی یا ضرورت بتائیں...",
        "err_no_data": "سکیموں کا کوئی ڈیٹا نہیں ملا۔",
        "spinner_chat": "سوچ رہا ہے...",
        "spinner_scheme": "آپ کے لیے بہترین سکیمیں تلاش کی جا رہی ہیں...",
        "matched_schemes": "مماثل سکیمیں (Matched Schemes)",
        "why_eligible": "اہل کیوں ہیں:",
        "docs_needed": "مطلوبہ دستاویزات:",
        "how_to_apply": "اپلائی کرنے کا طریقہ:",
        "official_source": "سرکاری ذریعہ:",
        "latest_info": "{scheme} پر تازہ ترین معلومات (ویب سے)",
        "no_match": "آپ کی صورتحال کے لیے کوئی مماثل سکیم نہیں ملی۔",
        "teach_debug": "سکھانے کے موڈ کی معلومات (Debug Info)",
        "err_occurred": "ایک خرابی پیش آ گئی: ",
        "initial_greeting": "ہیلو! میں آپ کو سرکاری سکیمیں تلاش کرنے میں مدد کر سکتا ہوں۔ شروع کرنے کے لیے، براہ کرم مجھے اپنی صورتحال کے بارے میں تھوڑا سا بتائیں (جیسے آپ کی آمدنی، مقام، یا اگر آپ طالب علم ہیں)۔"
    }
}

t = UI[lang_choice]
lang_param = "Urdu" if lang_choice == "اردو" else "English"

# Render right-to-left if Urdu
if lang_choice == "اردو":
    st.markdown(
        """
        <style>
        .rtl-text {
            direction: rtl;
            text-align: right;
            font-family: 'Jameel Noori Nastaleeq', 'Nafees Web Naskh', Arial, sans-serif;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    def render_rtl(text, tag="div"):
        return f'<{tag} class="rtl-text">{text}</{tag}>'
else:
    def render_rtl(text, tag="div"):
        return text

# Main UI setup
if lang_choice == "اردو":
    st.markdown(render_rtl(f'<h1>{t["title"]}</h1>'), unsafe_allow_html=True)
    st.markdown(render_rtl(t["description"]), unsafe_allow_html=True)
else:
    st.title(t["title"])
    st.write(t["description"])

col_teach, col_reset = st.columns([1, 1])
with col_teach:
    teach_mode = st.checkbox(t["teach_mode"])
with col_reset:
    if st.button(t["start_over"]):
        if "messages" in st.session_state:
            del st.session_state.messages
        st.rerun()

if lang_choice == "اردو":
    st.markdown(render_rtl(t["examples_label"]), unsafe_allow_html=True)
else:
    st.write(t["examples_label"])

col1, col2, col3, _ = st.columns([1, 1, 1, 2])
if col1.button(t["ex_1"]):
    st.session_state.pill_input = t["ex_1"]
if col2.button(t["ex_2"]):
    st.session_state.pill_input = t["ex_2"]
if col3.button(t["ex_3"]):
    st.session_state.pill_input = t["ex_3"]

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": t["initial_greeting"]}
    ]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if lang_choice == "اردو":
            st.markdown(render_rtl(message["content"]), unsafe_allow_html=True)
        else:
            st.markdown(message["content"])

        # If it's a recommendation message, maybe we should not have saved the complex markdown
        # We will handle scheme rendering separately or save it as a special role
        
user_input = st.chat_input(t["chat_input"])

# Handle pill input
if "pill_input" in st.session_state and st.session_state.pill_input:
    user_input = st.session_state.pill_input
    st.session_state.pill_input = ""

if user_input:
    # Append user message to state and display
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        if lang_choice == "اردو":
            st.markdown(render_rtl(user_input), unsafe_allow_html=True)
        else:
            st.markdown(user_input)
            
    with st.spinner(t["spinner_chat"]):
        decision = decide_next_step(st.session_state.messages, language=lang_param)
        
    if decision.get("action") == "ask":
        question = decision.get("question", "Could you provide more details?")
        st.session_state.messages.append({"role": "assistant", "content": question})
        with st.chat_message("assistant"):
            if lang_choice == "اردو":
                st.markdown(render_rtl(question), unsafe_allow_html=True)
            else:
                st.markdown(question)
                
    elif decision.get("action") == "recommend":
        summary = decision.get("summary", "")
        summary_msg = f"Got it! Let me find the best schemes for you. Situation: {summary}"
        st.session_state.messages.append({"role": "assistant", "content": summary_msg})
        with st.chat_message("assistant"):
            if lang_choice == "اردو":
                st.markdown(render_rtl(summary_msg), unsafe_allow_html=True)
            else:
                st.markdown(summary_msg)
                
        schemes = load_schemes()
        if not schemes:
            st.error(t["err_no_data"])
        else:
            with st.spinner(t["spinner_scheme"]):
                try:
                    if teach_mode:
                        matches, match_debug = match_schemes(summary, schemes, debug=True, language=lang_param)
                    else:
                        matches = match_schemes(summary, schemes, language=lang_param)
                        
                    if matches:
                        if lang_choice == "اردو":
                            st.markdown(render_rtl(f'<h2>{t["matched_schemes"]}</h2>'), unsafe_allow_html=True)
                        else:
                            st.subheader(t["matched_schemes"])
                        
                        cols = st.columns(len(matches) if len(matches) < 3 else 3)
                        for idx, match in enumerate(matches):
                            col_idx = idx % 3
                            with cols[col_idx]:
                                official_source = match.get('official_source', '')
                                source_html = f'<p><strong>{t["official_source"]}</strong> <a href="{official_source}" target="_blank">{official_source}</a></p>' if official_source else ''
                                
                                rtl_class = ' class="rtl-text"' if lang_choice == "اردو" else ''
                                
                                st.markdown(f"""
                                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; border-left: 5px solid #0078D7; height: 100%; margin-bottom: 10px;"{rtl_class}>
                                    <h4 style="color: #0078D7; margin-top: 0;">{match.get('scheme_name')}</h4>
                                    <p><strong>{t["why_eligible"]}</strong> {match.get('why_eligible')}</p>
                                    <p><strong>{t["docs_needed"]}</strong> {match.get('documents_needed')}</p>
                                    <p><strong>{t["how_to_apply"]}</strong> {match.get('how_to_apply')}</p>
                                    {source_html}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        st.write("---")
                        top_scheme = matches[0].get('scheme_name')
                        latest_info_heading = t["latest_info"].format(scheme=top_scheme)
                        
                        if lang_choice == "اردو":
                            st.markdown(render_rtl(f'<h2>{latest_info_heading}</h2>'), unsafe_allow_html=True)
                        else:
                            st.subheader(latest_info_heading)

                        if teach_mode:
                            latest_info, info_debug = get_latest_info(top_scheme, debug=True, language=lang_param)
                        else:
                            latest_info = get_latest_info(top_scheme, language=lang_param)
                        
                        if lang_choice == "اردو":
                            st.markdown(render_rtl(f'<div style="background-color: #e8f4f8; padding: 15px; border-radius: 5px; color: #00529b;">{latest_info}</div>'), unsafe_allow_html=True)
                        else:
                            st.info(latest_info)
                        
                        if teach_mode:
                            st.write("---")
                            if lang_choice == "اردو":
                                st.markdown(render_rtl(f'<h3>{t["teach_debug"]}</h3>'), unsafe_allow_html=True)
                            else:
                                st.subheader(t["teach_debug"])
                            with st.expander("System prompt sent"):
                                st.text(match_debug["system_prompt"])
                            with st.expander("Raw JSON before parsing"):
                                st.text(match_debug["raw_json"])
                            with st.expander("Web search request"):
                                st.write(f"**Scheme Name:** {info_debug['scheme_name']}")
                                st.write(f"**Query:** {info_debug['query']}")
                    else:
                        st.info(t["no_match"])
                except Exception as e:
                    st.error(f"{t['err_occurred']}{e}")
