#!/bin/bash

# Definir colores para los mensajes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Obtener el directorio donde se encuentra este script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_SCRIPT="$SCRIPT_DIR/MKStroboscopeDiscGeneratorGUI.py"

echo -e "${BLUE}=== MKStroboscopeDiscGeneratorGUI ===${NC}"
echo -e "${BLUE}Starting...${NC}"

# Verificar si Python está instalado
if ! command -v python3.13 &> /dev/null; then
    echo -e "${YELLOW}Python 3.13 not found, please install it and run this script again.${NC}"
    exit 1
fi

# Verificar si el script Python existe
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${YELLOW}The file MKStroboscopeDiscGeneratorGUI.py was not found in the current directory.${NC}"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Error while creating virtual environment. Please check that the python313-venv package is installed.${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}Using the current virtual environment...${NC}"
fi

# Activar el entorno virtual
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Verificar si la activación fue exitosa
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Error while activating virtual environment.${NC}"
    exit 1
fi

# Instalar dependencias
echo -e "${BLUE}Installing dependencies...${NC}"
pip install --upgrade pip
pip install PyQt6 svgwrite svglib reportlab nuitka

# Verificar si la instalación fue exitosa
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Error while installing dependencies.${NC}"
    deactivate
    exit 1
fi

# Ejecutar la aplicación
echo -e "${GREEN}Starting application...${NC}"
python "$PYTHON_SCRIPT"

# Desactivar el entorno virtual cuando la aplicación termina
echo -e "${BLUE}Closing application and deactivating virtual environment...${NC}"
deactivate

echo -e "${GREEN}The application has finished.${NC}"
