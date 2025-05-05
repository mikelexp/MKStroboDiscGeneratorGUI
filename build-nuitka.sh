#!/bin/bash
source venv/bin/activate
pip install pyinstaller
#python -m nuitka --enable-plugin=pyqt6 --standalone --onefile stroboscope_generator.py
python -m nuitka --standalone --onefile --include-data-dir=/usr/lib64/qt6/plugins=PyQt6/Qt6/plugins stroboscope_generator.py
echo "The executable has been created in the current folder."
deactivate
