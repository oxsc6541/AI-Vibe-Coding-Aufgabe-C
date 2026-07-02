import os
import requests
import json
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Load environment variables and configure Gemini
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    print("Warning: GEMINI_API_KEY not found in environment or .env file.")

genai.configure(api_key=gemini_api_key)

# 2. Fetch data from REST API
API_URL = "http://localhost:3000/api/messages"

def fetch_ekg_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None

def analyze_with_gemini(text):
    if not gemini_api_key:
        print("Cannot analyze: GEMINI_API_KEY is missing.")
        return None

    prompt = f"Extrahiere aus diesem EKG-Text Name, Herzfrequenz (BPM) als Zahl und Befund. Antworte nur als JSON mit den Feldern name, bpm, befund.\n\nEKG-Text: {text}"

    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content(prompt)
        # Remove markdown code blocks if present
        content = response.text.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        return json.loads(content)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def main():
    data = fetch_ekg_data()
    if not data or 'text' not in data:
        print("No EKG text found to analyze.")
        return

    ekg_text = data['text']
    print(f"Empfangener EKG-Text: {ekg_text}")

    analysis = analyze_with_gemini(ekg_text)
    if not analysis:
        print("Gemini analysis failed.")
        return

    # 3. Rule-based BPM check
    try:
        bpm = int(analysis.get('bpm', 0))
    except (ValueError, TypeError):
        bpm = 0

    classification = ""
    if bpm < 60:
        classification = "Bradykardie"
    elif 60 <= bpm <= 100:
        classification = "Normal"
    else:
        classification = "Tachykardie"

    # 4. Formatted output
    print("-" * 30)
    print("EKG ANALYSE ERGEBNIS")
    print("-" * 30)
    print(f"Name:         {analysis.get('name', 'N/A')}")
    print(f"Herzfrequenz: {bpm} BPM")
    print(f"Befund:       {analysis.get('befund', 'N/A')}")
    print(f"Einstufung:   {classification}")
    print("-" * 30)

if __name__ == "__main__":
    main()
