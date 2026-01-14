from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtGui import QPixmap, QPainter


class CustomCheckBox(QCheckBox):
    """Custom checkbox that draws image directly."""

    def __init__(self, text, unchecked_path, checked_path, parent=None):
        super().__init__(text, parent)
        self.unchecked_pixmap = QPixmap(unchecked_path)
        self.checked_pixmap = QPixmap(checked_path)

        # Scale pixmaps to 20x20 if needed
        if not self.unchecked_pixmap.isNull():
            self.unchecked_pixmap = self.unchecked_pixmap.scaled(20, 20)
        if not self.checked_pixmap.isNull():
            self.checked_pixmap = self.checked_pixmap.scaled(20, 20)

        # Hide default indicator and add spacing for our custom image
        self.setStyleSheet(
            """
            QCheckBox {
                spacing: 30px;
            }
            QCheckBox::indicator {
                width: 0px;
                height: 0px;
            }
        """
        )
        self.setMinimumHeight(28)

    def paintEvent(self, a0):
        super().paintEvent(a0)

        painter = QPainter(self)

        # Draw checkbox image at left position
        pixmap = self.checked_pixmap if self.isChecked() else self.unchecked_pixmap
        if not pixmap.isNull():
            painter.drawPixmap(0, (self.height() - 20) // 2, pixmap)

        painter.end()


# Backwards-compatible alias: some modules import `CustomCheckbox` (lowercase b)
# while the class here is named `CustomCheckBox`. Provide alias to satisfy
# callers and linters without renaming the class.
CustomCheckbox = CustomCheckBox
