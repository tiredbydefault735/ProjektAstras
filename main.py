from __init__ import *


# Button
class RoundedButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setFixedSize(160, 80)
        self.setStyleSheet(
            """
            QPushButton {
                border: 2px solid #444;
                border-radius: 20px;
                background-color: #5c4033;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7b5e45;
            }
        """
        )


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fullscreen Layout")

        # Image placeholder
        label = QLabel(self)
        pixmap = QPixmap("assets/Logo.png")
        scaled_pixmap = pixmap.scaled(
            400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignCenter)

        # Vertical stack of buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(40)
        for i in range(3):
            btn = RoundedButton(f"Button {i+1}")
            button_layout.addWidget(btn)
        button_layout.addStretch()

        # Wrap image in its own layout (optional for spacing)
        image_layout = QVBoxLayout()
        image_layout.addWidget(label)
        image_layout.addStretch()

        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(60, 60, 60, 60)
        main_layout.addLayout(image_layout)  # ✅ Add image layout
        main_layout.addLayout(button_layout)  # ✅ Add button layout

        self.setLayout(main_layout)

        self._createMenuBar

    def _createMenuBar(self):
        menuBar = self.menuBar()
        # Creating menus using a QMenu object
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)
        # Creating menus using a title
        editMenu = menuBar.addMenu("&Edit")
        helpMenu = menuBar.addMenu("&Help")
        menubar = self.menuBar()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    app.exec_()
