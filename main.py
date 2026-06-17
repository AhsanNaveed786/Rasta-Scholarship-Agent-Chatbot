import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def decide_next_step(history, language="English"):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    system_prompt = f"""You are a helpful AI assistant tasked with finding Pakistani welfare schemes for users.
Before making any recommendations, you MUST gather exactly three facts:
1. Approximate income level
2. Location (Province or City in Pakistan)
3. Student status (whether they are a student or not)

Review the conversation history.
If ANY of these three facts is unknown, ask ONE short follow-up question in {language} to find out the most important missing fact.
If all three facts are known, summarize the user's situation into a single line.

Respond ONLY with a valid JSON object.
If asking a question:
{{"action": "ask", "question": "<your question in {language}>"}}

If ready to recommend:
{{"action": "recommend", "income": "<income>", "location": "<location>", "student": "<student status>", "summary": "<one-line summary>"}}"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={ "type": "json_object" }
        )
        response_text = response.choices[0].message.content.strip()
        return json.loads(response_text)
    except Exception as e:
        return {"action": "ask", "question": f"Error: {e}. Please try again."}


def match_schemes(user_message, schemes=None, debug=False, language="English"):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    query = f"Search the web for real, currently-available Pakistani government welfare schemes, scholarships, or loan programs that fit this user's situation:\n{user_message}"
    
    system_prompt = f"""You are an AI assistant helping a user find Pakistani government welfare schemes they might qualify for using live web search.
Instructions:
1. Reply in the {language} language. If {language} is Urdu, respond in Urdu script (اردو), not Roman Urdu. If {language} is English, respond in clear simple English. The values for "why_eligible", "documents_needed", and "how_to_apply" should be written in {language}.
2. Find only real, currently-existing Pakistani government schemes relevant to the user's actual need — do NOT invent schemes.
3. Return up to 4 schemes, ranked best-first by relevance.
4. For each scheme provide exactly these keys: "scheme_name", "why_eligible", "documents_needed", "how_to_apply", and "official_source" (URL if available from the search, otherwise empty string).
5. If the search finds no genuinely relevant government scheme, return a single item named "No direct scheme found" explaining that in the user's language in the "why_eligible" field and suggesting the closest related option. Leave other fields empty.
6. You must respond ONLY with valid JSON containing an array of match objects. Do not include any extra text, markdown formatting, or code blocks. Just the JSON array."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-search-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )
        
        response_text = response.choices[0].message.content.strip()
        raw_response_text = response_text
        
        # Safely parse JSON in case model added code blocks despite instructions
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        matches = json.loads(response_text)
        if debug:
            return matches, {"system_prompt": system_prompt, "raw_json": raw_response_text, "query": query}
        return matches
    except Exception as e:
        error_msg = f"Failed to perform live scheme matching: {e}"
        err_res = [{"scheme_name": "Error", "why_eligible": error_msg, "documents_needed": "", "how_to_apply": "", "official_source": ""}]
        if debug:
            return err_res, {"system_prompt": system_prompt, "raw_json": "", "query": query}
        return err_res


def get_latest_info(scheme_name, debug=False, language="English"):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    query = f"Search the web for the latest official details or current deadlines about the Pakistani government scheme: {scheme_name}. Provide a short 3-4 sentence summary in {language}. If {language} is Urdu, respond in Urdu script (اردو), not Roman Urdu."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-search-preview",
            messages=[
                {"role": "user", "content": query}
            ]
        )
        info = response.choices[0].message.content.strip()
        if debug:
            return info, {"scheme_name": scheme_name, "query": query}
        return info
    except Exception as e:
        info = "No latest updates found."
        if debug:
            return info, {"scheme_name": scheme_name, "query": query}
        return info


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in .env")
        return
        
    # Load and parse schemes.json
    schemes_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemes.json')
    try:
        with open(schemes_path, 'r', encoding='utf-8') as f:
            schemes = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Could not find {schemes_path}")
        return
    except json.JSONDecodeError:
        print(f"ERROR: Could not parse {schemes_path}")
        return

    # Hardcoded test user message
    test_message = "Mujhe paison ki zaroorat hai, meri income kam hai"
    
    print(f"Project scaffold ready. API key loaded. Loaded {len(schemes)} schemes.")
    
    try:
        matches = match_schemes(test_message, schemes)
        print("\n--- MATCHED SCHEMES ---")
        for match in matches:
            print(f"\nScheme Name: {match.get('scheme_name')}")
            print(f"Why Eligible: {match.get('why_eligible')}")
            print(f"Documents Needed: {match.get('documents_needed')}")
            print(f"How to Apply: {match.get('how_to_apply')}")
            
        if matches:
            top_scheme_name = matches[0].get('scheme_name')
            print("\nLATEST INFO FROM THE WEB")
            print(get_latest_info(top_scheme_name))
    except Exception as e:
        print(f"\nFailed to match schemes: {e}")

if __name__ == "__main__":
    main()
