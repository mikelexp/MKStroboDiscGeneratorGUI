#!/bin/bash

# Definir colores para los mensajes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Obtener el directorio donde se encuentra este script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_SCRIPT="$SCRIPT_DIR/stroboscope_multi_rings_generator.py"

echo -e "${BLUE}=== Generador de Discos Estroboscópicos ===${NC}"
echo -e "${BLUE}Iniciando configuración...${NC}"

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 no está instalado. Por favor, instálalo antes de continuar.${NC}"
    exit 1
fi

# Verificar si el script Python existe
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${YELLOW}No se encontró el archivo stroboscope_multi_rings_generator.py en el directorio actual.${NC}"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}Creando entorno virtual...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Error al crear el entorno virtual. Verifica que el paquete python3-venv esté instalado.${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}Usando entorno virtual existente...${NC}"
fi

# Activar el entorno virtual
echo -e "${BLUE}Activando entorno virtual...${NC}"
source "$VENV_DIR/bin/activate"

# Verificar si la activación fue exitosa
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Error al activar el entorno virtual.${NC}"
    exit 1
fi

# Instalar dependencias
echo -e "${BLUE}Instalando dependencias...${NC}"
pip install --upgrade pip
pip install PyQt6 svgwrite svglib reportlab

# Verificar si la instalación fue exitosa
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Error al instalar las dependencias.${NC}"
    deactivate
    exit 1
fi

# Ejecutar la aplicación
echo -e "${GREEN}Iniciando la aplicación...${NC}"
python "$PYTHON_SCRIPT"

# Desactivar el entorno virtual cuando la aplicación termina
echo -e "${BLUE}Cerrando la aplicación y desactivando el entorno virtual...${NC}"
deactivate

echo -e "${GREEN}¡Listo! La aplicación ha finalizado.${NC}"
