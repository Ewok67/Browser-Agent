# 🤖 AI Search Guard

Leichtgewichtige Browser Extension (Brave/Chrome), die Suchanfragen mit einem lokalen LLM (llama.cpp) gegen konfigurierbare Regeln prüft.

## Architektur

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Brave Browser  │────▶│  Python Server   │────▶│  llama.cpp   │
│  (Extension)    │◀────│  (localhost:8081)│◀────│  (port 8080) │
└─────────────────┘     └──────────────────┘     └──────────────┘
        │                        │
        │                        ▼
        │               ┌──────────────────┐
        └──────────────▶│  Blocked Page    │
                        │  (localhost:8081)│
                        └──────────────────┘
```

## Setup

### 1. llama.cpp installieren

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DLLAMA_SERVER=ON
cmake --build build --config Release -j
```

### 2. Kleines Modell herunterladen (~400 MB)

```bash
mkdir -p models
curl -L -o models/qwen2.5-0.5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
```

### 3. Extension in Brave laden

1. Brave öffnen → `brave://extensions/`
2. **Entwicklermodus** aktivieren
3. **Entpackte Erweiterung laden** → Ordner `extension/` wählen

### 4. Python Server starten

```bash
cd "C:\Users\ewokb\Documents\Projects\Browser Agent"
python server/server.py
```

### 5. llama.cpp Server starten

Pfad in `server/start-llama.bat` anpassen, dann ausführen:

```bash
C:\Pfad\zu\llama.cpp\build\bin\llama-server.exe ^
  -m models\qwen2.5-0.5b-instruct-q4_k_m.gguf ^
  --port 8080 -c 2048 --host 0.0.0.0
```

## Konfiguration

| Wo | Was |
|---|---|
| Extension-Optionen | Regeln hinzufügen/entfernen, Server-Status |
| `server/config.json` | Ports, max_tokens, temperature |
| Regeln-Sync | Extension → Server via `POST /rules` automatisch |

## API

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/check` | POST | `{"query": "..."}` → `{"blocked": bool, "reason": str}` |
| `/rules` | POST | Regeln aktualisieren |
| `/health` | GET | Server-Status |
| `/blocked` | GET | Blocked Page (Redirect-Ziel) |

## Projektstruktur

```
Browser Agent/
├── extension/              # Browser Extension (MV3, < 50 KB)
│   ├── manifest.json
│   ├── background.js       # Service Worker
│   ├── content.js          # Content Script für Suchseiten
│   ├── options.*           # Einstellungsseite
│   └── rules-default.json  # Standard-Regeln
├── server/                 # Lokaler Python Server
│   ├── server.py           # Standard Library only, keine Dependencies!
│   ├── config.json
│   └── start-llama.bat     # Helper zum Starten von llama.cpp
├── blocked-page/           # Blocked Page (wird ausgeliefert bei Redirect)
│   ├── index.html
│   └── styles.css
└── README.md
```

## Technische Details

- **Extension < 50 KB** (JS + HTML + CSS, keine Libraries)
- **Modell ~400 MB** (Qwen2.5 0.5B Instruct, Q4_K_M quantisiert)
- **Latency:** ~0.5–2 s pro Abfrage (je nach Hardware)
- **CORS:** Server erlaubt `Access-Control-Allow-Origin: *`
- **Keine externen Python-Dependencies** — nur Standard Library

## Nächste Schritte

- [ ] Icons für die Extension erstellen
- [ ] Cache für wiederholte Abfragen
- [ ] Statistik für blockierte Anfragen
- [ ] Mehrere Modelle konfigurierbar
