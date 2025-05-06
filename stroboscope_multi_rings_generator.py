import sys
import math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSpinBox, QDoubleSpinBox, QFileDialog, QGroupBox,
    QComboBox, QCheckBox, QRadioButton, QButtonGroup, QMessageBox,
    QFrame
)

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtGui import QResizeEvent, QGuiApplication
import svgwrite
import tempfile
import os

# For PDF export
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import A4, LETTER, LEGAL, A3
from reportlab.lib.units import mm

# Constants for sizes
PREVIEW_PANEL_MARGIN_WIDTH = 20  # mm margin in the preview panel, width
PREVIEW_PANEL_MARGIN_HEIGHT = 20  # mm margin in the preview panel, height

class RingSettings(QWidget):
    # Widget for configuring a single ring of lines
    def __init__(self, parent=None, index=0, on_delete=None, on_change=None):
        super().__init__(parent)
        self.index = index
        self.on_delete = on_delete
        self.on_change = on_change
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create a frame with border
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QFrame.Shadow.Raised)
        frame.setStyleSheet("QFrame { background-color: rgba(0, 0, 0, 0.03); border-radius: 8px; }")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(10)
        
        # Header with title and delete button
        header_layout = QHBoxLayout()
        title_label = QLabel(f"Ring {self.index + 1}")
        font = title_label.font()
        font.setBold(True)
        title_label.setFont(font)
        
        delete_button = QPushButton("Delete")
        delete_button.setMaximumWidth(80)
        delete_button.clicked.connect(self.request_delete)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(delete_button)
        frame_layout.addLayout(header_layout)
        
        # RPM settings - now vertical
        rpm_layout = QVBoxLayout()
        rpm_label = QLabel("RPM:")
        self.rpm_combo = QComboBox()
        self.rpm_combo.addItems(["16", "33.33", "45", "78"])
        self.rpm_combo.setCurrentIndex(1)  # 33.33 by default
        self.rpm_combo.currentIndexChanged.connect(self.settings_changed)
        
        rpm_layout.addWidget(rpm_label)
        rpm_layout.addWidget(self.rpm_combo)
        
        # Manual RPM input
        self.rpm_manual_check = QCheckBox("Enter RPM manually:")
        self.rpm_manual_check.stateChanged.connect(self.toggle_rpm_input)
        self.rpm_manual_check.stateChanged.connect(self.settings_changed)
        rpm_layout.addWidget(self.rpm_manual_check)
        
        self.rpm_input = QDoubleSpinBox()
        self.rpm_input.setRange(1, 100)
        self.rpm_input.setValue(33.33)
        self.rpm_input.setDecimals(2)
        self.rpm_input.setEnabled(False)  # Disabled by default
        self.rpm_input.valueChanged.connect(self.settings_changed)
        rpm_layout.addWidget(self.rpm_input)
        
        frame_layout.addLayout(rpm_layout)
        
        # Frequency (Hz)
        hz_layout = QVBoxLayout()
        hz_label = QLabel("Frequency (Hz):")
        self.hz_combo = QComboBox()
        self.hz_combo.addItems(["50", "60"])
        self.hz_combo.currentIndexChanged.connect(self.settings_changed)
        hz_layout.addWidget(hz_label)
        hz_layout.addWidget(self.hz_combo)
        frame_layout.addLayout(hz_layout)
        
        # Ring depth
        depth_layout = QVBoxLayout()
        depth_label = QLabel("Ring depth (mm):")
        self.depth_input = QDoubleSpinBox()
        self.depth_input.setRange(1, 100)
        self.depth_input.setValue(8)
        self.depth_input.setDecimals(1)
        self.depth_input.valueChanged.connect(self.settings_changed)
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.depth_input)
        frame_layout.addLayout(depth_layout)
        
        # Single mode checkbox
        self.force_single_check = QCheckBox("Single mode")
        self.force_single_check.setChecked(True)
        self.force_single_check.stateChanged.connect(self.settings_changed)
        frame_layout.addWidget(self.force_single_check)
        
        # Information layout
        info_layout = QVBoxLayout()
        info_group = QGroupBox()
        info_group_layout = QVBoxLayout()
        
        self.segments_label = QLabel()
        info_group_layout.addWidget(self.segments_label)
        
        self.line_width_label = QLabel()
        info_group_layout.addWidget(self.line_width_label)
        
        self.information_label = QLabel()
        info_group_layout.addWidget(self.information_label)
        
        info_group.setLayout(info_group_layout)
        info_layout.addWidget(info_group)
        frame_layout.addLayout(info_layout)
        
        main_layout.addWidget(frame)
        
        # Calculate and update segments info
        self.update_segments_info()
    
    def toggle_rpm_input(self, state):
        # Enables or disables manual RPM input
        is_checked = state == Qt.CheckState.Checked.value
        self.rpm_input.setEnabled(is_checked)
        self.rpm_combo.setEnabled(not is_checked)
        self.update_segments_info()
    
    def get_rpm_value(self):
        # Gets the RPM value according to the configuration
        if self.rpm_manual_check.isChecked():
            return self.rpm_input.value()
        else:
            return float(self.rpm_combo.currentText())
    
    def get_hz_value(self):
        # Gets the Hz value
        return float(self.hz_combo.currentText())
    
    def get_depth_value(self):
        # Gets the ring depth value
        return self.depth_input.value()
    
    def lines_to_rpm(self, num_lines, frequency):
        # Calculates the RPM given the number of lines and the frequency
        rpm = (120 * frequency) / num_lines
        return round(rpm, 3)
    
    def calculate_segments_and_line_width(self, radius):
        # Calculate the number of lines, width of lines and rpm
        rpm = self.get_rpm_value()
        hz = self.get_hz_value()
        
        # Calculate exact number of lines
        num_lines_exact = (60 * hz) / rpm * 2
        
        # Calculate floor and ceiling number of lines
        num_lines_floor = math.floor(num_lines_exact)
        num_lines_floor_rpm = self.lines_to_rpm(num_lines_floor, hz)
        num_lines_ceil = math.ceil(num_lines_exact)
        num_lines_ceil_rpm = self.lines_to_rpm(num_lines_ceil, hz)
        
        num_lines_rpm = 0
        
        # Check if number of lines is an integer or if single mode is forced
        if num_lines_floor == num_lines_ceil or self.force_single_check.isChecked():
            if (num_lines_floor == num_lines_ceil):
                num_lines = num_lines_floor
            else:
                num_lines = round(num_lines_exact)
            num_lines_rpm = self.lines_to_rpm(num_lines, hz)
        else:
            num_lines = 0  # Will be used to draw 2 sets of lines
        
        # Calculate line width
        segment_width = (2 * math.pi * radius) / max(num_lines, 1)
        line_width = segment_width / 2
        
        return (num_lines_exact, num_lines, num_lines_rpm, line_width, 
                num_lines_floor, num_lines_ceil, num_lines_floor_rpm, num_lines_ceil_rpm)
    
    def update_segments_info(self, radius=None):
        # Updates information about the number of segments and line width
        # Use a default radius if none provided
        if radius is None:
            radius = 100  # Default radius for calculations
        
        (num_lines_exact, num_lines, num_lines_rpm, line_width,
         num_lines_floor, num_lines_ceil, num_lines_floor_rpm, num_lines_ceil_rpm) = self.calculate_segments_and_line_width(radius)
        
        # Update segments label
        if num_lines_floor == num_lines_ceil or self.force_single_check.isChecked():
            self.segments_label.setText(f"Number of segments: {num_lines}")
        else:
            self.segments_label.setText(f"Number of segments: {num_lines_floor}/{num_lines_ceil}")
        
        # Update line width label
        self.line_width_label.setText(f"Line width: {line_width:.2f} mm")
        
        # Update information label
        if num_lines_floor == num_lines_ceil or self.force_single_check.isChecked():
            output_text = [
                f"Ideal: {round(num_lines_exact, 3)} lines",
                f"Created: {num_lines} ({num_lines_rpm} rpm) lines",
            ]
        else:
            output_text = [
                f"Ideal: {round(num_lines_exact, 3)} lines",
                f"Inner: {num_lines_ceil_rpm} rpm ({num_lines_ceil} lines)",
                f"Outer: {num_lines_floor_rpm} rpm ({num_lines_floor} lines)",
            ]
        self.information_label.setText("\n".join(output_text))
    
    def settings_changed(self):
        # Called when any setting is changed
        self.update_segments_info()
        if self.on_change:
            self.on_change()
    
    def request_delete(self):
        # Request to delete this ring
        if self.on_delete:
            self.on_delete(self.index)
    
    def get_settings(self):
        # Returns the settings for this ring
        return {
            'rpm': self.get_rpm_value(),
            'hz': self.get_hz_value(),
            'depth': self.get_depth_value(),
            'single_mode': self.force_single_check.isChecked()
        }

class StroboscopeMultiRingsGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Ring Stroboscopic Disc Generator")
        self.setMinimumSize(1000, 700)
        self.svg_content = ""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_svg_file = None  # Temporary file to store the SVG
        
        # List to store ring widgets
        self.ring_widgets = []
        
        # Timer to delay the preview update
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.generate_disc)
        
        # Apply a modest increase to the application's font
        self.apply_font_scaling()
        
        # Setup the user interface
        self.setup_ui()
        
        # Add the first ring by default
        self.add_ring()
    
    def apply_font_scaling(self):
        # Apply a modest increase to the application's font
        # Use a fixed and conservative scale factor
        self.scale_factor = 1.15  # 15% increase
        
        # Apply scaling to the default application font
        font = QApplication.font()
        font_size = font.pointSize()
        if font_size > 0:  # If font size is valid
            font.setPointSize(int(font_size * self.scale_factor))
            QApplication.setFont(font)
    
    def is_dark_theme(self):
        # Detect if the system is using a dark theme
        # Get the application palette
        palette = QGuiApplication.palette()
        # Get the window background color
        background_color = palette.color(palette.ColorRole.Window)
        # Calculate brightness (0-255), where lower values are darker
        brightness = (background_color.red() * 299 + background_color.green() * 587 + background_color.blue() * 114) / 1000
        # If brightness is less than 128, consider it a dark theme
        return brightness < 128
    
    def apply_font_to_widget(self, widget, size_increase=0):
        # Apply a font with a custom size to a specific widget
        font = widget.font()
        current_size = font.pointSize()
        if current_size > 0 and size_increase > 0:
            font.setPointSize(current_size + size_increase)
            widget.setFont(font)
    
    def schedule_preview_update(self):
        # Schedule a preview update after a brief delay
        self.update_timer.start(300)  # 300ms delay to avoid excessive updates
    
    def setup_ui(self):
        # Main widget
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
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Controls Panel
        controls_panel = QWidget()
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Disc Parameters Group
        params_group = QGroupBox("Disc Parameters (in mm)")
        self.apply_font_to_widget(params_group, 1)  # Group title slightly larger
        params_layout = QVBoxLayout()
        
        # Diameter
        diameter_layout = QHBoxLayout()
        diameter_label = QLabel("Total diameter:")
        self.diameter_input = QSpinBox()
        self.diameter_input.setRange(10, 320)
        self.diameter_input.setValue(200)
        self.diameter_input.valueChanged.connect(self.schedule_preview_update)
        diameter_layout.addWidget(diameter_label)
        diameter_layout.addWidget(self.diameter_input)
        params_layout.addLayout(diameter_layout)
        
        # Spindle diameter
        spindle_diameter_layout = QHBoxLayout()
        spindle_diameter_label = QLabel("Spindle diameter:")
        self.spindle_diameter_input = QDoubleSpinBox()
        self.spindle_diameter_input.setRange(0, 20)
        self.spindle_diameter_input.setValue(7)
        self.spindle_diameter_input.setDecimals(2)
        self.spindle_diameter_input.setSingleStep(0.1)
        self.spindle_diameter_input.valueChanged.connect(self.schedule_preview_update)
        spindle_diameter_layout.addWidget(spindle_diameter_label)
        spindle_diameter_layout.addWidget(self.spindle_diameter_input)
        params_layout.addLayout(spindle_diameter_layout)
        
        # Optional outer circle
        
        # Outer circle width
        outer_circle_layout = QVBoxLayout()
        outer_circle_width_layout = QHBoxLayout()
        outer_circle_width_label = QLabel("Outer circle width:")
        self.outer_circle_width_input = QDoubleSpinBox()
        self.outer_circle_width_input.setRange(0, 10)
        self.outer_circle_width_input.setValue(1)
        self.outer_circle_width_input.setSingleStep(0.1)
        self.outer_circle_width_input.setDecimals(2)
        self.outer_circle_width_input.valueChanged.connect(self.schedule_preview_update)
        outer_circle_width_layout.addWidget(outer_circle_width_label)
        outer_circle_width_layout.addWidget(self.outer_circle_width_input)
        outer_circle_layout.addLayout(outer_circle_width_layout)
        
        params_layout.addLayout(outer_circle_layout)
        
        # Ring separation
        ring_separation_layout = QHBoxLayout()
        ring_separation_label = QLabel("Ring separation:")
        self.ring_separation_input = QDoubleSpinBox()
        self.ring_separation_input.setRange(0, 10)
        self.ring_separation_input.setValue(1)
        self.ring_separation_input.setDecimals(2)
        self.ring_separation_input.valueChanged.connect(self.schedule_preview_update)
        ring_separation_layout.addWidget(ring_separation_label)
        ring_separation_layout.addWidget(self.ring_separation_input)
        params_layout.addLayout(ring_separation_layout)

        params_group.setLayout(params_layout)
        controls_layout.addWidget(params_group)
        
        # Rings Group
        rings_group = QGroupBox("Rings Configuration")
        self.apply_font_to_widget(rings_group, 1)
        rings_layout = QVBoxLayout()
        rings_layout.setSpacing(5)  # Increase spacing between elements

        # Scroll area for rings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(250)  # Set minimum height

        # Container for rings
        self.rings_container = QWidget()
        self.rings_layout = QVBoxLayout(self.rings_container)
        self.rings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.rings_layout.setContentsMargins(0, 0, 10, 0)  # Add padding
        self.rings_layout.setSpacing(5)  # Add spacing between rings

        scroll_area.setWidget(self.rings_container)
        rings_layout.addWidget(scroll_area)
        
        # Add Ring button
        self.add_ring_button = QPushButton("Add Another Ring")
        self.apply_font_to_widget(self.add_ring_button, 1)
        self.add_ring_button.clicked.connect(self.add_ring)
        rings_layout.addWidget(self.add_ring_button)
        
        rings_group.setLayout(rings_layout)
        controls_layout.addWidget(rings_group)
        
        # Buttons
        buttons_layout = QVBoxLayout()
        
        # Generate Disc button
        self.generate_button = QPushButton("Update Preview")
        self.apply_font_to_widget(self.generate_button, 1)
        self.generate_button.setToolTip("The preview is updated automatically, but you can force an update with this button")
        self.generate_button.clicked.connect(self.generate_disc)
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
        
        # Paper format selection (for PDF export)
        self.paper_format_layout = QHBoxLayout()
        paper_format_label = QLabel("Paper format:")
        self.paper_format_combo = QComboBox()
        self.paper_format_combo.addItems(["A4", "Letter", "Legal", "A3"])
        self.paper_format_combo.setCurrentIndex(0)  # A4 by default
        self.paper_format_combo.setEnabled(False)  # Disabled by default (enabled only when PDF is selected)
        
        self.paper_format_layout.addWidget(paper_format_label)
        self.paper_format_layout.addWidget(self.paper_format_combo)
        buttons_layout.addLayout(self.paper_format_layout)
        
        # Connect radio buttons to enable/disable paper format selection
        self.pdf_radio.toggled.connect(lambda checked: self.paper_format_combo.setEnabled(checked))
        
        self.export_button = QPushButton("Export")
        self.apply_font_to_widget(self.export_button, 1)
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
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        # Adjust the size of the SVG when the window is resized
        super().resizeEvent(event)
        self.adjust_svg_size()
    
    def adjust_svg_size(self):
        # Adjust the size of the SVG widget to occupy the maximum available space
        if hasattr(self, 'svg_widget') and hasattr(self, 'preview_panel'):
            # Get the available width in the preview panel
            available_width = self.preview_panel.width() - PREVIEW_PANEL_MARGIN_WIDTH
            available_height = self.preview_panel.height() - PREVIEW_PANEL_MARGIN_HEIGHT
            
            # Use the smaller value to maintain a square aspect
            size = min(available_width, available_height)
            
            # Set the size of the SVG widget
            self.svg_widget.setFixedSize(QSize(size, size))
    
    def add_ring(self):
        # Add a new ring to the configuration
        # Add a separator if there are already rings
        if self.ring_widgets:
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            self.rings_layout.addWidget(separator)
        
        index = len(self.ring_widgets)
        ring_widget = RingSettings(
            parent=self.rings_container,
            index=index,
            on_delete=self.delete_ring,
            on_change=self.schedule_preview_update
        )
        self.ring_widgets.append(ring_widget)
        self.rings_layout.addWidget(ring_widget)
        
        # Update the preview
        self.schedule_preview_update()
    
    def delete_ring(self, index):
        # Delete a ring from the configuration
        if index < len(self.ring_widgets):
            # Remove the widget from the layout and delete it
            widget = self.ring_widgets.pop(index)
            self.rings_layout.removeWidget(widget)
            widget.deleteLater()
            
            # Remove separator if needed
            if index > 0 and index < len(self.ring_widgets) + 1:
                # Find the separator before this widget
                separator_index = index * 2 - 1
                if separator_index < self.rings_layout.count():
                    separator = self.rings_layout.itemAt(separator_index).widget()
                    if separator and isinstance(separator, QFrame):
                        self.rings_layout.removeWidget(separator)
                        separator.deleteLater()
        
        # Update the indices of the remaining widgets
        for i, widget in enumerate(self.ring_widgets):
            widget.index = i
            title_label = widget.findChild(QLabel)
            if title_label:
                title_label.setText(f"Ring {i + 1}")
        
        # Update the preview
        self.schedule_preview_update()
    
    def calculate_lines_for_ring(self, ring_widget, radius, ring_depth):
        # Calculate the number of lines and line width for a ring
        settings = ring_widget.get_settings()
        rpm = settings['rpm']
        hz = settings['hz']
        single_mode = settings['single_mode']
        
        # Update the ring widget's calculated information
        ring_widget.update_segments_info(radius)
        
        # Calculate the exact number of lines
        num_lines_exact = (60 * hz) / rpm * 2
        
        # Calculate floor and ceiling number of lines
        num_lines_floor = math.floor(num_lines_exact)
        num_lines_ceil = math.ceil(num_lines_exact)
        
        # Determine if we're using single or double mode
        if num_lines_floor == num_lines_ceil or single_mode:
            if num_lines_floor == num_lines_ceil:
                num_lines = num_lines_floor
            else:
                num_lines = round(num_lines_exact)
            
            # Calculate line width
            circumference = 2 * math.pi * radius
            line_width = circumference / (num_lines * 2)  # Half the segment width
            
            return {
                'mode': 'single',
                'num_lines': num_lines,
                'line_width': line_width
            }
        else:
            # Double mode
            # Calculate line widths for both sets
            outer_circumference = 2 * math.pi * radius
            inner_circumference = 2 * math.pi * (radius - ring_depth)
            
            outer_line_width = outer_circumference / (num_lines_floor * 2)
            inner_line_width = inner_circumference / (num_lines_ceil * 2)
            
            return {
                'mode': 'double',
                'outer_num_lines': num_lines_floor,
                'outer_line_width': outer_line_width,
                'inner_num_lines': num_lines_ceil,
                'inner_line_width': inner_line_width
            }
    
    def generate_disc(self):
        # Generates the multi-ring stroboscopic disc SVG.
        # Check if there are any rings
        if not self.ring_widgets:
            QMessageBox.warning(self, "Warning", "Please add at least one ring.")
            return
        
        # Input parameters
        diameter = self.diameter_input.value()
        spindle_diameter = self.spindle_diameter_input.value()
        outer_circle_width = self.outer_circle_width_input.value()
        
        ring_separation = self.ring_separation_input.value()
        
        # SVG temp file path
        self.temp_svg_file = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
        self.temp_svg_file.close()
        
        dwg = svgwrite.Drawing(
            self.temp_svg_file.name,
            size=(f"{diameter}mm", f"{diameter}mm"),
            profile="tiny",
            viewBox=f"0 0 {diameter} {diameter}",
        )
        
        center = (diameter / 2, diameter / 2)
        
        # Draw Outer Circle
        disc_radius = diameter / 2 - (outer_circle_width / 2 if outer_circle_width > 0 else 0)
        
        if outer_circle_width > 0:
            dwg.add(dwg.circle(
                center=center, 
                r=disc_radius, 
                fill='none', 
                stroke='black', 
                stroke_width=outer_circle_width
            ))
            
        current_radius = disc_radius - (outer_circle_width / 2 if outer_circle_width > 0 else 0)
        
        # Get settings for all rings
        ring_widgets = self.ring_widgets.copy()
        
        # Draw each ring from outside to inside
        for i, ring_widget in enumerate(ring_widgets):
            settings = ring_widget.get_settings()
            ring_depth = settings['depth']
            
            # Calculate inner radius for this ring
            inner_radius = current_radius - ring_depth
            
            # Ensure inner radius is not smaller than the spindle radius
            if inner_radius < spindle_diameter / 2:
                inner_radius = spindle_diameter / 2
                ring_depth = current_radius - inner_radius
            
            # Calculate lines for this ring
            lines_info = self.calculate_lines_for_ring(ring_widget, current_radius, ring_depth)
            
            if lines_info['mode'] == 'single':
                # Draw single set of lines
                num_lines = lines_info['num_lines']
                line_width = lines_info['line_width']
                
                angle_increment = 360 / num_lines # Degrees between each line
                
                for j in range(num_lines):
                    angle = math.radians(j * angle_increment)
                    # Outer endpoint of the line (x1, y1)
                    x1 = center[0] + current_radius * math.sin(angle)
                    y1 = center[1] - (current_radius * math.cos(angle))
                    
                    # Inner endpoint of the line (x2, y2)
                    x2 = center[0] + inner_radius * math.sin(angle)
                    y2 = center[1] - (inner_radius * math.cos(angle))
                    
                    dwg.add(dwg.line((x1, y1), (x2, y2), stroke=svgwrite.rgb(0, 0, 0, "%"), stroke_width=line_width))
            else:
                # Draw double set of lines
                # Outer set
                outer_num_lines = lines_info['outer_num_lines']
                outer_line_width = lines_info['outer_line_width']
                
                angle_increment_outer = 360 / outer_num_lines
                
                for j in range(outer_num_lines):
                    angle = math.radians(j * angle_increment_outer)
                    # Outer endpoint of the line (x1, y1)
                    x1 = center[0] + current_radius * math.sin(angle)
                    y1 = center[1] - (current_radius * math.cos(angle))
                    
                    # Inner endpoint of the line (x2, y2)
                    mid_radius = current_radius - ring_depth / 2
                    x2 = center[0] + mid_radius * math.sin(angle)
                    y2 = center[1] - (mid_radius * math.cos(angle))
                    
                    dwg.add(dwg.line((x1, y1), (x2, y2), stroke=svgwrite.rgb(0, 0, 0, "%"), stroke_width=outer_line_width))
                
                # Inner set
                inner_num_lines = lines_info['inner_num_lines']
                inner_line_width = lines_info['inner_line_width']
                
                angle_increment_inner = 360 / inner_num_lines
                
                for j in range(inner_num_lines):
                    angle = math.radians(j * angle_increment_inner)
                    # Outer endpoint of the line (x1, y1)
                    mid_radius = current_radius - ring_depth / 2
                    x1 = center[0] + mid_radius * math.sin(angle)
                    y1 = center[1] - (mid_radius * math.cos(angle))
                    
                    # Inner endpoint of the line (x2, y2)
                    x2 = center[0] + inner_radius * math.sin(angle)
                    y2 = center[1] - (inner_radius * math.cos(angle))
                    
                    dwg.add(dwg.line((x1, y1), (x2, y2), stroke=svgwrite.rgb(0, 0, 0, "%"), stroke_width=inner_line_width))
            
            # Update current radius for the next ring, applying separation
            current_radius = inner_radius - ring_separation
        
        # Draw Spindle Hole
        dwg.add(dwg.circle(
            center=center, 
            r=spindle_diameter/2, 
            fill='black', 
            stroke='black', 
            stroke_width=0.2
        ))
        
        # Save and Display
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
            else:
                # PDF selected
                file_filter = "PDF Files (*.pdf)"
                default_ext = ".pdf"
        
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Multi-Ring Stroboscopic Disc", "", file_filter
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
                    return # Do not overwrite
        
            if self.svg_radio.isChecked():
                # Save as SVG (copy the temporary file)
                with open(self.temp_svg_file.name, 'r') as src, open(file_path, 'w') as dst:
                    dst.write(src.read())
            else:
                # Save as PDF (convert SVG to PDF)
                drawing = svg2rlg(self.temp_svg_file.name)
            
                # Get the disc diameter in points (1 mm = 2.83465 points)
                disc_diameter_mm = self.diameter_input.value()
                disc_diameter_pt = disc_diameter_mm * 2.83465
            
                # Set paper size based on selection
                paper_format = self.paper_format_combo.currentText()
                if paper_format == "A4":
                    pagesize = A4
                elif paper_format == "Letter":
                    pagesize = LETTER
                elif paper_format == "Legal":
                    pagesize = LEGAL
                elif paper_format == "A3":
                    pagesize = A3
                else:
                    pagesize = A4  # Default to A4
            
                # Get page dimensions in points
                page_width, page_height = pagesize
            
                # Calculate margins in points (20mm)
                margin_pt = 20 * 2.83465
            
                # Calculate the available space for the disc
                max_width = page_width - 2 * margin_pt
                max_height = page_height - 2 * margin_pt
            
                # Calculate the scale factor to fit the disc within the available space
                scale_factor = min(max_width / disc_diameter_pt, max_height / disc_diameter_pt)
            
                # Calculate the position to center the disc on the page
                x_offset = (page_width - disc_diameter_pt * scale_factor) / 2
                y_offset = (page_height - disc_diameter_pt * scale_factor) / 2
            
                # Create a new drawing with the correct page size
                from reportlab.graphics.shapes import Drawing, Group
            
                # Create a new drawing with the page size
                new_drawing = Drawing(page_width, page_height)
            
                # Scale and center the original drawing
                group = Group(drawing)
                group.scale(scale_factor, scale_factor)
                group.translate(x_offset / scale_factor, y_offset / scale_factor)
            
                # Add the scaled and centered group to the new drawing
                new_drawing.add(group)
            
                # Render the new drawing to PDF
                renderPDF.drawToFile(new_drawing, file_path, pagesize=pagesize)
        
            QMessageBox.information(self, "Success", f"File saved successfully to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving file: {e}")
    
    def closeEvent(self, event):
        self.temp_dir.cleanup()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StroboscopeMultiRingsGenerator()
    window.show()
    sys.exit(app.exec())
