from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

LOG_FONT_FAMILY = "Consolas"
LOG_FONT_SIZE = 12


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
            (QRegularExpression(r"(?i)verhungert"), fmt("#cc3333")),
            (QRegularExpression(r"(?i)Temperatur"), fmt("#99ddff")),
            (QRegularExpression(r"(?i)stirbt an Temperatur"), fmt("#ff9999")),
            (QRegularExpression(r"(?i)\bisst\b"), fmt("#cd853f")),
            (QRegularExpression(r"(?i)tritt.*bei"), fmt("#bb88ff")),
            (QRegularExpression(r"(?i)verlässt|verlassen"), fmt("#ff9944")),
            (QRegularExpression(r"(?i)tötet|stirbt|kampf"), fmt("#ff6666")),
            (QRegularExpression(r"(?i)Tag|Nacht"), fmt("#ffdd44")),
        ]

    def highlightBlock(self, text: str | None) -> None:
        if not text:
            return
        # Apply each regex rule to the provided text block
        for rx, fmt in self.rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                start = m.capturedStart()
                length = m.capturedLength()
                self.setFormat(start, length, fmt)
