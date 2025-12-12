# PyQt6 Dokumentation - ProjektAstras

Eine Anleitung zum Verständnis und zur Verwendung der PyQt6-Implementierung in ProjektAstras.

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Projektstruktur](#projektstruktur)
3. [Kernkonzepte](#kernkonzepte)
4. [Wichtige PyQt6-Komponenten](#wichtige-pyqt6-komponenten)
5. [Anwendungsablauf](#anwendungsablauf)
6. [Theme-System](#theme-system)
7. [Häufige Aufgaben](#häufige-aufgaben)

---

## Überblick

**ProjektAstras** ist eine PyQt6-Anwendung mit zwei Hauptbildschirmen:
1. **StartScreen** - Intro/Menu mit Logo und Buttons
2. **SimulationScreen** - Hauptsimulation mit Karte und Kontrollen

### Warum PyQt6?
- ✅ Scharfe, pixel-perfekte Interfaces (ideal für Pixel-Art)
- ✅ Keine erzwungenen Abrundungen (im Gegensatz zu KivyMD)
- ✅ Native Widgets → bessere Plattform-Integration
- ✅ Modulares Design → einfache Wartung

---

## Projektstruktur

```
frontend/
├── main.py                           # App-Einstiegspunkt & Fenster-Management
├── screens/                          # UI-Screens
│   ├── start_screen.py              # Startbildschirm
│   ├── simulation_screen.py         # Simulationsbildschirm
│   ├── simulation_map.py            # Custom Map-Widget
│   └── __init__.py
└── styles/                           # Styling & Themes
    ├── stylesheet.py                # Dynamischer CSS-Generator
    ├── color_presets.py             # Farbthemes
    └── __init__.py

backend/
└── model.py                         # SimPy Simulation

static/
├── data/
│   └── species.json                # Spezies-Konfiguration
└── src/
    └── logo_astras_pix.png         # Bilder
```

---

## Kernkonzepte

### 1. **QMainWindow** - Das Hauptfenster
```python
class ArachfaraApp(QMainWindow):
    """Das Hauptfenster der Anwendung."""
```

**Wichtige Methoden:**
- `setWindowTitle()` - Titel setzen
- `showFullScreen()` - Im Vollbildmodus starten
- `setCentralWidget()` - Inhalt setzen
- `setStyleSheet()` - CSS-Styling anwenden

**Beispiel aus `main.py`:**
```python
self.setWindowTitle("Projekt Astras")
self.showFullScreen()  # Vollbildmodus
self.setStyleSheet(get_stylesheet(self.color_preset))
```

---

### 2. **QStackedWidget** - Screen-Navigation
Ein Container, der mehrere Widgets übereinander stapelt und nur eines anzeigt.

```python
self.stacked = QStackedWidget()
self.stacked.addWidget(self.start_screen)      # Screen 0
self.stacked.addWidget(self.simulation_screen)  # Screen 1

# Wechsel zum Simulationsbildschirm
self.stacked.setCurrentWidget(self.simulation_screen)
```

**Vergleich mit anderen Frameworks:**
| Framework | Äquivalent |
|-----------|-----------|
| PyQt6 | `QStackedWidget` |
| Kivy | `ScreenManager` |
| Flutter | `Navigator` / `PageView` |

---

### 3. **Layouts** - Widget-Anordnung

PyQt6 verwendet Layouts für responsive Design (ähnlich wie Flexbox/CSS Grid):

```python
# Vertikales Layout (Stack vertikal)
main_layout = QVBoxLayout()
main_layout.addWidget(header)
main_layout.addWidget(content)
main_layout.addWidget(footer)

# Horizontales Layout (nebeneinander)
button_layout = QHBoxLayout()
button_layout.addWidget(btn_play)
button_layout.addWidget(btn_pause)
button_layout.addWidget(btn_stop)

# Layout zu einem Widget hinzufügen
self.setLayout(main_layout)
```

**Layout-Beispiel aus `simulation_screen.py`:**
```python
# Main Layout (vertikal)
main_layout = QVBoxLayout()
main_layout.addLayout(top_bar)           # Top-Navigation
main_layout.addLayout(content_layout)    # Map + Sidebar (horizontal)
main_layout.addLayout(control_layout)    # Buttons
main_layout.addWidget(log_frame)         # Logs

self.setLayout(main_layout)
```

---

### 4. **Widgets** - UI-Elemente

#### QPushButton
```python
btn = QPushButton("Start Simulation")
btn.clicked.connect(self.on_button_clicked)  # Signal-Slot Connection
btn.setFixedWidth(100)
btn.setFixedHeight(40)
```

#### QLabel
```python
label = QLabel("Temperatur: 20 C°")
label.setAlignment(Qt.AlignmentFlag.AlignCenter)
label.setStyleSheet("color: #ffffff;")
```

#### QSlider
```python
slider = QSlider(Qt.Orientation.Horizontal)
slider.setMinimum(-50)
slider.setMaximum(50)
slider.setValue(20)
slider.valueChanged.connect(lambda v: label.setText(f"Temp: {v}"))
```

#### QFrame
Ein einfacher Container für Styling:
```python
frame = QFrame()
frame.setStyleSheet("background-color: #2a2a2a; border: 2px solid #666666;")
layout = QVBoxLayout(frame)
layout.addWidget(some_widget)
```

---

### 5. **Signals & Slots** - Event-Handling

Das PyQt6-Equivalent zu Event-Listenern:

```python
# Signal = Event (z.B. Button-Click)
btn.clicked.connect(self.on_button_clicked)

# Slider-Wert ändert sich
slider.valueChanged.connect(self.on_slider_changed)

# Custom Signal definieren
from PyQt6.QtCore import pyqtSignal
class MyWidget(QWidget):
    value_changed = pyqtSignal(int)  # Definieren
    
    def change_value(self, new_val):
        self.value_changed.emit(new_val)  # Emittieren
```

**Beispiel aus `simulation_screen.py`:**
```python
self.btn_play = QPushButton("▶")
self.btn_play.clicked.connect(self.toggle_simulation)

# Slider mit Live-Update
temp_slider.valueChanged.connect(
    lambda v: self.temp_value_label.setText(f"Temp: {v} C°")
)
```

---

## Wichtige PyQt6-Komponenten

### QGraphicsView & QGraphicsScene
Für Custom-Zeichnung (2D-Grafiken, Animationen):

```python
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

class SimulationMapWidget(QGraphicsView):
    def __init__(self):
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setBackgroundBrush(QColor(255, 255, 255))
    
    def draw_groups(self, groups_data):
        """Zeichne Ellipsen für jede Gruppe."""
        self.scene.clear()
        for group in groups_data:
            color = QColor(int(color[0] * 255), int(color[1] * 255), ...)
            ellipse = self.scene.addEllipse(x, y, 3, 3, pen=QPen(color))
```

**Wichtige Methoden:**
- `scene.addEllipse()` - Ellipse zeichnen
- `scene.addRect()` - Rechteck zeichnen
- `scene.addLine()` - Linie zeichnen
- `scene.clear()` - Alles löschen
- `paintEvent()` - Custom Paint-Handler

---

### QTimer - Zeitgesteuerte Events
Für regelmäßige Updates (z.B. Simulation):

```python
from PyQt6.QtCore import QTimer

class SimulationScreen(QWidget):
    def toggle_simulation(self):
        if not self.is_running:
            self.is_running = True
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_simulation)
            self.update_timer.start(100)  # Alle 100ms
    
    def update_simulation(self):
        # Wird alle 100ms aufgerufen
        data = self.sim_model.step()
        self.map_widget.draw_groups(data["groups"])
        self.time_label.setText(f"Zeit: {data['time']}")
```

---

## Anwendungsablauf

### 1. **App-Start** (`frontend/main.py`)

```
main()
  ↓
QApplication erstellen
  ↓
ArachfaraApp (QMainWindow) erstellen
  ├─ StartScreen erstellen
  ├─ SimulationScreen erstellen
  ├─ Beide in QStackedWidget hinzufügen
  └─ Stylesheet anwenden
  ↓
window.show() (fullscreen)
  ↓
app.exec() (Event-Loop)
```

### 2. **StartScreen anzeigen**
```
ArachfaraApp.__init__()
  → self.stacked.setCurrentWidget(self.start_screen)
  → StartScreen.init_ui() wird aufgerufen
     ├─ Logo laden & anzeigen
     ├─ Buttons erstellen
     └─ Layout aufbauen
```

### 3. **Zu Simulation navigieren**
```
User klickt "Start Simulation"
  ↓
StartScreen.on_start_clicked()
  ↓
self.go_to_simulation() (callback)
  ↓
ArachfaraApp.go_to_simulation()
  ↓
self.stacked.setCurrentWidget(self.simulation_screen)
  → SimulationScreen.init_ui() wird aufgerufen
```

### 4. **Simulation starten**
```
User klickt Play-Button
  ↓
SimulationScreen.toggle_simulation()
  ↓
QTimer.start(100) // Alle 100ms
  ↓
Every 100ms:
  - sim_model.step() aufrufen
  - map_widget.draw_groups() aufrufen
  - UI aktualisieren
```

---

## Theme-System

### Farben definieren (`styles/color_presets.py`)

```python
DARK_RED = ColorPreset(
    name="Dark Red",
    colors={
        "bg_primary": "#2a2a2a",      # Haupthintergrund
        "bg_secondary": "#333333",     # Sekundär
        "accent_primary": "#cc0000",   # Rote Akzente
        "accent_light": "#ff3333",     # Hover
        "text_primary": "#ffffff",     # Text
        # ... weitere Farben
    }
)
```

### Stylesheet generieren (`styles/stylesheet.py`)

```python
def get_stylesheet(preset):
    c = preset.colors  # Shorthand
    return f"""
    QPushButton {{
        background-color: {c['button_bg']};
        border: 2px solid {c['accent_primary']};
        color: {c['text_primary']};
    }}
    """
```

### Theme auf Screens anwenden

```python
# main.py
self.start_screen = StartScreen(callback, self.color_preset)
self.setStyleSheet(get_stylesheet(self.color_preset))

# start_screen.py
bg_color = self.color_preset.get_color("bg_secondary")
center_container.setStyleSheet(f"background-color: {bg_color};")
```

**Neues Preset hinzufügen:**
```python
# 1. In color_presets.py definieren
DARK_ORANGE = ColorPreset(name="Dark Orange", colors={...})

# 2. Zu AVAILABLE_PRESETS hinzufügen
AVAILABLE_PRESETS = [..., DARK_ORANGE]

# 3. App mit Preset starten
main(preset_name="Dark Orange")
```

---

## Häufige Aufgaben

### Task 1: Neuen Button hinzufügen

```python
# In einer Screen-Klasse
btn_new = QPushButton("New Button")
btn_new.setFixedWidth(100)
btn_new.setFixedHeight(40)
btn_new.clicked.connect(self.on_new_button_clicked)
layout.addWidget(btn_new)

def on_new_button_clicked(self):
    print("Button wurde geklickt!")
```

### Task 2: Label dynamisch aktualisieren

```python
# Initialisierung
self.info_label = QLabel("Anfangswert")

# Update
self.info_label.setText(f"Neue Zeit: {time_step}")
```

### Task 3: Bedingte Styling

```python
# StyleSheet mit Bedingung
if some_condition:
    self.label.setStyleSheet("color: #ff3333;")  # Rot
else:
    self.label.setStyleSheet("color: #33ff33;")  # Grün
```

### Task 4: Neuen Screen hinzufügen

```python
# 1. Neue Klasse erstellen: screens/new_screen.py
class NewScreen(QWidget):
    def __init__(self, callback, color_preset=None):
        super().__init__()
        self.callback = callback
        self.color_preset = color_preset
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        # Widgets hinzufügen...
        self.setLayout(layout)

# 2. In main.py hinzufügen
self.new_screen = NewScreen(self.go_to_new, self.color_preset)
self.stacked.addWidget(self.new_screen)

# 3. Navigation hinzufügen
def go_to_new(self):
    self.stacked.setCurrentWidget(self.new_screen)
```

### Task 5: QTimer stoppen

```python
if self.update_timer:
    self.update_timer.stop()
    self.update_timer = None
self.is_running = False
```

---

## PyQt6 vs. andere Frameworks

| Feature | PyQt6 | Kivy | PySimpleGUI |
|---------|-------|------|-------------|
| Setup | Einfach | Mittel | Sehr einfach |
| Customization | Sehr hoch | Sehr hoch | Niedrig |
| Native Look | ✅ | ❌ | ✅ |
| Performance | Sehr gut | Gut | Befriedigend |
| Mobile | ❌ | ✅ | ❌ |
| Learning Curve | Mittel | Mittel | Flach |
| **Pixel-Art** | ✅✅✅ | ⚠️ (MD Design) | ✅ |

---

## Weitere Ressourcen

- **Offizielle PyQt6 Docs:** https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **Qt Designer (GUI Builder):** Tools für visuelles Layout-Design
- **QSS (Qt Style Sheets):** Wie CSS für Qt

---

## Zusammenfassung

**Wichtigste Konzepte zum Merken:**

1. ✅ **QMainWindow** = Hauptfenster
2. ✅ **QStackedWidget** = Screen-Navigation
3. ✅ **Layouts** = Responsive Design (QVBoxLayout, QHBoxLayout)
4. ✅ **Signals & Slots** = Event-Handling
5. ✅ **Stylesheets** = CSS-ähnliches Styling
6. ✅ **QGraphicsScene** = Custom-Zeichnung
7. ✅ **QTimer** = Zeitgesteuerte Events

Mit diesen Konzepten kannst du beliebige UI-Erweiterungen in ProjektAstras vornehmen! 🚀
