# Arachfara - Simulation des Überlebenskampfes
Dieses Projekt simuliert die Interaktionen und den Überlebenskampf von vier Subspezies der Spezies "Arachfara" auf dem Planeten Astras. Das Ziel ist es, die dynamischen Verhaltensweisen in einer begrenzten Umgebung visuell darzustellen und zu analysieren.

## Tech Stack
- **Frontend:** PyQt6 (sharp, pixel-art optimiert, keine Abrundungen)
- **Backend:** Python + SimPy (diskrete Event-Simulation)
- **Architektur:** Frontend/Backend Separation, JSON-basierte Konfiguration

## Installation und Nutzung

### Voraussetzungen
- Python 3.10+

### Installation
```bash
# Clone das Repository
git clone <repo-url>
cd ProjektAstras

# Installiere Dependencies
pip install PyQt6 simpy

# Starte die App
python frontend/main.py
```

## Documentation

- **[Theme System](./docs/THEME_SYSTEM.md)** - Dokumentation des modularen Farbsystems
- **[Anforderungen](./docs/Anforderungen.md)** - Funktionale Anforderungen
- **[Konzeption](./docs/Konzeption.md)** - Technisches Design

## Projektstruktur
```
ProjektAstras/
├── frontend/              # PyQt6 GUI
│   ├── main.py           # App Entry Point
│   ├── screens/          # UI Screens
│   │   ├── start_screen.py
│   │   ├── simulation_screen.py
- **Framework:** PyQt6 für native, scharfe UI (ideal für Pixel-Art Ästhetik)
# ProjektAstras — Arachfara Simulation

ProjektAstras ist eine diskrete Ereignis-Simulation, die das Verhalten und die Interaktionen mehrerer Arachfara-Subspezies in einer begrenzten Umgebung modelliert und visualisiert.

Kurz: Backend (SimPy) simuliert die Entitäten und Interaktionen; Frontend (PyQt6) zeigt die Karte, Populationen und Logs an.

## Tech stack
- Backend: Python 3.10+ mit SimPy
- Frontend: PyQt6 (UI)

## Schnellstart (Entwicklung)
1. Repository klonen

```bash
git clone <repo-url>
cd ProjektAstras
```

2. Abhängigkeiten installieren

```bash
pip install -r requirements.txt  # or: pip install PyQt6 simpy
```

3. App starten (Entwickler-Modus)

```bash
python frontend/main.py
```

## Projektstruktur (Kurzüberblick)

ProjektAstras/
├── frontend/         # PyQt6 UI and screens (app entry point)
│   ├── main.py       # Application entry (runs the UI)
│   ├── screens/      # UI screens (start, simulation, map, ...)
│   └── styles/       # Styling and theme presets
├── backend/          # Simulation logic (core app code)
│   ├── model.py      # `SimulationModel` — setup() and step()
│   ├── entities.py   # Entity classes (Loner, Clan, FoodSource)
│   ├── processors.py # Interaction & behavior processors (food, combat, formation)
│   ├── spatial.py    # Spatial grid helper (nearby queries)
│   ├── temperature.py# Temperature/transition/regen logic
│   ├── spawn.py      # Loner spawn helpers
   └── stats.py      # Snapshot collector and stats helpers
├── static/           # Assets (images, fonts, icons)
├── docs/             # Project documentation and notes (non-essential for runtime)
├── tests/            # Unit and integration tests (not required to run the app)
└── build/            # Build artifacts (safe to ignore/remove)

## Entwickeln & Übersicht

- Laufzeit-relevante Dateien (für die App-Ausführung):
    - `frontend/main.py` — Startet die GUI und verbindet Controls mit Backend
    - `frontend/screens/` — Enthält `simulation_screen.py` und `simulation_map.py` (UI rendering)
    - `backend/model.py` — Simulation core (`setup`, `step`)
    - `backend/entities.py` — `Loner`, `Clan`, `FoodSource`
    - `backend/processors.py` — Verhalten (Nahrung, Interaktionen, Formation)
    - `backend/spatial.py` — Nachbarschafts-/Grid-Abfragen
    - `config.py` — zentrale Konstanten/Defaults

- Development / non-runtime files (safe to ignore when running the app):
    - `build/`, `main.onefile-build/` — generated build artifacts
    - `tests/` — test code
    - `docs/` — long-form docs (useful for contributors, not required at runtime)

Die Hauptsimulation wird in `backend/model.py` initialisiert (`SimulationModel.setup`) und per `SimulationModel.step()` vorwärts bewegt. Helper-Module (`processors.py`, `spatial.py`, `temperature.py`, `stats.py`, `spawn.py`) kapseln Verhalten und erleichtern Wartung.

## Hinweise
- Entfernte veraltete/detaillierte Guides aus der Haupt-README; für tiefere UI-Infos sehen Sie bitte `docs/` oder den Code in `frontend/screens/`.

---
Wenn Sie möchten, kann ich `docs/PYQT6_GUIDE.md` entweder löschen, kürzen oder in eine kurze `docs/DEVELOPER_NOTES.md` übertragen.
