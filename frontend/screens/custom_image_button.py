from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import Qt


class CustomImageButton(QPushButton):
    """Button that draws a centered image; supports checked state with optional alternate image."""

    def __init__(self, image_path, checked_image_path=None, parent=None, size=36):
        super().__init__(parent)
        self.pixmap = QPixmap(image_path)
        self.checked_pixmap = (
            QPixmap(checked_image_path) if checked_image_path else None
        )
        self.setCheckable(True)
        self.setFixedSize(size, size)
        self.setStyleSheet("border: none; background: transparent;")

    def paintEvent(self, a0):
        super().paintEvent(a0)
        painter = QPainter(self)
        pix = (
            self.checked_pixmap
            if (self.isChecked() and self.checked_pixmap)
            else self.pixmap
        )
        if not pix.isNull():
            scaled = pix.scaled(
                max(4, self.width() - 8),
                max(4, self.height() - 8),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        painter.end()
