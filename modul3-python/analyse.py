import os
import requests
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    print("Warning: GROQ_API_KEY not found in environment or .env file.")

client = Groq(api_key=groq_api_key)

API_URL = "http://localhost:3000/api/messages"

def fetch_ekg_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None

def analyze_with_llm(text):
    if not groq_api_key:
        print("Cannot analyze: GROQ_API_KEY is missing.")
        return None

    prompt = f"Extrahiere aus diesem EKG-Text Name, Herzfrequenz (BPM) als Zahl und Befund. Antworte nur als JSON mit den Feldern name, bpm, befund.\n\nEKG-Text: {text}"

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return None

def main():
    data = fetch_ekg_data()
    if not data or 'text' not in data:
        print("No EKG text found to analyze.")
        return

    ekg_text = data['text']
    print(f"Empfangener EKG-Text:\n{ekg_text}")

    analysis = analyze_with_llm(ekg_text)
    if not analysis:
        print("LLM-Analyse fehlgeschlagen.")
        return

    try:
        bpm = int(analysis.get('bpm', 0))
    except (ValueError, TypeError):
        bpm = 0

    if bpm < 60:
        classification = "Bradykardie"
    elif 60 <= bpm <= 100:
        classification = "Normal"
    else:
        classification = "Tachykardie"

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
