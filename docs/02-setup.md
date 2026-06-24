# 02-setup.md – Erstellung der Verzeichnisstruktur & Systemvorbereitung

Dieses Dokument beschreibt die Einrichtung der Entwicklungsumgebung und das Anlegen der physischen Ordnerstruktur über das Windows 11 Terminal (PowerShell).

## 1. Systemvoraussetzungen (Pre-requisites)

Für den reibungslosen Betrieb der drei autonomen Module müssen folgende Laufzeitumgebungen auf dem Host-System installiert sein:

- **Java JDK 17+** (für Modul 1, installiert: OpenJDK 23.0.2 Temurin)
- **Node.js LTS v18+** (für Modul 2)
- **Python 3.11+** (für Modul 3)

## 2. Automatisierte Erstellung via PowerShell

Die gesamte Projektstruktur wurde mit folgendem Skript blockweise über die native Windows PowerShell initialisiert, um menschliche Fehler beim manuellen Anlegen zu minimieren:

```powershell
# In das Desktop-Verzeichnis wechseln
Set-Location -Path "$env:USERPROFILE\Desktop"

# Hauptprojektordner anlegen und betreten
New-Item -ItemType Directory -Path ".\EasyEKG"
cd .\EasyEKG

# Funktionale Modul- und Dokumentationsordner erstellen
New-Item -ItemType Directory -Path ".\modul1-java"
New-Item -ItemType Directory -Path ".\modul2-nodejs"
New-Item -ItemType Directory -Path ".\modul3-python"
New-Item -ItemType Directory -Path ".\docs"

# Leere Dokumentations-Markdown-Dateien generieren
$docs = @("01-expose.md", "02-setup.md", "03-modul1-java.md", "04-modul2-nodejs.md", "05-modul3-python.md", "06-code-verstehen.md")
foreach ($doc in $docs) { 
    New-Item -ItemType File -Path ".\docs\$doc" 
}
```

## 3. Resultierende Verzeichnisstruktur

Nach Ausführung des Skripts stellt sich das verteilte System im Workspace wie folgt dar:

```text
📁 EasyEKG/
├── 📁 docs/               # Alle 6 Markdown-Dokumente für die Abgabe
├── 📁 modul1-java/        # Java-Quellcode & Maven-Konfiguration (Port 8080 Client)
├── 📁 modul2-nodejs/      # Node.js Express & WebSocket-Server (Port 8080 & 3000)
└── 📁 modul3-python/      # Python-Skript & KI-Analyse-Pipeline (Port 3000 Client)
```

Die IDE (Cursor) wird anschließend direkt aus dem Verzeichnis heraus mit dem CLI-Befehl `code .` gestartet.

## 4. Nachweis: KI-CLI-Werkzeug (Google Jules)

Zusätzlich zu Cursor wurde **Google Jules** als eigenständiger KI-Coding-Agent eingesetzt – über die lokale CLI **Jules Tools**, installiert via npm und direkt im Windows-Terminal bedient. Anders als Cursor (IDE-integrierter Agent) läuft Jules dabei autonom in einer Remote-VM und greift auf das verbundene GitHub-Repository zu; die Steuerung erfolgt jedoch lokal über die Kommandozeile.

### 4.1 Installation der Jules CLI

```powershell
npm install -g @google/jules
```

**Aufgetretener Fehler (Execution Policy):**
Bei der ersten Ausführung blockierte PowerShell das Skript `npm.ps1` standardmäßig aus Sicherheitsgründen:

```
npm : Die Datei "C:\Program Files\nodejs\npm.ps1" kann nicht geladen werden, da die Ausführung von Skripts auf diesem System deaktiviert ist.
```

**Lösung:**

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Zweiter Fehler (falscher Paketname):**
Der zunächst verwendete Paketname `@google/jules-tools` existiert nicht im npm-Registry:

```
npm error code E404
npm error 404 Not Found - GET https://registry.npmjs.org/@google%2fjules-tools - Not found
```

Der korrekte Paketname lautet `@google/jules` (ohne `-tools`-Suffix). Nach Korrektur lief die Installation erfolgreich durch.

### 4.2 Authentifizierung & Repo-Verbindung

```powershell
jules login
```

Öffnet den Browser zur Google-OAuth-Authentifizierung. Nach erfolgreichem Login:

```
You are now logged in.
```

Verbundene Repositories prüfen:

```powershell
jules remote list --repo
```

Das Projekt-Repository `oxsc6541/AI-Vibe-Coding-Aufgabe-C` ist in der Liste sichtbar und damit erfolgreich mit dem Google-Account verknüpft.

### 4.3 Übergabe der Aufgabe an Jules

Über die CLI wurde folgende Aufgabe an Jules übergeben:

```powershell
jules new --repo oxsc6541/AI-Vibe-Coding-Aufgabe-C "[HIER: tatsächlich verwendeter Jules-Prompt einfügen]"
```

Jules liefert das Ergebnis als Pull Request: [HIER: PR-Link einfügen].

Damit ist neben dem IDE-basierten Werkzeug (Cursor) auch der Einsatz eines eigenständigen, CLI-gesteuerten KI-Agenten dokumentiert.
