from PyQt6.QtWidgets import QCheckBox, QPushButton
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class CustomCheckBox(QCheckBox):
    """Custom checkbox that draws image directly."""

    def __init__(self, text, unchecked_path, checked_path, parent=None):
        super().__init__(text, parent)
        self.unchecked_pixmap = QPixmap(unchecked_path)
        self.checked_pixmap = QPixmap(checked_path)

        # Scale pixmaps to 20x20 if needed
        if not self.unchecked_pixmap.isNull():
            self.unchecked_pixmap = self.unchecked_pixmap.scaled(
                20,
                20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        if not self.checked_pixmap.isNull():
            self.checked_pixmap = self.checked_pixmap.scaled(
                20,
                20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

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
        from PyQt6.QtGui import QPainter

        painter = QPainter(self)

        # Draw checkbox image at left position
        pixmap = self.checked_pixmap if self.isChecked() else self.unchecked_pixmap
        if not pixmap.isNull():
            painter.drawPixmap(0, (self.height() - 20) // 2, pixmap)

        painter.end()


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

    def paintEvent(self, event):
        super().paintEvent(event)
        from PyQt6.QtGui import QPainter

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
