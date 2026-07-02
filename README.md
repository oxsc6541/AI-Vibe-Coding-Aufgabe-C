## 1. Modul 1:Java (PDF-Extraktion & WebSocket-Versand)

### 1.1 PDF-Text extrahieren

```java
try (PDDocument document = Loader.loadPDF(pdfFile)) {
    PDFTextStripper stripper = new PDFTextStripper();
    return stripper.getText(document);
}
```

`Loader.loadPDF(pdfFile)` öffnet die PDF-Datei. `PDFTextStripper.getText()` extrahiert den gesamten Rohtext ohne Formatierung, Layout-Erkennung oder RegEx, egal von welchem EKG-Gerät die PDF stammt. Das `try`-with-resources-Statement schließt das Dokument automatisch nach der Extraktion (kein Speicherleck).

### 1.2 Text als JSON verpacken

```java
private static String toJson(String text) {
    String escaped = text
            .replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "");
    return "{\"text\":\"" + escaped + "\"}";
}
```

Der extrahierte Text wird manuell in ein JSON-Objekt `{"text": "..."}` verpackt. Sonderzeichen (Backslashes, Anführungszeichen, Zeilenumbrüche) werden dabei escaped, damit das JSON gültig bleibt und beim Empfänger (Modul 2) korrekt geparst werden kann.

### 1.3 WebSocket-Verbindung aufbauen und Text senden

```java
WebSocketClient client = new WebSocketClient(serverUri) {
    @Override
    public void onOpen(ServerHandshake handshakedata) {
        send(json);
    }
};
client.connectBlocking();
Thread.sleep(1000);
client.closeBlocking();
```

`connectBlocking()` wartet, bis die Verbindung zu Modul 2 (`ws://localhost:8080`) hergestellt ist. Im `onOpen()`-Callback wird das JSON sofort gesendet. `Thread.sleep(1000)` gibt dem Server Zeit, die Nachricht zu verarbeiten, bevor die Verbindung mit `closeBlocking()` sauber getrennt wird.

---

## 2. Modul 2 – Node.js (WebSocket-Server & REST-API)

### 2.1 WebSocket-Server starten und Nachricht empfangen

```javascript
const wss = new WebSocket.Server({ port: 8080 });

wss.on("connection", (ws) => {
    ws.on("message", (message) => {
        fs.writeFileSync(STORAGE_FILE, message.toString());
        ws.send("OK: Text gespeichert.");
    });
});
```

`new WebSocket.Server({ port: 8080 })` startet den Server auf Port 8080. Bei jeder eingehenden Verbindung wird auf `message`-Events gewartet. Sobald eine Nachricht ankommt, wird sie sofort mit `fs.writeFileSync()` als `ekg-text.json` auf die Festplatte geschrieben. Der Sender (Modul 1) bekommt eine Bestätigung zurück.

### 2.2 REST-API bereitstellen

```javascript
app.get("/api/messages", (req, res) => {
    if (!fs.existsSync(STORAGE_FILE)) {
        return res.status(404).json({ error: "Noch keine Daten vorhanden." });
    }
    const data = fs.readFileSync(STORAGE_FILE, "utf-8");
    res.json(JSON.parse(data));
});
```

Die einzige Route `GET /api/messages` prüft zuerst, ob die JSON-Datei existiert. Falls nicht, wird `404` zurückgegeben. Sonst wird die Datei gelesen und als JSON-Antwort zurückgeschickt – das ist die Schnittstelle für Modul 3.

### 2.3 Zwei Server gleichzeitig

```javascript
const wss = new WebSocket.Server({ port: 8080 });  // WebSocket
app.listen(3000, () => { ... });                    // REST
```

Node.js läuft in einem einzigen Prozess, aber betreibt gleichzeitig zwei Server auf zwei verschiedenen Ports. Das ist möglich, weil Node.js ereignisbasiert (event-driven) und nicht-blockierend arbeitet – beide Server reagieren auf Anfragen, ohne sich gegenseitig zu blockieren.

---

## 3. Modul 3 – Python (REST-Abfrage, LLM-Extraktion & Analyse)

### 3.1 Daten von REST-API abrufen

```python
response = requests.get(API_URL)
response.raise_for_status()
return response.json()
```

`requests.get()` sendet eine HTTP-GET-Anfrage an `http://localhost:3000/api/messages`. `raise_for_status()` wirft automatisch eine Exception, wenn der Server einen Fehler zurückgibt (z.B. 404). `.json()` parst die Antwort direkt als Python-Dictionary.

### 3.2 LLM-Extraktion mit Groq

```python
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"}
)
content = response.choices[0].message.content.strip()
return json.loads(content)
```

Der EKG-Text wird zusammen mit einem Prompt an das Modell `llama-3.3-70b-versatile` (via Groq) geschickt. `response_format={"type": "json_object"}` erzwingt, dass das Modell valides JSON zurückgibt – kein manuelles Parsen von Markdown-Blöcken nötig. Das JSON enthält die Felder `name`, `bpm` und `befund`.

### 3.3 Regelbasierte Herzfrequenz-Klassifikation

```python
if bpm < 60:
    classification = "Bradykardie"
elif 60 <= bpm <= 100:
    classification = "Normal"
else:
    classification = "Tachykardie"
```

Die medizinische Klassifikation erfolgt ausschließlich regelbasiert – kein KI-Einsatz. Das LLM liefert nur den BPM-Wert; die Bewertung übernimmt diese einfache `if/elif/else`-Logik. Das ist eine bewusste Entscheidung: KI für Textverständnis, Regeln für medizinische Einordnung.

---

## 4. Zusammenfassung des Datenflusses

```
[EKG_Oxana.pdf]
      │
      ▼ Loader.loadPDF() + PDFTextStripper.getText()
[Rohtext als String]
      │
      ▼ toJson() → WebSocket send() → ws://localhost:8080
[Modul 2: Node.js]
      │ fs.writeFileSync() → ekg-text.json
      │
      ▼ GET http://localhost:3000/api/messages
[Modul 3: Python]
      │ Groq LLM → name, bpm, befund
      │
      ▼ if/elif/else auf bpm
[Terminal-Ausgabe]
------------------------------
EKG ANALYSE ERGEBNIS
------------------------------
Name:         Oxana
Herzfrequenz: 76 BPM
Befund:       No irregular rhythm found
Einstufung:   Normal
------------------------------
```
