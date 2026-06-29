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