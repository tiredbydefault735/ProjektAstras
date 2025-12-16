# ProjektAstras - Build-Anleitung

## Voraussetzungen

1. **Python installiert** (Version 3.8 oder höher)
2. **PyInstaller installieren**:
   ```powershell
   & "C:\Users\Sarah\AppData\Local\Programs\Python\Python312\python.exe" -m pip install pyinstaller
   ```

3. **Projektabhängigkeiten installieren**:
   ```powershell
   & "C:\Users\Sarah\AppData\Local\Programs\Python\Python312\python.exe" -m pip install PyQt6 simpy
   ```

## EXE erstellen

### Option 1: Mit dem Build-Skript (empfohlen)

```powershell
& "C:\Users\Sarah\AppData\Local\Programs\Python\Python312\python.exe" build_pyinstaller.py
```

### Option 2: Manueller Befehl

```powershell
& "C:\Users\Sarah\AppData\Local\Programs\Python\Python312\python.exe" -m PyInstaller --onefile --windowed --name ProjektAstras --add-data "static;static" --hidden-import backend --hidden-import backend.model --hidden-import utils frontend/main.py
```

## Ergebnis

Die fertige EXE befindet sich in: `dist\ProjektAstras.exe`

**Das ist alles was Sie brauchen!** Die EXE enthält:
- ✅ Python-Interpreter
- ✅ Alle Bibliotheken (PyQt6, simpy, etc.)
- ✅ Alle Python-Module
- ✅ Alle Ressourcen (species.json, Fonts, Bilder)

## Verteilung

Kopieren Sie einfach `dist\ProjektAstras.exe` auf einen USB-Stick oder verteilen Sie sie.

**Keine weiteren Dateien nötig!**

Die EXE läuft auf jedem Windows-PC:
- ✅ Kein Python erforderlich
- ✅ Keine Installation nötig
- ✅ Vollständig eigenständig

⚠️ **Einzige mögliche Anforderung:** Visual C++ Redistributables (meist bereits installiert)

## Troubleshooting

### Build schlägt fehl
```powershell
# Alte Builds löschen
Remove-Item -Path "dist", "build", "*.spec" -Recurse -Force

# Erneut versuchen
& "C:\Users\Sarah\AppData\Local\Programs\Python\Python312\python.exe" build_pyinstaller.py
```

### Debug-Version erstellen (um Fehler zu sehen)
```powershell
# Mit Console-Fenster (--console statt --windowed)
& "C:\Users\Sarah\AppData\Local\Programs\Python\Python312\python.exe" -m PyInstaller --onefile --console --name ProjektAstras_debug --add-data "static;static" --hidden-import backend --hidden-import backend.model --hidden-import utils frontend/main.py
```

### ImportError beim Start
```powershell
# Fügen Sie fehlende Module hinzu
--hidden-import modulname
```

## Technische Details

### Wie funktioniert es?

Die Anwendung verwendet `utils.py` für intelligente Pfaderkennung:
- **Entwicklungsmodus:** Ressourcen im Projekt-Ordner
- **PyInstaller EXE:** Ressourcen werden zur Laufzeit in `sys._MEIPASS` extrahiert

### Was passiert beim Start der EXE?

1. PyInstaller extrahiert Ressourcen in temporäres Verzeichnis
2. `utils.py` erkennt `sys._MEIPASS` und nutzt diesen Pfad
3. Anwendung lädt alle Ressourcen korrekt
4. Beim Schließen wird das temporäre Verzeichnis aufgeräumt

## Weitere Informationen

PyInstaller Dokumentation: https://pyinstaller.org/
