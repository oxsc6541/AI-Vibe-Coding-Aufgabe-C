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