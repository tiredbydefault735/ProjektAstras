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

## Dokumentation

- **[PyQt6 Guide](./docs/PYQT6_GUIDE.md)** - Umfassende Anleitung zu PyQt6 und der Verwendung in ProjektAstras (START HERE!)
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
│   │   └── simulation_map.py
│   └── styles/           # Styling & Theming
│       ├── stylesheet.py     # Dynamischer CSS-Generator
│       └── color_presets.py  # Farbthemes
├── backend/              # Simulation Logic
│   └── model.py          # SimPy Model
├── static/               # Assets & Data
│   ├── data/
│   │   └── species.json  # Species Config
│   └── src/              # Images
└── docs/                 # Documentation
    ├── PYQT6_GUIDE.md           # PyQt6 Anleitung ⭐
    ├── THEME_SYSTEM.md          # Theme-Dokumentation
    ├── Anforderungen.md
    └── Konzeption.md
```

## Über das Projekt
- **Framework:** PyQt6 für native, scharfe UI (ideal für Pixel-Art Ästhetik)
- **Simulation:** SimPy für Ereignis-basierte Simulation
- **Design:** Dark Theme mit konfigurierbaren Farbpresets, keine Abrundungen
- **Modular:** Einfache Erweiterung durch Separation of Concerns

## Quick Start für Entwicklung

### Neue UI-Komponente hinzufügen
Siehe [PyQt6 Guide - Task 1](./docs/PYQT6_GUIDE.md#task-1-neuen-button-hinzufügen)

### Theme wechseln
```python
# In main.py
main(preset_name="Dark Blue")  # Dark Red, Dark Green, Dark Purple
```

### Neuen Screen hinzufügen
Siehe [PyQt6 Guide - Task 4](./docs/PYQT6_GUIDE.md#task-4-neuen-screen-hinzufügen)

## Über den Autor
Dieses Projekt wurde von Tired im Rahmen des 3. Lehrjahres an der Berufsschule erstellt.
