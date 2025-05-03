#!/bin/bash
source venv/bin/activate
pip install pyinstaller
pyinstaller --onefile stroboscope_generator.py
echo "The executable has been created in the dist folder."
deactivate
