#!/bin/bash
# This script compiles the Python script into a standalone executable using Nuitka.

# Check if the virtual environment directory exists
if [ ! -d "venv" ]; then
	echo "Error: The 'venv' directory does not exist. Please set up the virtual environment first."
	exit 1
fi

source venv/bin/activate
python -m nuitka MKStroboscopeDiscGeneratorGUI.py \
--standalone \
--onefile \
--enable-plugin=pyqt6 \
--output-dir=dist \
--enable-plugin=pyqt6 \
--include-module=svgwrite \
--include-module=svglib \
--include-module=tempfile \
--include-module=reportlab \
--include-package=reportlab \
--windows-disable-console \
--onefile

output_file="dist/MKStroboscopeDiscGeneratorGUI.bin"
echo "The executable '${output_file}' has been created."
