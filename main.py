import os

# Setzt Kivy-Logging auf 'warning' vor dem Import von Kivy/KivyMD,
# um überflüssige 'info'-Logs in der Konsole zu vermeiden.
os.environ["KIVY_LOG_LEVEL"] = "warning"

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.core.window import Window

# Setzen einer Standard-Fenstergröße für den Start
Window.size = (1024, 768)

# KV-String für das Layout, basierend auf ProjektAstras_Mockup.gif
KV = """
<MainLayout>:
    orientation: 'vertical'

    # 1. Top Bar (wie in der Skizze)
    MDTopAppBar:
        # Kein Titel, wie in der Skizze, nur Icons
        left_action_items: [['arrow-left', lambda x: app.on_back()]]
        right_action_items: [['close', lambda x: app.stop()]]

    # 2. Haupt-Content-Bereich (Horizontal geteilt)
    MDBoxLayout:
        orientation: 'horizontal'
        padding: '5dp'

        # 2a. Linke Seite: Simulations-Ansicht
        MDBoxLayout:
            md_bg_color: .3, .3, .3, 1 # Dunkler Hintergrund für den Viewport
            MDLabel:
                text: 'Simulations-Ansicht (Canvas)'
                halign: 'center'
                valign: 'center'

        # 2b. Rechte Seite: Control-Sidebar
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_x: None
            width: '280dp' # Feste Breite für die Sidebar
            padding: '10dp'
            spacing: '8dp'

            MDLabel:
                text: 'Region'
                font_style: 'H6'
                size_hint_y: None
                height: self.texture_size[1] # Höhe an Text anpassen

            MDSlider:
                id: temp_slider
                min: 0
                max: 40
                value: 20
                size_hint_y: None
                height: '48dp'
                on_value: app.update_temp_label(self.value)

            MDLabel:
                id: temp_label
                text: f'Temp: {int(temp_slider.value)}°C'
                size_hint_y: None
                height: self.texture_size[1]

            # Nahrung-Steuerung
            MDBoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: '48dp'
                spacing: '5dp'
                
                MDIconButton:
                    icon: 'arrow-left'
                    on_release: app.change_nahrung(-1)
                MDLabel:
                    id: nahrung_label
                    text: '3' # Startwert
                    halign: 'center'
                    valign: 'center'
                    size_hint_x: .4
                MDIconButton:
                    icon: 'arrow-right'
                    on_release: app.change_nahrung(1)
                MDLabel:
                    text: 'Nahrung'
                    valign: 'center'
                    size_hint_x: 1.2

            MDLabel:
                text: 'Tag — Nacht'
                halign: 'center'
                size_hint_y: None
                height: self.texture_size[1]
            
            # Simulations-Steuerung (Play, Pause, etc.)
            MDBoxLayout:
                orientation: 'horizontal'
                adaptive_height: True
                spacing: '5dp'
                pos_hint: {'center_x': .5}
                
                MDIconButton:
                    icon: 'rewind'
                    # on_release: app.set_speed('rewind')
                MDIconButton:
                    icon: 'play'
                    # on_release: app.set_speed('play')
                MDIconButton:
                    icon: 'pause'
                    # on_release: app.set_speed('pause')
                MDIconButton:
                    icon: 'stop'
                    # on_release: app.stop_simulation()
                MDIconButton:
                    icon: 'fast-forward'
                    # on_release: app.set_speed('fastforward')

            # Stats-Button und Laufzeit
            MDBoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: '36dp'
                spacing: '10dp'
                
                MDRaisedButton:
                    text: 'Stats'
                    # on_release: app.show_stats()
                MDLabel:
                    id: laufzeit_label
                    text: 'Laufzeit: 0.0s'
                    halign: 'right'
                    valign: 'center'
            
            # Spacer, um Elemente nach oben zu drücken
            Widget:
                size_hint_y: 1

    # 3. Untere Log-Leiste
    MDBoxLayout:
        size_hint_y: None
        height: '100dp'
        padding: '10dp'
        md_bg_color: .2, .2, .2, 1 # Dunkler Hintergrund für Logs
        
        ScrollView:
            MDLabel:
                id: log_label
                text: 'Logs:\\n' # Starttext für Logs
                size_hint_y: None
                height: self.texture_size[1]
                markup: True # Erlaubt einfaches Text-Styling
                color: 1, 1, 1, 1
"""


class MainLayout(MDBoxLayout):
    """Root-Widget, das das Hauptlayout enthält."""

    pass


class SimulationApp(MDApp):
    # Aktueller Wert für Nahrung, 1-5
    current_nahrung = 3

    def build(self):
        # Setzt das Theme basierend auf der Skizze (dunkel, rote Akzente)
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Red"
        # Lade das KV-String (registriert die <MainLayout> rule)
        Builder.load_string(KV)
        # Erstelle und gib die Root-Instanz zurück, so dass self.root gesetzt wird
        return MainLayout()

    def on_start(self):
        # Initialisiere die Labels beim Start
        self.root.ids.temp_label.text = (
            f"Temp: {int(self.root.ids.temp_slider.value)}°C"
        )
        self.root.ids.nahrung_label.text = str(self.current_nahrung)
        self.root.ids.log_label.text = (
            "[color=ff0000]Logs:[/color] Simulation initialisiert.\n"
        )

    def on_back(self):
        """Platzhalter für den 'Zurück'-Button."""
        self.root.ids.log_label.text += "Zurück-Button gedrückt.\n"
        print("Zurück-Button gedrückt")

    # --- Sidebar Logic Callbacks ---

    def update_temp_label(self, value):
        """Aktualisiert das Temperatur-Label, wenn der Slider bewegt wird."""
        self.root.ids.temp_label.text = f"Temp: {int(value)}°C"

    def change_nahrung(self, direction):
        """Ändert den 'Nahrung'-Wert (zwischen 1 und 5)."""
        new_value = self.current_nahrung + direction
        if 1 <= new_value <= 5:
            self.current_nahrung = new_value
            self.root.ids.nahrung_label.text = str(self.current_nahrung)
            self.root.ids.log_label.text += (
                f"Nahrung auf {self.current_nahrung} gesetzt.\n"
            )
        else:
            self.root.ids.log_label.text += (
                "[color=ffff00]Warnung:[/color] Nahrung-Limit (1-5) erreicht.\n"
            )


if __name__ == "__main__":
    SimulationApp().run()
