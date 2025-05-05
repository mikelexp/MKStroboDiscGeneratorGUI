#!/bin/bash

#source venv/bin/activate
#python -m nuitka --enable-plugin=pyqt6 --standalone --onefile stroboscope_generator.py
#python -m nuitka --standalone --onefile --include-data-dir=/usr/lib64/qt6/plugins=PyQt6/Qt6/plugins stroboscope_generator.py

venv/bin/python -m nuitka stroboscope_multi_rings_generator.py \
--standalone \
--enable-plugin=pyqt6 \
--include-module=svgwrite \
--include-module=svglib \
--include-module=reportlab \
--include-package=reportlab \
--include-module=tempfile \
--onefile

echo "The executable has been created in the current folder."
