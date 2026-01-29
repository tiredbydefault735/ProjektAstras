import logging
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
)
from PyQt6.QtGui import (
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
)
from PyQt6.QtCore import Qt, QRegularExpression

from frontend.i18n import _
from config import (
    LOG_FONT_FAMILY,
    LOG_FONT_SIZE,
    LOG_COLOR_DEATH,
    LOG_COLOR_COLD,
    LOG_COLOR_COLD_DEATH,
    LOG_COLOR_EAT,
    LOG_COLOR_JOIN,
    LOG_COLOR_LEAVE,
    LOG_COLOR_COMBAT,
    LOG_COLOR_TEMP,
    LOG_COLOR_DAY,
    LOG_COLOR_NIGHT,
)


class LogHighlighter(QSyntaxHighlighter):
    """Simple syntax highlighter for log colorization using regex rules."""

    def __init__(self, document):
        super().__init__(document)

        def fmt(color_hex, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color_hex))
            f.setFontFamily(LOG_FONT_FAMILY)
            f.setFontPointSize(LOG_FONT_SIZE)
            if bold:
                f.setFontWeight(QFont.Weight.Bold)
            return f

        # Use inline (?i) for case-insensitive matching to avoid enum differences
        self.rules = [
            (QRegularExpression(r"(?i)☠️.*verhungert.*"), fmt(LOG_COLOR_DEATH)),
            (QRegularExpression(r"(?i)❄️.*Temperatur.*"), fmt(LOG_COLOR_COLD)),
            (
                QRegularExpression(r"(?i)stirbt an Temperatur"),
                fmt(LOG_COLOR_COLD_DEATH),
            ),
            (QRegularExpression(r"(?i)🍽️|🍖|\bisst\b"), fmt(LOG_COLOR_EAT)),
            (QRegularExpression(r"(?i)👥.*tritt.*bei"), fmt(LOG_COLOR_JOIN)),
            (QRegularExpression(r"(?i)verlässt|verlassen"), fmt(LOG_COLOR_LEAVE)),
            (QRegularExpression(r"(?i)⚔️|💀"), fmt(LOG_COLOR_COMBAT)),
            (QRegularExpression(r"(?i)🌡️"), fmt(LOG_COLOR_TEMP)),
            (QRegularExpression(r"(?i)☀️"), fmt(LOG_COLOR_DAY)),
            (QRegularExpression(r"(?i)🌙"), fmt(LOG_COLOR_NIGHT)),
        ]

    def highlightBlock(self, text: str | None) -> None:
        if not text:
            return
        for rx, fmt in self.rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                start = m.capturedStart()
                length = m.capturedLength()
                self.setFormat(start, length, fmt)


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

        # Title
        title = QLabel(_("Simulation Logs"))
        title_font = QFont("Minecraft", 14)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff; font-weight: bold;")
        layout.addWidget(title)

        # Text area with scroll (use QPlainTextEdit for performance)
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        text_font = QFont(LOG_FONT_FAMILY, LOG_FONT_SIZE)
        text_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.text_edit.setFont(text_font)
        self.text_edit.setStyleSheet(
            f"background-color: #2a2a2a; color: #ffffff; border: 1px solid #666666; font-family: {LOG_FONT_FAMILY}; font-size: {LOG_FONT_SIZE}px;"
        )
        # Enable word wrapping and scrolling
        self.text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # Populate plain text and attach highlighter for colorization
        self.text_edit.setPlainText(log_text)
        LogHighlighter(self.text_edit.document())
        layout.addWidget(self.text_edit)

        # Close button
        close_btn = QPushButton(_("Schließen"))
        close_btn_font = QFont("Minecraft", 12)
        close_btn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        close_btn.setFont(close_btn_font)
        close_btn.setStyleSheet(
            "background-color: #444444; color: #ffffff; "
            "border: 2px solid #666666; padding: 5px;"
        )
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def colorize_logs(self, log_text):
        """Return plain log text. Coloring is handled by QSyntaxHighlighter."""
        if not log_text:
            return ""

        # Keep as plain text; LogHighlighter applies formats to the document.
        return log_text

    def update_log(self, log_text):
        """Update the log text in the dialog."""
        scrollbar = self.text_edit.verticalScrollBar()
        was_at_bottom = False
        if scrollbar is not None:
            was_at_bottom = (
                scrollbar.value() >= scrollbar.maximum() - 10
            )  # 10px threshold

        # Replace plain text; highlighter will reformat visually
        self.text_edit.setPlainText(self.colorize_logs(log_text))

        # Force scrollbar update
        self.text_edit.ensureCursorVisible()

        # Only auto-scroll if user was already at the bottom
        if scrollbar is not None and was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
