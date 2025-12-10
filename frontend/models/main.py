import os
import json
import sys
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivy.uix.screenmanager import NoTransition
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDRectangleFlatButton
from kivymd.uix.slider import MDSlider
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.selectioncontrol import MDSwitch, MDCheckbox
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse
from kivy.uix.image import Image
from kivy.lang import Builder
from kivy.properties import StringProperty
from random import randint
from kivy.metrics import dp
from pathlib import Path
from kivy.core.window import Window

# Add parent directory to path to import backend
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend import model

# --- HILFSKLASSEN (Map & Panels) ---


class SimulationMap(MDFloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [0.15, 0.15, 0.15, 1]

    def draw_arachfara(self, groups_data):
        self.canvas.after.clear()
        with self.canvas.after:
            for group in groups_data:
                if "color" in group:
                    Color(*group["color"])
                else:
                    Color(1, 1, 1, 1)

                draw_count = min(group["population"], 200)
                for _ in range(draw_count):
                    if self.width > 20 and self.height > 20:
                        relative_x = randint(10, int(self.width) - 10)
                        relative_y = randint(10, int(self.height) - 10)
                        Ellipse(
                            pos=(self.x + relative_x, self.y + relative_y), size=(6, 6)
                        )


class RegionPanel(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 20
        self.padding = 10

        self.add_widget(
            MDLabel(
                text="Umweltbedingungen",
                font_style="H6",
                size_hint_y=None,
                height=30,
                theme_text_color="Primary",
            )
        )

        self.add_widget(MDLabel(text="Temperatur: 20°C", theme_text_color="Secondary"))
        self.temp_slider = MDSlider(min=-50, max=50, value=20, color=[1, 0.2, 0.2, 1])
        self.add_widget(self.temp_slider)

        food_layout = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=50)
        food_layout.add_widget(MDIconButton(icon="arrow-left-bold"))
        food_layout.add_widget(MDLabel(text="Nahrung: Mittel", halign="center"))
        food_layout.add_widget(MDIconButton(icon="arrow-right-bold"))
        self.add_widget(food_layout)

        day_night_layout = MDBoxLayout(
            orientation="horizontal", size_hint_y=None, height=50
        )
        day_night_layout.add_widget(MDLabel(text="Tag"))
        day_night_layout.add_widget(MDSwitch(thumb_color_active=[1, 0.2, 0.2, 1]))
        day_night_layout.add_widget(MDLabel(text="Nacht", halign="right"))
        self.add_widget(day_night_layout)

        self.add_widget(MDLabel())


class SpeciesPanel(MDBoxLayout):
    def __init__(self, species_config, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 10
        self.padding = 10

        self.add_widget(
            MDLabel(
                text="Subspezies Konfiguration",
                font_style="H6",
                size_hint_y=None,
                height=40,
            )
        )

        scroll = MDScrollView()
        list_layout = MDBoxLayout(
            orientation="vertical", adaptive_height=True, spacing=20
        )

        for name, stats in species_config.items():
            row = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=5)

            header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=40)
            chk = MDCheckbox(
                size_hint=(None, None),
                size=(dp(40), dp(40)),
                active=True,
                selected_color=[1, 0.2, 0.2, 1],
            )
            lbl = MDLabel(text=name, bold=True, theme_text_color="Primary")
            header.add_widget(chk)
            header.add_widget(lbl)

            slider_box = MDBoxLayout(
                orientation="horizontal", size_hint_y=None, height=40
            )
            slider_lbl = MDLabel(
                text="Geschwindigkeit:",
                size_hint_x=0.4,
                font_style="Caption",
                theme_text_color="Secondary",
            )
            slider = MDSlider(
                min=0, max=10, value=5, size_hint_x=0.6, color=[1, 0.2, 0.2, 1]
            )
            slider_box.add_widget(slider_lbl)
            slider_box.add_widget(slider)

            row.add_widget(header)
            row.add_widget(slider_box)
            list_layout.add_widget(row)

        scroll.add_widget(list_layout)
        self.add_widget(scroll)


# --- SCREEN 1: STARTSEITE (OPTIMIERT) ---


class StartScreen(MDScreen):
    logo_path = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [0.1, 0.1, 0.1, 1]
        # expose logo path to kv
        logo_dir = Path(__file__).parent.parent.parent / "static" / "src"
        self.logo_path = str(logo_dir / "logo_astras_pix.png")

    def go_to_simulation(self, instance):
        # ensure transition is disabled before switching screens
        try:
            self.manager.transition = NoTransition()
        except Exception:
            pass
        self.manager.current = "first_screen"

    def close_app(self, instance):
        MDApp.get_running_app().stop()


# --- SCREEN 2: SIMULATION ---


class SimulationScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [0.1, 0.1, 0.1, 1]
        json_path = (
            Path(__file__).parent.parent.parent / "static" / "data" / "species.json"
        )
        try:
            with open(json_path, "r") as f:
                self.species_config = json.load(f)
        except FileNotFoundError:
            self.species_config = {}

        self.sim_model = model.SimulationModel()
        self.sim_model.setup(self.species_config, {})
        self.is_running = False

    def go_to_menu(self, instance):
        self.manager.transition.direction = "right"
        self.manager.current = "start"

    def close_app(self, instance):
        MDApp.get_running_app().stop()

    def switch_tab(self, tab_name):
        self.ids.sidebar_content.clear_widgets()
        if tab_name == "region":
            self.ids.btn_tab_region.md_bg_color = [0.8, 0.1, 0.1, 1]
            self.ids.btn_tab_species.md_bg_color = [0.25, 0.25, 0.25, 1]
            self.ids.sidebar_content.add_widget(RegionPanel())
        elif tab_name == "species":
            self.ids.btn_tab_species.md_bg_color = [0.8, 0.1, 0.1, 1]
            self.ids.btn_tab_region.md_bg_color = [0.25, 0.25, 0.25, 1]
            self.ids.sidebar_content.add_widget(SpeciesPanel(self.species_config))

    def toggle_simulation(self, instance):
        if not self.is_running:
            self.is_running = True
            self.ids.btn_play.icon = "pause"
            self.ids.log_label.text += "\n[color=33ff33]Info:[/color] Simulation läuft."
            Clock.schedule_interval(self.update_simulation, 0.1)
        else:
            self.is_running = False
            self.ids.btn_play.icon = "play"
            self.ids.log_label.text += "\n[color=ffff33]Info:[/color] Pausiert."
            Clock.unschedule(self.update_simulation)

    def update_simulation(self, dt):
        data = self.sim_model.step()
        self.ids.map_view.draw_arachfara(data["groups"])
        self.ids.time_label.text = f"Zeit: {data['time']}"


class ArachfaraApp(MDApp):
    def build(self):
        self.title = "Projekt Astras"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Red"
        # prefer maximize (keeps taskbar visible) which avoids some DPI fullscreen issues
        try:
            Window.maximize()
        except Exception:
            try:
                # fallback: set window size to current screen resolution
                sw, sh = Window.system_size
                Window.size = (sw, sh)
            except Exception:
                pass
        # load all kv layouts from frontend/views
        views_dir = Path(__file__).parent.parent / "views"
        if views_dir.exists():
            for kv in views_dir.glob("*.kv"):
                try:
                    Builder.load_file(str(kv))
                except Exception:
                    # continue loading other kv files even if one fails
                    pass

        sm = MDScreenManager()
        # disable transitions by default
        sm.transition = NoTransition()
        sm.add_widget(StartScreen(name="start_screen"))
        # register simulation screen under the name expected by navigation
        sm.add_widget(SimulationScreen(name="first_screen"))
        return sm


if __name__ == "__main__":
    ArachfaraApp().run()
