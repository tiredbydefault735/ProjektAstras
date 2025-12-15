from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication
import sys

# PyQt6 requires QApplication to be created before using QFontDatabase
app = QApplication(sys.argv)

# In PyQt6, use static method directly
fonts = QFontDatabase.families()
for font in fonts:
    print(font)
