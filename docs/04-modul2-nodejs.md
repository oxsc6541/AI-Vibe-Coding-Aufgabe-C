# 04-modul2-nodejs.md – Node.js-Server für Datenspeicherung und REST-API

Dieses Dokument beschreibt die Implementierung von Modul 2: Entgegennahme des PDF-Textes von Modul 1 (Java) per WebSocket, Speicherung als JSON-Datei, und Bereitstellung über eine REST-API für Modul 3 (Python).

## 1. Systemvoraussetzungen für Modul 2

- **Node.js v24.18.0** (LTS-Anforderung war v18+, deutlich übertroffen)
- **npm 11.16.0**
- Zwei npm-Pakete: **Express** (REST-API) und **ws** (WebSocket-Server)

## 2. Projekt-Setup

```powershell
cd modul2-nodejs
npm init -y
npm install express ws
```

**Aufgetretener Fehler (falscher Ordner):**
Beim ersten Versuch wurde `npm init -y` ausgeführt, bevor der Ordner `modul2-nodejs` überhaupt existierte — `cd` schlug stillschweigend mit einer Fehlermeldung fehl, aber `npm init` lief trotzdem im übergeordneten `EasyEKG`-Ordner weiter und erzeugte dort eine falsche `package.json`. **Lösung:** Falsche Datei gelöscht, Ordner explizit mit `New-Item` angelegt, danach erst `npm init` ausgeführt.

## 3. server.js – Implementierung

```javascript
const express = require("express");
const WebSocket = require("ws");
const fs = require("fs");
const path = require("path");

const STORAGE_FILE = path.join(__dirname, "ekg-text.json");

// --- WebSocket-Server (Port 8080) ---
const wss = new WebSocket.Server({ port: 8080 });

wss.on("connection", (ws) => {
    console.log("Modul 1 (Java) hat sich verbunden.");

    ws.on("message", (message) => {
        console.log("Daten empfangen, speichere als JSON-Datei...");
        fs.writeFileSync(STORAGE_FILE, message.toString());
        ws.send("OK: Text gespeichert.");
    });

    ws.on("close", () => {
        console.log("Verbindung zu Modul 1 getrennt.");
    });
});

console.log("WebSocket-Server läuft auf Port 8080...");

// --- REST-API (Port 3000) ---
const app = express();

app.get("/api/messages", (req, res) => {
    if (!fs.existsSync(STORAGE_FILE)) {
        return res.status(404).json({ error: "Noch keine Daten vorhanden." });
    }
    const data = fs.readFileSync(STORAGE_FILE, "utf-8");
    res.json(JSON.parse(data));
});

app.listen(3000, () => {
    console.log("REST-API läuft auf Port 3000 (GET /api/messages)...");
});
```

### 3.1 Funktion

1. **WebSocket-Server (Port 8080):** Nimmt die Verbindung von Modul 1 entgegen, speichert jede empfangene Nachricht direkt als `ekg-text.json` auf der Festplatte und bestätigt den Empfang mit `"OK: Text gespeichert."`.
2. **REST-API (Port 3000):** Eine einzige Route `GET /api/messages` liest diese Datei und liefert sie als JSON zurück — das ist die Schnittstelle, über die Modul 3 (Python) später den Text abruft. Falls noch keine Datei existiert, wird `404` mit einer Fehlermeldung zurückgegeben.

## 4.  Fehler bei der Versionskontrolle (Git)

### 4.1 .gitignore mit falscher Kodierung

Der erste Versuch, `node_modules/` per PowerShell-`echo` in eine `.gitignore` zu schreiben, schlug fehl:
```powershell
echo "node_modules/" > .gitignore
```
PowerShell erzeugt dabei standardmäßig eine UTF-16-Datei, die Git nicht korrekt als Ausschlussmuster interpretiert. Folge: Der komplette `node_modules`-Ordner (über 700 Dateien) wurde versehentlich mit committed und gepusht.

**Lösung:**
```powershell
Set-Content -Path .gitignore -Value "node_modules/" -Encoding utf8
git rm -r --cached modul2-nodejs/node_modules
git commit -m "Fix: node_modules aus Versionskontrolle entfernt, .gitignore korrigiert"
git push
```
`Set-Content -Encoding utf8` erzeugt eine Datei in der Kodierung, die Git zuverlässig lesen kann.

### 4.2 Build-Output aus Modul 1 auch betroffen

Derselbe Kodierungs-Stolperstein zeigte sich indirekt auch bei Modul 1: der Maven-`target`-Ordner (kompilierte `.class`-Dateien) landete ebenfalls im Repository, da zu diesem Zeitpunkt noch keine `.gitignore` für Java existierte. Mit demselben Verfahren (`git rm -r --cached`, danach `.gitignore` mit `target/` ergänzen) wurde das nachträglich korrigiert.

**Lerneffekt:** Vor dem ersten Commit eines neuen Sprach-Moduls sollte die passende `.gitignore` (Build-Output, Abhängigkeits-Ordner) angelegt werden — nicht erst danach.

## 5. End-to-End-Test: Modul 1 → Modul 2

Mit laufendem Node.js-Server wurde Modul 1 (Java) gegen `ws://localhost:8080` ausgeführt.

**Fehler (Leerzeichen im Dateinamen):**
Der ursprüngliche Dateiname `EKG Oxana.pdf` (mit Leerzeichen) führte beim Aufruf über Maven zu einem `NoSuchFileException`, da das Leerzeichen die Kommandozeilen-Argumente fälschlich trennte. **Lösung:** Datei umbenannt zu `EKG_Oxana.pdf` (Unterstrich statt Leerzeichen).

**Erfolgreicher Testlauf:**
```
Verbindung zu Modul 2 (Node.js) hergestellt.
Antwort vom Server: OK: Text gespeichert.
Verbindung geschlossen:
```

**Verifikation über die REST-API** (`http://localhost:3000/api/messages`):
```json
{"text":"ECG Waveform Record\nID No.: 050581\nName : Oxana Sex: F Print Out Time: 06.19.2026 23:34:23 X1Age: 44\nBMI = 25,4\n10mm/mV 25mm/sec\n06.25.2025 22:49:41Record Time :\nHeart Rate : 76\nAnalysis : No irregular rhythm found\nRemarks:\nDoctor:\n"}
```

Der vollständige Datenfluss Java → WebSocket → Node.js → REST-API funktioniert nachweislich. Name, Herzfrequenz (76 BPM) und Befund sind im extrahierten Text klar enthalten — die Grundlage für die LLM-Extraktion in Modul 3.

## 6. Offener Punkt

Modul 3 (Python) muss diesen REST-Endpunkt noch abfragen, die Werte per LLM extrahieren und die regelbasierte Herzfrequenz-Analyse durchführen 
