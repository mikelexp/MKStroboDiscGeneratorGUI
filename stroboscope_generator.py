import sys
import math
from PyQt6.QtWidgets import (
    QApplication,
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QDoubleSpinBox, QFileDialog, QGroupBox,
    QComboBox, QCheckBox, QRadioButton, QButtonGroup, QMessageBox
)

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtGui import QResizeEvent, QFont, QGuiApplication
import svgwrite
import tempfile
import os

# For PDF export
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

# Constants for sizes
SVG_MARGIN = 10  # mm margin in the SVG
PREVIEW_PANEL_MARGIN_WIDTH = 20  # mm margin in the preview panel, width
PREVIEW_PANEL_MARGIN_HEIGHT = 40  # mm margin in the preview panel, height
        
class StroboscopeGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stroboscopic Disc Generator")
        self.setMinimumSize(800, 600)
        self.svg_content=""
        self.temp_dir = tempfile.TemporaryDirectory()
        # Variables para almacenar los parámetros
        self.temp_svg_file = None # Temporary file to store the SVG
        self.num_lines=0
        
        # Timer to delay the preview update
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.generate_disc)
        
        # Apply a modest increase to the application's font
        self.apply_font_scaling()
        
        # Setup the user interface
        self.setup_ui()
        
    def apply_font_scaling(self):
        """Apply a modest increase to the application's font"""
        # Use a fixed and conservative scale factor
        self.scale_factor = 1.15  # 15% de aumento
        
        # Aplicar el escalado a la fuente predeterminada de la aplicación
        font = QApplication.font()
        font_size = font.pointSize()
        if font_size > 0:  # Si el tamaño de fuente es válido
            font.setPointSize(int(font_size * self.scale_factor))
            QApplication.setFont(font)
    
    def is_dark_theme(self):
        """Detect if the system is using a dark theme"""
        # Get the application palette
        palette = QGuiApplication.palette()
        # Get the window background color
        background_color = palette.color(palette.ColorRole.Window)
        # Calculate brightness (0-255), where lower values are darker
        brightness = (background_color.red() * 299 + background_color.green() * 587 + background_color.blue() * 114) / 1000
        # If brightness is less than 128, consider it a dark theme
        return brightness < 128
    
    def apply_font_to_widget(self, widget, size_increase=0):
        """Apply a font with a custom size to a specific widget"""
        font = widget.font()
        current_size = font.pointSize()
        if current_size > 0 and size_increase > 0:  # Solo aplicar aumento adicional si es necesario
            font.setPointSize(current_size + size_increase)
            widget.setFont(font)

    def schedule_preview_update(self):
        """Programa una actualización de la vista previa después de un breve retraso"""
        self.update_timer.start(300)  # 300ms de retraso para evitar actualizaciones excesivas
        
    def setup_ui(self):
        # Widget principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Apply style based on the system theme
        central_widget.setStyleSheet("""
            QPushButton {
                border: 2px solid #0078d7;
                border-radius: 10px;
                padding: 5px;
                background-color: rgba(0, 120, 215, 0.1);
            }
        """)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Controls Panel
        controls_panel = QWidget()
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Parameters Group
        params_group = QGroupBox("Disc Parameters")
        self.apply_font_to_widget(params_group, 1)  # Group title slightly larger
        params_layout = QVBoxLayout()
        
        # RPM - Now with dropdown and manual option
        rpm_layout = QVBoxLayout()
        rpm_label = QLabel("RPM:")
        
        # Layout for the RPM dropdown
        rpm_combo_layout = QHBoxLayout()
        self.rpm_combo = QComboBox()
        self.rpm_combo.addItems(["16", "33.33", "45", "78"])
        self.rpm_combo.setCurrentIndex(1)  # 33.33 by default
        self.rpm_combo.currentIndexChanged.connect(self.update_segments_info)
        self.rpm_combo.currentIndexChanged.connect(self.schedule_preview_update)  # Update preview
        rpm_combo_layout.addWidget(rpm_label)
        rpm_combo_layout.addWidget(self.rpm_combo)
        rpm_layout.addLayout(rpm_combo_layout)
        
        # Layout for manual RPM input
        rpm_manual_layout = QHBoxLayout()
        self.rpm_manual_check = QCheckBox("Enter RPM manually:")
        self.rpm_input = QDoubleSpinBox()
        self.rpm_input.setRange(1, 100)
        self.rpm_input.setValue(33.33)
        self.rpm_input.setDecimals(2)
        self.rpm_input.setEnabled(False)  # Disabled by default
        self.rpm_input.valueChanged.connect(self.update_segments_info)
        self.rpm_input.valueChanged.connect(self.schedule_preview_update)  # Update preview
        
        # Connect the checkbox to enable/disable manual input
        self.rpm_manual_check.stateChanged.connect(self.toggle_rpm_input)
        self.rpm_manual_check.stateChanged.connect(self.schedule_preview_update)  # Update preview
        
        rpm_manual_layout.addWidget(self.rpm_manual_check)
        rpm_manual_layout.addWidget(self.rpm_input)
        rpm_layout.addLayout(rpm_manual_layout)
        
        params_layout.addLayout(rpm_layout)
        
        # Frequency (Hz) - Now only 50 or 60
        hz_layout = QHBoxLayout()
        hz_label = QLabel("Frequency (Hz):")
        self.hz_combo = QComboBox()
        self.hz_combo.addItems(["50", "60"])
        self.hz_combo.currentIndexChanged.connect(self.update_segments_info)
        self.hz_combo.currentIndexChanged.connect(self.schedule_preview_update)  # Actualizar vista previa
        hz_layout.addWidget(hz_label)
        hz_layout.addWidget(self.hz_combo)
        params_layout.addLayout(hz_layout)

        # Diameter
        diameter_layout = QHBoxLayout()
        diameter_label = QLabel("Diameter (mm):")
        self.diameter_input = QSpinBox()
        self.diameter_input.setRange(50, 300)
        self.diameter_input.setValue(200)
        self.diameter_input.valueChanged.connect(self.update_segments_info)
        self.diameter_input.valueChanged.connect(self.schedule_preview_update)  # Actualizar vista previa
        diameter_layout.addWidget(diameter_label)
        diameter_layout.addWidget(self.diameter_input)
        params_layout.addLayout(diameter_layout)

        # Central hole diameter
        hole_diameter_layout = QHBoxLayout()
        hole_diameter_label = QLabel("Central Hole (mm):")
        self.hole_diameter_input = QDoubleSpinBox()
        self.hole_diameter_input.setRange(1, 20)
        self.hole_diameter_input.setValue(7)
        self.hole_diameter_input.setDecimals(1)
        self.hole_diameter_input.valueChanged.connect(self.schedule_preview_update)  # Update preview
        hole_diameter_layout.addWidget(hole_diameter_label)
        hole_diameter_layout.addWidget(self.hole_diameter_input)
        params_layout.addLayout(hole_diameter_layout)
        
        # Tamaño de las líneas (profundidad hacia el centro)
        line_size_layout = QHBoxLayout()
        line_size_label = QLabel("Line depth (mm):")
        self.line_size_input = QDoubleSpinBox()
        self.line_size_input.setRange(5, 50)
        self.line_size_input.setValue(10)
        self.line_size_input.setDecimals(1)
        self.line_size_input.valueChanged.connect(self.schedule_preview_update)  # Actualizar vista previa
        line_size_layout.addWidget(line_size_label)
        line_size_layout.addWidget(self.line_size_input)
        
        # Checkbox force single
        self.force_single_check = QCheckBox("Single mode")
        self.force_single_check.stateChanged.connect(self.update_segments_info)
        self.force_single_check.stateChanged.connect(self.schedule_preview_update)
        line_size_layout.addWidget(self.force_single_check)
        params_layout.addLayout(line_size_layout)

        # Optional outer circle
        outer_circle_layout = QVBoxLayout()
        self.outer_circle_check = QCheckBox("Show outer circle")
        self.outer_circle_check.setChecked(True)  # Enabled by default
        self.outer_circle_check.stateChanged.connect(self.schedule_preview_update)  # Update preview
        outer_circle_layout.addWidget(self.outer_circle_check)

        # Outer circle width
        outer_circle_width_layout = QHBoxLayout()
        outer_circle_width_label = QLabel("Outer circle width (mm):")
        self.outer_circle_width_input = QDoubleSpinBox()
        self.outer_circle_width_input.setRange(0.1, 5)
        self.outer_circle_width_input.setValue(0.5)
        self.outer_circle_width_input.setDecimals(2)
        self.outer_circle_width_input.valueChanged.connect(self.schedule_preview_update)  # Actualizar vista previa
        outer_circle_width_layout.addWidget(outer_circle_width_label)
        outer_circle_width_layout.addWidget(self.outer_circle_width_input)
        outer_circle_layout.addLayout(outer_circle_width_layout)

        # Connect the checkbox to enable/disable the circle width
        self.outer_circle_check.stateChanged.connect(
            lambda state: self.outer_circle_width_input.setEnabled(state == Qt.CheckState.Checked.value)
        )
        
        # Optional inner circle
        inner_circle_layout = QVBoxLayout()
        self.inner_circle_check = QCheckBox("Show inner circle")
        self.inner_circle_check.setChecked(True)  # Enabled by default
        self.inner_circle_check.stateChanged.connect(self.schedule_preview_update)  # Update preview
        inner_circle_layout.addWidget(self.inner_circle_check)

        # Inner circle width
        inner_circle_width_layout = QHBoxLayout()
        inner_circle_width_label = QLabel("Inner circle width (mm):")
        self.inner_circle_width_input = QDoubleSpinBox()
        self.inner_circle_width_input.setRange(0.1, 5)
        self.inner_circle_width_input.setValue(0.2)
        self.inner_circle_width_input.setDecimals(2)
        self.inner_circle_width_input.valueChanged.connect(self.schedule_preview_update)  # Actualizar vista previa
        inner_circle_width_layout.addWidget(inner_circle_width_label)
        inner_circle_width_layout.addWidget(self.inner_circle_width_input)
        inner_circle_layout.addLayout(inner_circle_width_layout)
        
        # Conectar el checkbox para habilitar/deshabilitar el ancho del círculo
        self.inner_circle_check.stateChanged.connect(
            lambda state: self.inner_circle_width_input.setEnabled(state == Qt.CheckState.Checked.value))
        
        params_layout.addLayout(inner_circle_layout)

        params_layout.addLayout(outer_circle_layout)
        
        params_group.setLayout(params_layout)
        controls_layout.addWidget(params_group)

        # Calculated Information
        info_group = QGroupBox("Calculated Information")
        self.apply_font_to_widget(info_group, 1)  # Group title slightly larger
        info_layout = QVBoxLayout()
        
        self.segments_label = QLabel("Number of segments: -")
        info_layout.addWidget(self.segments_label)
        
        self.line_width_label = QLabel("Line width: -")
        info_layout.addWidget(self.line_width_label)

        self.information_label = QLabel("Information: -")
        info_layout.addWidget(self.information_label)
        
        info_group.setLayout(info_layout)
        controls_layout.addWidget(info_group)
        
        # Buttons
        buttons_layout = QVBoxLayout()
        
        # Generate Disc button
        self.generate_button = QPushButton("Update Preview")
        self.apply_font_to_widget(self.generate_button, 1)        
        self.generate_button.setToolTip("The preview is updated automatically, but you can force an update with this button")
        buttons_layout.addWidget(self.generate_button)
        
        # Export format
        export_format_layout = QHBoxLayout()
        export_format_label = QLabel("Export format:")
        self.format_group = QButtonGroup()
        self.svg_radio = QRadioButton("SVG")
        self.pdf_radio = QRadioButton("PDF")
        self.svg_radio.setChecked(True)  # SVG by default
        self.format_group.addButton(self.svg_radio)
        self.format_group.addButton(self.pdf_radio)
        
        export_format_layout.addWidget(export_format_label)
        export_format_layout.addWidget(self.svg_radio)
        export_format_layout.addWidget(self.pdf_radio)
        buttons_layout.addLayout(export_format_layout)        
        
        self.export_button = QPushButton("Export")
        self.generate_button.clicked.connect(self.generate_disc)
        self.apply_font_to_widget(self.export_button, 1)  # Botones ligeramente más grandes
        self.export_button.clicked.connect(self.export_file)

        self.export_button.setEnabled(False)        
        buttons_layout.addWidget(self.export_button)
        
        controls_layout.addLayout(buttons_layout)
        
        # Add control panel to main layout
        main_layout.addWidget(controls_panel, 1)
        
        # Preview panel
        self.preview_panel = QWidget()
        preview_layout = QVBoxLayout(self.preview_panel)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Container for the SVG that takes up all available width
        self.svg_widget = QSvgWidget()
        self.svg_widget.setMinimumSize(QSize(300, 300))
        preview_layout.addWidget(self.svg_widget, 1, Qt.AlignmentFlag.AlignCenter)
        
        # Add preview panel to main layout
        main_layout.addWidget(self.preview_panel, 2)
        
        # Update segment information at startup
        self.update_segments_info()
        
        # Generate initial preview
        QTimer.singleShot(100, self.generate_disc)
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Adjust the size of the SVG when the window is resized"""
        super().resizeEvent(event)
        self.adjust_svg_size()
    
    def adjust_svg_size(self):
        """Adjust the size of the SVG widget to occupy the maximum available space"""
        if hasattr(self, 'svg_widget') and hasattr(self, 'preview_panel'):
            # Obtener el ancho disponible en el panel de vista previa
            available_width = self.preview_panel.width() - PREVIEW_PANEL_MARGIN_WIDTH  # Margen
            available_height = self.preview_panel.height() - PREVIEW_PANEL_MARGIN_HEIGHT  # Margen y espacio para el título
            
            # Usar el valor más pequeño para mantener un aspecto cuadrado
            size = min(available_width, available_height)
            
            # Establecer el tamaño del widget SVG
            self.svg_widget.setFixedSize(QSize(size, size))
    
    def toggle_rpm_input(self, state):
        """Enables or disables manual RPM input"""
        is_checked = state == Qt.CheckState.Checked.value
        self.rpm_input.setEnabled(is_checked)
        self.rpm_combo.setEnabled(not is_checked)
        self.update_segments_info()
        
    def get_rpm_value(self):
        """Gets the RPM value according to the configuration"""
        if self.rpm_manual_check.isChecked():
            return self.rpm_input.value()
        else:
            return float(self.rpm_combo.currentText())
    
    def lines_to_rpm(self,num_lines, frequency):
        """Calculates the RPM given the number of lines and the frequency"""
        rpm = (120 * frequency) / num_lines
        return round(rpm, 3)
    
    def calculate_segments_and_line_width(self):
        """Calculate the number of lines, width of lines and rpm"""
        rpm = self.get_rpm_value() #get the right rpm value.        
        hz = float(self.hz_combo.currentText()) #get the frequency
        diameter = self.diameter_input.value() #get the diameter
        
        # Calcular el número de líneas exacto
        num_lines_exact = (60 * hz) / rpm * 2

        # Calcular el número de líneas inferior y superior
        num_lines_floor = math.floor(num_lines_exact)
        num_lines_floor_rpm = self.lines_to_rpm(num_lines_floor, hz)
        num_lines_ceil = math.ceil(num_lines_exact)
        num_lines_ceil_rpm = self.lines_to_rpm(num_lines_ceil, hz)

        num_lines_rpm = 0
        
        # Verificar si el número de líneas es un entero o si se fuerza a usar solo un juego de lineas
        if num_lines_floor == num_lines_ceil or self.force_single_check.isChecked():
            if (num_lines_floor == num_lines_ceil):
                num_lines = num_lines_floor
            else:
                num_lines = round(num_lines_exact)
            num_lines_rpm = self.lines_to_rpm(num_lines, hz)
        else:
            num_lines=0 #it will be used to draw the 2 sets of lines.
        radius=diameter/2
        segment_width = (2 * math.pi * radius) / max(num_lines, 1)
        line_width = segment_width / 2
        return num_lines_exact,num_lines,num_lines_rpm,line_width,num_lines_floor,num_lines_ceil,num_lines_floor_rpm,num_lines_ceil_rpm

    def update_segments_info(self):
        """Updates information about the number of segments and line width"""
        num_lines_exact,num_lines,num_lines_rpm,line_width,num_lines_floor,num_lines_ceil,num_lines_floor_rpm,num_lines_ceil_rpm=self.calculate_segments_and_line_width()
        if num_lines_floor == num_lines_ceil or self.force_single_check.isChecked():
            output_text = [
                f"Ideal: {round(num_lines_exact, 3)} lines)",
                f"Created: {num_lines} ({num_lines_rpm} rpm) lines",
            ]
        else:           
            output_text = [
                f"Ideal: {round(num_lines_exact, 3)} lines",
                f"Inner: {num_lines_ceil_rpm} rpm ({num_lines_ceil} lines)",
                f"Outer: {num_lines_floor_rpm} rpm ({num_lines_floor} lines)",
            ]
        self.information_label.setText("\n".join(output_text))
        self.line_width_label.setText(f"Line width: {line_width:.2f} mm")
        
    def generate_disc(self):
        """Generates the stroboscopic disc SVG."""
        # --- 1. Retrieve Input Parameters ---
        rpm = self.get_rpm_value()
        hz = float(self.hz_combo.currentText())
        diameter = self.diameter_input.value()
        hole_diameter = self.hole_diameter_input.value()
        line_depth = self.line_size_input.value()
        inner_circle_width = self.inner_circle_width_input.value()
        outer_circle_width = self.outer_circle_width_input.value()
        
        # --- 2. Calculate Derived Values ---
        num_lines_exact, num_lines, num_lines_rpm, line_width, num_lines_floor, num_lines_ceil, num_lines_floor_rpm, num_lines_ceil_rpm = self.calculate_segments_and_line_width()

        # Update segments label
        self.segments_label.setText(f"Number of segments: {num_lines if (num_lines_floor == num_lines_ceil or self.force_single_check.isChecked()) else f'{num_lines_floor}/{num_lines_ceil}'}")
        
        # Basic calculations
        radius = diameter / 2  # Radius of the disc
        
        # Calculate inner radius (where the inner side of the lines will be)
        # The inner radius starts from the inner edge of the outer lines.
        inner_radius = radius - line_depth
        
        # If there is an inner circle, calculate the inner circle radius and the lines inner radius
        # inner_circle_radius_single: It represents the radius of the inner circle for single lines.
        # inner_circle_radius_ceil: It represents the radius of the inner circle for the upper set of lines (double mode)
        # inner_circle_radius_floor: It represents the radius of the inner circle for the lower set of lines (double mode)
        # lines_inner_radius: It represents the inner point of the lines.
        
        #Determine if single or double lines
        is_single_line = num_lines_floor == num_lines_ceil or self.force_single_check.isChecked()        
        if is_single_line:
            inner_circle_radius_single = inner_radius
            lines_inner_radius = inner_circle_radius_single - inner_circle_width / 2 if self.inner_circle_check.isChecked() else inner_radius
            line_width= (2 * math.pi * radius) / max(num_lines, 1) /2 #calculates line_width
        else:
            inner_circle_radius_floor = inner_radius - inner_circle_width / 2 if self.inner_circle_check.isChecked() else inner_radius            
            inner_circle_radius_ceil = inner_radius - line_depth

            lines_inner_radius = inner_radius
            line_width_floor = (2 * math.pi * radius) / max(num_lines_floor, 1) /2 #calculates line_width
            line_width_ceil= (2 * math.pi * inner_radius) / max(num_lines_ceil, 1) /2

        
        
        if not is_single_line and self.inner_circle_check.isChecked():
            lines_inner_radius = inner_circle_radius_floor + inner_circle_width /2
        
        # --- 3. Setup SVG Drawing ---
        self.temp_svg_file = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
        self.temp_svg_file.close()

        svg_size = diameter + SVG_MARGIN  # Add a margin around the disc
        dwg = svgwrite.Drawing(
            self.temp_svg_file.name,
            size=(f"{svg_size}mm", f"{svg_size}mm"),
            profile="tiny",
            viewBox=f"0 0 {svg_size} {svg_size}",
        )
        center = (svg_size / 2, svg_size / 2)

        # --- 4. Draw Outer Circle (if enabled) ---
        if self.outer_circle_check.isChecked():
            dwg.add(dwg.circle(center=center, r=radius, fill='none', stroke='black', stroke_width=outer_circle_width))

        # --- 5. Draw Inner Circles (if enabled) ---
        if self.inner_circle_check.isChecked(): 
            if is_single_line:
                dwg.add(dwg.circle(center=center, r=inner_circle_radius_single, fill='none', stroke='black', stroke_width=inner_circle_width))
            else:
                # Draw inner circles for each set of lines

                dwg.add(dwg.circle(center=center, r=inner_circle_radius_ceil, fill='none', stroke='black', stroke_width=inner_circle_width))
                dwg.add(dwg.circle(center=center, r=inner_circle_radius_floor, fill='none', stroke='black', stroke_width=inner_circle_width))


        # --- 6. Draw Lines (Single or Double Set) ---
        if is_single_line:
            # --- 6.1 Draw Single Set of Lines ---
            num_lines = num_lines_floor if num_lines_floor == num_lines_ceil else round(num_lines_exact)
            angle_increment = 360 / max(num_lines, 1)  # Degrees between each line
            
            for i in range(num_lines):
                angle = math.radians(i * angle_increment)
                # Outer endpoint of the line (x1, y1)
                x1 = center[0] + radius * math.sin(angle)
                y1 = center[1] - (radius * math.cos(angle))
                
                # Inner endpoint of the line (x2, y2)
                if self.inner_circle_check.isChecked() and is_single_line:
                    x2 = center[0] + ((inner_radius - inner_circle_width) * math.sin(angle))
                elif self.inner_circle_check.isChecked():
                    x2 = center[0] + ((lines_inner_radius - inner_circle_width/2) * math.sin(angle))
                else:
                    x2 = center[0] + (lines_inner_radius * math.sin(angle))

                y2 = center[1] - (lines_inner_radius * math.cos(angle))
                
                
                dwg.add(dwg.line((x1, y1), (x2, y2), stroke=svgwrite.rgb(0, 0, 0, "%"), stroke_width=line_width))
        else:
            # --- 6.2 Draw Double Set of Lines ---
            # Draw the first set of lines (number of lines is num_lines_floor)
            angle_increment_floor = 360 / num_lines_floor

            for i in range(num_lines_floor):
                angle = math.radians(i * angle_increment_floor) # Convert angle to radians
                
                # Outer endpoint of the line (x1, y1)
                x1 = center[0] + radius * math.sin(angle)
                y1 = center[1] - (radius * math.cos(angle))
                
                # Inner endpoint of the line (x2, y2)                
                if self.inner_circle_check.isChecked():
                    x2 = center[0] + ((lines_inner_radius - inner_circle_width/2) * math.sin(angle))
                else:
                    x2 = center[0] + (lines_inner_radius * math.sin(angle))
                y2 = center[1] - (lines_inner_radius * math.cos(angle))                
                
                dwg.add(dwg.line((x1, y1), (x2, y2), stroke=svgwrite.rgb(0, 0, 0, "%"), stroke_width=line_width_floor))

            # Draw the second set of lines (number of lines is num_lines_ceil)
            angle_increment_ceil = 360 / num_lines_ceil

            for i in range(num_lines_ceil):
                angle = math.radians(i * angle_increment_ceil)# Convert angle to radians
                
                # Outer endpoint of the line (x1, y1)
                x1 = center[0] + inner_radius * math.sin(angle)
                y1 = center[1] - (inner_radius * math.cos(angle))
                #if self.inner_circle_check.isChecked():
                #    x1 = center[0] + ((inner_radius - inner_circle_width) * math.sin(angle))
                #    y1 = center[1] - ((inner_radius - inner_circle_width) * math.cos(angle))
                
                # Inner endpoint of the line (x2, y2)
                x2 = center[0] + ((inner_radius - line_depth) * math.sin(angle))
                y2 = center[1] - ((inner_radius - line_depth) * math.cos(angle))                

                dwg.add(dwg.line((x1, y1), (x2, y2), stroke=svgwrite.rgb(0, 0, 0, '%'), stroke_width=line_width_ceil))

        # --- 7. Create texts for label ---
        if is_single_line:
            output_text = [
                f"Ideal: {round(num_lines_exact, 3)} lines",
                f"{num_lines} ({num_lines_rpm} rpm) lines",
            ]
        else:
            output_text = [
                f"Ideal: {round(num_lines_exact, 3)} lines",
                f"Inside: {num_lines_ceil_rpm} rpm ({num_lines_ceil} lines)",
                f"Outside: {num_lines_floor_rpm} rpm ({num_lines_floor} lines)"
            ]
        self.information_label.setText("\n".join(output_text))

        # --- 8. Draw Center Hole ---
        dwg.add(dwg.circle(center=center, r=hole_diameter/2, fill='black', stroke='black', stroke_width=0.2))

        # --- 9. Save and Display ---
        dwg.save()
        self.svg_widget.load(self.temp_svg_file.name)
        self.adjust_svg_size()
        self.export_button.setEnabled(True)
    
    def export_file(self):
        try:
            if not self.temp_svg_file:
                QMessageBox.warning(self, "Error", "There is no generated disc to export.")
                return
            
            # Determine the file format according to the selection
            if self.svg_radio.isChecked():
                file_filter = "SVG Files (*.svg)"
                default_ext = ".svg"
            else:  # PDF seleccionado
                file_filter = "PDF Files (*.pdf)"
                default_ext = ".pdf"                
                
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Stroboscopic Disc", "", file_filter
            )
            
            if not file_path:
                return

            # If the user did not add the extension, add it
            if not file_path.endswith(default_ext):
                file_path += default_ext

            # Check if the file already exists
            if os.path.exists(file_path):
                reply = QMessageBox.question(
                    self, "Confirmation", f"'{file_path}' already exists. Do you want to overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return  # Do not overwrite

            if self.svg_radio.isChecked():
                
                # Guardar como SVG (copiar el archivo temporal)
                with open(self.temp_svg_file.name, 'r') as src, open(file_path, 'w') as dst:
                    dst.write(src.read())
            else:
                # Guardar como PDF (convertir SVG a PDF)
                drawing = svg2rlg(self.temp_svg_file.name)
                renderPDF.drawToFile(drawing, file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving file: {e}")    

    def closeEvent(self, event):
        self.temp_dir.cleanup()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StroboscopeGenerator()
    window.show()
    sys.exit(app.exec())
