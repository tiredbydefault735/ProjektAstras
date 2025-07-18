from __init__ import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Main Window")
        button = QPushButton("Click Me")

        self.setMinimumSize(QSize(400, 300))
        self.setMaximumSize(QSize(800, 600))
        self.setCentralWidget(button)


app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec_()
