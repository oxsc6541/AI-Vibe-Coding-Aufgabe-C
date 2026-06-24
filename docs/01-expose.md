Dieses Dokument beschreibt das Konzept für EasyEKG 1.0, eine leichtgewichtige, verteilte Anwendung zur automatisierten Auswertung von textbasierten EKG-PDF-Berichten. Das System setzt auf minimale, lauffähige Kernlogik in drei verschiedenen Programmiersprachen.

## 1. Systemarchitektur & Datenfluss

Die Plattform besteht aus drei getrennten Modulen), die über Standard-Netzwerkprotokolle (WebSockets und REST) autonom miteinander kommunizieren.


[ MODUL 1: Java CLI ]
       │ (1. Liest beliebige lokale PDF-Datei ein)
       │ (2. Extrahiert nur den Rohtext, kein RegEx)
       ▼ [ WebSocket-Stream - Port 8080 ]
[ MODUL 2: Node.js Server ] ──> [ Lokale JSON-Datei (Speicher) ]
       │
       ▼ [ REST API - Port 3000 (`GET /api/messages`) ]
[ MODUL 3: Python CLI ]
       │ (1. LLM extrahiert Name, BPM, Befund aus Rohtext als JSON)
       ▼ (2. Regelbasierte Herzfrequenz-Analyse, if/elif/else)
   Terminal-Ausgabe (Bradykardie / Normal / Tachykardie)


## 2. Die 3 Kern-Module

### Modul 1: Java (PDF-Reader & WebSocket Client)

- **Technologie:** Java 17+ (getestet mit OpenJDK 23.0.2 Temurin), Apache PDFBox, Java-WebSocket
- **Aufgabe:** Öffnet eine beliebige lokale PDF-Datei, extrahiert den vollständigen Text (`PDFTextStripper.getText()`) und streamt ihn als kompakten JSON-String über ein WebSocket-Protokoll an Modul 2. Keine Formaterkennung, keine RegEx-Filterung — das Modul liefert reinen Text, unabhängig von PDF-Layout oder Gerätehersteller. Dadurch funktioniert es mit EKG-Berichten unterschiedlicher Geräte/Praxen, nicht nur mit dem eigenen Export-Format.

### Modul 2: Node.js (Datenspeicher & REST-API)

- **Technologie:** Node.js 18, Express, `ws`-Bibliothek
- **Aufgabe:** Betreibt einen permanenten WebSocket-Server auf Port 8080, nimmt das JSON aus Modul 1 entgegen und schreibt es direkt als lokale JSON-Datei auf die Festplatte. Gleichzeitig stellt das Modul eine Express-REST-API auf Port 3000 mit einer einzigen GET-Route bereit, um den Text für Modul 3 anzubieten.

### Modul 3: Python (REST-Client, KI-Extraktion & Analyse)

- **Technologie:** Python 3.11, `requests`-Bibliothek, LLM-API
- **Aufgabe:** Fragt den REST-Endpunkt von Modul 2 ab und erhält den Rohtext des PDF-Berichts.
    1. **Extraktion:** Ein LLM-Aufruf liest aus dem Rohtext Name, Herzfrequenz (BPM) und Befund heraus und liefert sie als strukturiertes JSON zurück. Das übernimmt die Flexibilität gegenüber unterschiedlichen Gerätehersteller-Formaten, die ein starres RegEx nicht leisten könnte.
    2. **Analyse:** Auf dem extrahierten BPM-Wert läuft eine einfache, regelbasierte `if/elif/else`-Prüfung (Bradykardie / Normal / Tachykardie). Das Ergebnis wird formatiert im Terminal ausgegeben.

### Ergänzung zur Entwicklungsumgebung (IDE)

Für die Implementierung wird Cursor verwendet, ein eigenständiger VS-Code-Fork mit integriertem KI-Agenten. Cursor übernimmt die Rolle des Pair-Programmers in der IDE und verwaltet die Multi-Language-Architektur (Java, Node.js, Python).

Als Nachweis für die geforderte Gegenprobe wurde zusätzlich Google Jules eingesetzt – ein eigenständiger KI-Coding-Agent, der direkt auf das GitHub-Repository des Projekts zugreift und Aufgaben autonom bearbeitet. Jules wurde für eine kleine Teilaufgabe genutzt und lieferte das Ergebnis als Pull Request (siehe `02-setup.md`).

**Begründung der Aufteilung:** Die KI wird ausschließlich für Textverständnis eingesetzt (Extraktion aus wechselnden PDF-Layouts), nicht für die medizinische Bewertung.

## 3. Der Dokumentationsfahrplan (6 MDs)

1. `01-expose.md` (dieses Dokument) – Konzept).
2. `02-setup.md` – Erstellung der Verzeichnisstruktur über das Windows 11 Terminal (PowerShell).
3. `03-modul1-java.md` – Java-Code für PDFBox-Textextraktion und WebSocket-Übertragung.
4. `04-modul2-nodejs.md` – Node.js-Code für Datei-Speicherung und Express-Route.
5. `05-modul3-python.md` – Python-Code für API-Abfrage, LLM-Extraktion und regelbasierte Auswertung.
6. `06-code-verstehen.md` – Erklärung der wichtigsten Codezeilen.