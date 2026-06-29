# 03-modul1-java.md – Java-Code für PDF-Extraktion und WebSocket-Übertragung

Dieses Dokument beschreibt die Implementierung von Modul 1: 
das Einlesen einer EKG-PDF-Datei und das Versenden des extrahierten Textes an Modul 2 (Node.js) über WebSocket.

## 1. Systemvoraussetzungen für Modul 1

- **Java JDK 17+** (installiert: OpenJDK 23.0.2 Temurin)
- **Apache Maven 3.9.16** (manuell installiert, siehe Abschnitt 2)
- **Apache PDFBox 3.0.7** (Maven-Dependency)
- **Java-WebSocket 1.6.0** (Maven-Dependency, Library: `org.java-websocket`)

## 2. Maven-Installation 

Da `winget install Apache.Maven` kein offizielles Paket liefert, wurde Maven manuell installiert:

1. ZIP-Archiv von https://maven.apache.org/download.cgi heruntergeladen
2. Entpackt nach `C:\Users\oxana\Apps\Apache-Maven\apache-maven-3.9.16`
3. `bin`-Ordner per `[Environment]::SetEnvironmentVariable` zum User-PATH hinzugefügt

** Fehler 1 (Zugriff verweigert):**
Der ursprüngliche Versuch, nach `C:\Program Files\Apache Maven` zu entpacken, schlug fehl:
```
New-Item : Der Zugriff auf den Pfad "Apache Maven" wurde verweigert.
```
**Lösung:** Installation in den Benutzerordner (`$env:USERPROFILE\Apps\Apache-Maven`) statt in einen Systemordner, der Adminrechte erfordert.

** Fehler 2 (PowerShell verschluckt `-D`-Parameter):**
Beim ersten Aufruf von `mvn archetype:generate` mit mehreren `-DgroupId=...`-Parametern ohne Anführungszeichen kam wiederholt:
```
[ERROR] The goal you specified requires a project to execute but there is no POM in this directory
```
Obwohl der Befehl korrekt aussah. **Lösung:** Jeden `-D`-Parameter einzeln in Anführungszeichen setzen:
```powershell
mvn archetype:generate "-DgroupId=de.easyekg" "-DartifactId=modul1-java" "-DarchetypeArtifactId=maven-archetype-quickstart" "-DarchetypeVersion=1.4" "-DinteractiveMode=false"
```

**Fehler 3 (verschachtelter Ordner):**
Maven legte das Projekt in `modul1-java\modul1-java\` an (Artifact-Ordner innerhalb des bereits passend benannten Ordners). Mit `Move-Item` und `Remove-Item` wurde der Inhalt eine Ebene nach oben verschoben.

## 3. pom.xml – Konfiguration

Java-Version wurde von der Vorlage (1.7) auf **17** angehoben, passend zur Projekt-Anforderung und zum installierten JDK 23. Zwei Dependencies wurden ergänzt:

```xml
<dependencies>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>4.11</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>org.apache.pdfbox</groupId>
      <artifactId>pdfbox</artifactId>
      <version>3.0.7</version>
    </dependency>
    <dependency>
      <groupId>org.java-websocket</groupId>
      <artifactId>Java-WebSocket</artifactId>
      <version>1.6.0</version>
    </dependency>
</dependencies>
```

## 4. App.java – Implementierung

```java
package de.easyekg;

import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import java.io.File;
import java.net.URI;

public class App {

    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.out.println("Bitte Pfad zur PDF-Datei als Argument angeben.");
            System.out.println("Beispiel: java -jar modul1-java.jar \"../testdaten/EKG Oxana.pdf\"");
            return;
        }

        File pdfFile = new File(args[0]);
        String text = extractText(pdfFile);
        String json = toJson(text);

        sendOverWebSocket(json);
    }

    private static String extractText(File pdfFile) throws Exception {
        try (PDDocument document = Loader.loadPDF(pdfFile)) {
            PDFTextStripper stripper = new PDFTextStripper();
            return stripper.getText(document);
        }
    }

    private static String toJson(String text) {
        String escaped = text
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "");
        return "{\"text\":\"" + escaped + "\"}";
    }

    private static void sendOverWebSocket(String json) throws Exception {
        URI serverUri = new URI("ws://localhost:8080");

        WebSocketClient client = new WebSocketClient(serverUri) {
            @Override
            public void onOpen(ServerHandshake handshakedata) {
                System.out.println("Verbindung zu Modul 2 (Node.js) hergestellt.");
                send(json);
            }

            @Override
            public void onMessage(String message) {
                System.out.println("Antwort vom Server: " + message);
            }

            @Override
            public void onClose(int code, String reason, boolean remote) {
                System.out.println("Verbindung geschlossen: " + reason);
            }

            @Override
            public void onError(Exception ex) {
                System.err.println("WebSocket-Fehler: " + ex.getMessage());
            }
        };

        client.connectBlocking();
        Thread.sleep(1000);
        client.closeBlocking();
    }
}
```

### 4.1 Funktionsweise (Kurzfassung)

1. **Einlesen:** Der Pfad zur PDF-Datei wird als Kommandozeilen-Argument übergeben (kein hartkodierter Pfad — dadurch funktioniert das Modul mit beliebigen EKG-PDFs unterschiedlicher Geräte/Praxen).
2. **Extraktion:** `Loader.loadPDF()` öffnet das Dokument, `PDFTextStripper.getText()` liefert den reinen Text — ohne RegEx oder Layout-Erkennung, wie im Konzept (`01-expose.md`) festgelegt.
3. **JSON-Verpackung:** Der Text wird manuell escaped (Anführungszeichen, Backslashes, Zeilenumbrüche) und in ein einfaches JSON-Objekt `{"text": "..."}` verpackt.
4. **WebSocket-Versand:** Eine Verbindung zu `ws://localhost:8080` (Modul 2) wird aufgebaut; im `onOpen()`-Callback wird das JSON gesendet, danach wird die Verbindung wieder geschlossen.

## 5. Testdaten

Eine reale EKG-PDF (`testdaten/EKG Oxana.pdf`) dient als Testgrundlage für die Extraktion.

## 6. Offener Punkt

Das Modul kann erst vollständig getestet werden, sobald Modul 2 (Node.js-WebSocket-Server auf Port 8080) läuft.