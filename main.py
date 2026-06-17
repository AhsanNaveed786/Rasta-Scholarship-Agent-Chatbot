import json
import os
from openai import OpenAI


# ---------------------------
# OpenAI Client Helper
# ---------------------------
def get_client(api_key):
    return OpenAI(api_key=api_key)


# ---------------------------
# Decide Next Step (Agent Brain)
# ---------------------------
def decide_next_step(history, api_key, language="English"):
    client = get_client(api_key)

    system_prompt = f"""
You are a helpful AI assistant tasked with finding Pakistani welfare schemes for users.

Before making recommendations, you MUST gather exactly three facts:
1. Approximate income level
2. Location (Province or City in Pakistan)
3. Student status (whether they are a student or not)

If ANY fact is missing, ask ONE short follow-up question in {language}.
If all facts are known, summarize the user's situation in one line.

Respond ONLY in JSON:
If asking:
{{"action": "ask", "question": "<question>"}}

If ready:
{{"action": "recommend", "summary": "<summary>"}}
"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        return {"action": "ask", "question": f"Error: {e}"}


# ---------------------------
# Match Schemes Tool
# ---------------------------
def match_schemes(user_message, schemes=None, api_key=None, debug=False, language="English"):
    client = get_client(api_key)

    query = f"""
Find real Pakistani government welfare schemes for this user:
{user_message}
"""

    system_prompt = f"""
You are an AI assistant finding real Pakistani government schemes.

Rules:
- Respond in {language}
- Do NOT invent schemes
- Return max 4 schemes
- Each must have:
  scheme_name, why_eligible, documents_needed, how_to_apply, official_source
- Return ONLY JSON array
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-search-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )

        text = response.choices[0].message.content.strip()

        # clean markdown if any
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        result = json.loads(text)

        return result

    except Exception as e:
        return [{
            "scheme_name": "Error",
            "why_eligible": str(e),
            "documents_needed": "",
            "how_to_apply": "",
            "official_source": ""
        }]


# ---------------------------
# Latest Info Tool
# ---------------------------
def get_latest_info(scheme_name, api_key=None, debug=False, language="English"):
    client = get_client(api_key)

    query = f"""
Get latest official updates about {scheme_name}.
Respond in {language}, 3-4 lines only.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-search-preview",
            messages=[
                {"role": "user", "content": query}
            ]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"No latest info found: {e}"


# ---------------------------
# Optional Local Testing
# ---------------------------
def main():
    print("This module is used by Streamlit app. Run app.py instead.")


if __name__ == "__main__":
    main()
