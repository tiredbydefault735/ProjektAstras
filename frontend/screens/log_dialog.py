from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPlainTextEdit, QPushButton
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from frontend.i18n import _
from .log_highlighter import LogHighlighter


class LogDialog(QDialog):
    """Popup dialog to display simulation logs."""

    def __init__(self, log_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Simulation Logs"))
        self.setModal(False)
        self.resize(600, 400)

        # Set dark theme
        self.setStyleSheet("background-color: #1a1a1a; color: #ffffff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel(_("Simulation Logs"))
        title_font = QFont("Minecraft", 14)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff; font-weight: bold;")
        layout.addWidget(title)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        text_font = QFont("Consolas", 12)
        text_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.text_edit.setFont(text_font)
        self.text_edit.setStyleSheet(
            "background-color: #2a2a2a; color: #ffffff; border: 1px solid #666666;"
        )
        self.text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.text_edit.setPlainText(log_text)
        LogHighlighter(self.text_edit.document())
        layout.addWidget(self.text_edit)

        close_btn = QPushButton(_("Schließen"))
        close_btn_font = QFont("Minecraft", 12)
        close_btn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        close_btn.setFont(close_btn_font)
        close_btn.setStyleSheet(
            "background-color: #444444; color: #ffffff; border: 2px solid #666666; padding: 5px;"
        )
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def update_log(self, log_text):
        if not log_text:
            self.text_edit.setPlainText("")
            return
        self.text_edit.setPlainText(log_text)
        self.text_edit.ensureCursorVisible()
