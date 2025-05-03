#!/bin/bash
source venv/bin/activate
pip install pyinstaller
python -m nuitka --enable-plugin=pyqt6 --standalone --onefile stroboscope_generator.py
echo "The executable has been created in the current folder."
deactivate
