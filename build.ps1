# This script compiles the Python script into a standalone executable using Nuitka in Windows PowerShell.

# Check if the virtual environment directory exists
if (-Not (Test-Path "venv")) {
    Write-Error "Error: The 'venv' directory does not exist. Please set up the virtual environment first."
    exit 1
}

# Activate the virtual environment
& "venv\Scripts\Activate.ps1"

# Run Nuitka to compile the script
python -m nuitka MKStroboscopeDiscGeneratorGUI.py `
    --standalone `
    --onefile `
    --enable-plugin=pyqt6 `
    --output-dir=dist `
    --include-module=svgwrite `
    --include-module=svglib `
    --include-module=tempfile `
    --include-module=reportlab `
    --include-package=reportlab `
    --windows-console-mode=disable

$output_file = "dist\MKStroboscopeDiscGeneratorGUI.exe"
Write-Output "The executable '$output_file' has been created."
