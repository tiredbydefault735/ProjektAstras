from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from frontend.i18n import _
from utils import get_static_path
from .custom_widgets import CustomImageButton


class ControlBar(QWidget):
    """
    Bottom control bar with Play/Pause, Stop, Time, Day/Night, Speed, Chaos labels and buttons.
    """

    playPauseClicked = pyqtSignal()
    stopClicked = pyqtSignal()
    speedChanged = pyqtSignal(int)  # 1, 2, 5
    chaosClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Play/Pause and Stop Buttons
        play_controls_layout = QHBoxLayout()
        self.btn_play_pause = QPushButton("▶")
        play_font = QFont("Minecraft", 16)
        play_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_play_pause.setFont(play_font)
        self.btn_play_pause.setFixedHeight(40)
        self.btn_play_pause.clicked.connect(self.playPauseClicked.emit)
        play_controls_layout.addWidget(self.btn_play_pause)

        self.btn_stop = QPushButton(_("Reset/Stop"))
        stop_font = QFont("Minecraft", 16)
        stop_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_stop.setFont(stop_font)
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.clicked.connect(self.stopClicked.emit)
        play_controls_layout.addWidget(self.btn_stop)
        play_controls_layout.addStretch()
        layout.addLayout(play_controls_layout)

        # Info display row with timer, day/night, and speed controls
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)

        # Timer display
        self.timer_label = QLabel("00:00")
        timer_font = QFont("Minecraft", 14)
        timer_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.timer_label.setFont(timer_font)
        self.timer_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(self.timer_label)

        # Day/Night indicator
        self.day_night_label = QLabel("☀️")
        day_night_font = QFont("Minecraft", 16)
        day_night_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.day_night_label.setFont(day_night_font)
        self.day_night_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(self.day_night_label)

        # Speed control buttons next to time
        speed_label = QLabel("Sim Speed:")
        speed_label_font = QFont("Minecraft", 9)
        speed_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        speed_label.setFont(speed_label_font)
        speed_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(speed_label)

        # Replace text speed buttons with image buttons from static/ui
        one_img = str(get_static_path("ui/one_times.png"))
        two_img = str(get_static_path("ui/two_times.png"))
        five_img = str(get_static_path("ui/five_times.png"))

        self.btn_speed_1x = CustomImageButton(one_img)
        self.btn_speed_1x.setChecked(True)
        self.btn_speed_1x.clicked.connect(lambda: self.speedChanged.emit(1))
        info_layout.addWidget(self.btn_speed_1x)

        self.btn_speed_2x = CustomImageButton(two_img)
        self.btn_speed_2x.clicked.connect(lambda: self.speedChanged.emit(2))
        info_layout.addWidget(self.btn_speed_2x)

        self.btn_speed_5x = CustomImageButton(five_img)
        self.btn_speed_5x.clicked.connect(lambda: self.speedChanged.emit(5))
        info_layout.addWidget(self.btn_speed_5x)

        # Chaos/Randomize Button
        self.btn_chaos = QPushButton("🎲")
        chaos_font = QFont("Segoe UI Emoji", 14)
        self.btn_chaos.setFont(chaos_font)
        self.btn_chaos.setFixedWidth(40)
        self.btn_chaos.setToolTip(_("Inject Randomness"))
        self.btn_chaos.clicked.connect(self.chaosClicked.emit)
        info_layout.addWidget(self.btn_chaos)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Live info row
        live_info_layout = QHBoxLayout()
        live_info_layout.setSpacing(10)

        # Temperature display (live)
        self.live_temp_label = QLabel("🌡️ 0°C")
        live_temp_font = QFont("Minecraft", 11)
        live_temp_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.live_temp_label.setFont(live_temp_font)
        self.live_temp_label.setStyleSheet("color: #88ccff;")
        live_info_layout.addWidget(self.live_temp_label)

        # Day/Night indicator (live)
        self.live_day_night_label = QLabel(_("☀️ Tag"))
        live_dn_font = QFont("Minecraft", 11)
        live_dn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.live_day_night_label.setFont(live_dn_font)
        self.live_day_night_label.setStyleSheet("color: #ffcc44;")
        live_info_layout.addWidget(self.live_day_night_label)
        live_info_layout.addStretch()
        layout.addLayout(live_info_layout)

    def set_running_state(self, is_running):
        if is_running:
            self.btn_play_pause.setText("⏸")
            self.btn_play_pause.setStyleSheet(
                "background-color: #4CAF50; color: white;"
            )
        else:
            self.btn_play_pause.setText("▶")
            self.btn_play_pause.setStyleSheet("")
            # Pause icon in label is handled by update logic if needed, or by parent.
            # But the requirement was "setText" so we do this.

    def update_speed_buttons(self, speed):
        self.btn_speed_1x.setChecked(speed == 1)
        self.btn_speed_2x.setChecked(speed == 2)
        self.btn_speed_5x.setChecked(speed == 5)

    def update_time(self, seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        self.timer_label.setText(f"{minutes:02d}:{secs:02d}")

    def update_day_night_icon(self, is_day):
        self.day_night_label.setText("☀️" if is_day else "🌙")

    def update_live_info(self, temp, is_day):
        temp_color = "#88ccff" if temp < 0 else "#ffcc44" if temp > 25 else "#ffffff"
        try:
            self.live_temp_label.setText(_("🌡️ {val}°C").format(val=temp))
        except:
            self.live_temp_label.setText(f"🌡️ {temp}°C")
        self.live_temp_label.setStyleSheet(f"color: {temp_color}; padding: 0 10px;")

        if is_day:
            self.live_day_night_label.setText(_("☀️ Tag"))
            self.live_day_night_label.setStyleSheet("color: #ffcc44; padding: 0 10px;")
        else:
            self.live_day_night_label.setText(_("🌙 Nacht"))
            self.live_day_night_label.setStyleSheet("color: #8888ff; padding: 0 10px;")

    def update_language(self):
        self.btn_stop.setText(_("Reset/Stop"))
        self.btn_chaos.setToolTip(_("Inject Randomness"))

        txt = self.live_day_night_label.text()
        if "☀️" in txt:
            self.live_day_night_label.setText(_("☀️ Tag"))
        elif "🌙" in txt:
            self.live_day_night_label.setText(_("🌙 Nacht"))
