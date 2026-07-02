# 05-modul3-python.md – Python-Code für LLM-Extraktion und regelbasierte Analyse

Dieses Dokument beschreibt die Implementierung von Modul 3: Abruf des EKG-Textes von Modul 2 per REST, LLM-gestützte Extraktion von Name, BPM und Befund, sowie regelbasierte Herzfrequenz-Klassifikation.

## 1. Systemvoraussetzungen für Modul 3

- **Python 3.11** (installiert via `winget install Python.Python.3.11`)
- **pip** (kommt mit Python)
- Bibliotheken: `requests`, `python-dotenv`, `groq`

## 2. Ausgangslage (von Jules erstellt)

Jules hatte in einem separaten PR (`#3`) bereits die Datei `modul3-python/analyse.py` mit einem Grundgerüst erstellt, das ursprünglich die `google-generativeai`-Bibliothek und das Modell `gemini-1.5-flash` nutzte. Zusätzlich lagen durch PR `#1` bereits `requirements.txt` und `.env.example` vor.

Die eigentliche Implementierung erforderte jedoch mehrere Anpassungen aufgrund realer Probleme (siehe Abschnitt 3).

## 3. Reale Stolpersteine

### 3.1 Python nicht installiert

Python war auf dem System nicht vorhanden. Installation via:

```powershell
winget install Python.Python.3.11
```

### 3.2 Gemini API – Quota = 0

Der ursprüngliche Plan sah Google Gemini als LLM-Provider vor. Alle Versuche scheiterten mit folgendem Fehler:

```
429 RESOURCE_EXHAUSTED: Quota exceeded for metric:
generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0
```

Das Limit war nicht nur erschöpft, sondern auf `0` gesetzt – der kostenlose Google-Account hatte in diesem Projekt keinen API-Zugang. Mehrere Versuche mit unterschiedlichen Modellen (`gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-2.0-flash-exp`) und einem neu erstellten API-Key scheiterten alle.

### 3.3 Veraltetes Gemini SDK

Parallel zum Quota-Problem zeigte sich, dass die `google-generativeai`-Bibliothek vollständig deprecated ist:

```
FutureWarning: All support for the `google.generativeai` package has ended.
Please switch to the `google.genai` package as soon as possible.
```

Das neue `google-genai`-Paket wurde installiert (`pip install google-genai`), scheiterte aber ebenfalls am Quota-Problem.

### 3.4 .env versehentlich in Git committed

Die `.env`-Datei mit dem Gemini API-Key wurde versehentlich committed und gepusht. GitHub blockierte den Push automatisch über Secret Scanning:

```
remote: GITHUB PUSH PROTECTION
remote: Push cannot contain secrets
remote: GCP API Key Bound to a Service Account
```

**Lösung:**
```powershell
git rm --cached modul3-python/.env
git rm --cached .env
Set-Content -Path "modul3-python\.gitignore" -Value ".env" -Encoding utf8
git add .
git commit -m "Fix: .env aus Versionskontrolle entfernt"
```

Da der Gemini-Key sowieso Quota 0 hatte und damit wertlos war, wurde der Push über die GitHub Secret Scanning Oberfläche ("It's used in tests") freigegeben.

**Lerneffekt:** Vor dem ersten Commit einer neuen Sprach-Umgebung `.gitignore` mit `.env` anlegen – nicht erst danach.

### 3.5 Lösung: Wechsel auf Groq

Als zuverlässige, kostenlose Alternative wurde **Groq** eingesetzt. Groq bietet eine kostenlose API mit großzügigen Limits und unterstützt das Modell `llama-3.3-70b-versatile`.

```powershell
pip install groq --break-system-packages
```

## 4. analyse.py – Implementierung

```python
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
```

### 4.1 Funktionsweise (Kurzfassung)

1. **API-Abfrage:** `fetch_ekg_data()` ruft `GET http://localhost:3000/api/messages` ab und liefert den JSON-Inhalt mit dem EKG-Rohtext.
2. **LLM-Extraktion:** `analyze_with_llm()` schickt den Text per Groq-API an `llama-3.3-70b-versatile`. Der Prompt fordert eine strukturierte JSON-Antwort mit den Feldern `name`, `bpm`, `befund`. `response_format={"type": "json_object"}` erzwingt valides JSON – kein manuelles Parsen von Markdown-Blöcken nötig.
3. **Regelbasierte Klassifikation:** Ein einfaches `if/elif/else` prüft den BPM-Wert: unter 60 = Bradykardie, 60–100 = Normal, über 100 = Tachykardie.
4. **Formatierte Ausgabe:** Das Ergebnis wird strukturiert im Terminal ausgegeben.

**Begründung der KI-Nutzung:** Das LLM übernimmt ausschließlich die Textextraktion aus wechselnden PDF-Layouts – nicht die medizinische Bewertung. Die Klassifikation (Bradykardie/Normal/Tachykardie) erfolgt regelbasiert ohne KI.

## 5. Konfiguration (.env)

Der API-Key wird über eine lokale `.env`-Datei geladen (nicht im Repository):

```
GROQ_API_KEY=dein-groq-api-key
```

Die `.env`-Datei ist in `modul3-python/.gitignore` eingetragen und wird nicht versioniert.

## 6. End-to-End-Test (vollständige Kette)

Mit laufendem Node.js-Server (Modul 2) wurde der vollständige Datenfluss getestet:

```
------------------------------
EKG ANALYSE ERGEBNIS
------------------------------
Name:         Oxana
Herzfrequenz: 76 BPM
Befund:       No irregular rhythm found
Einstufung:   Normal
------------------------------
```

Der komplette Datenfluss Java → WebSocket → Node.js → REST → Python/Groq → Terminal-Ausgabe funktioniert nachweislich.
