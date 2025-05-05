venv\Scripts\python -m nuitka stroboscope_multi_rings_generator.py ^
--standalone ^
--enable-plugin=pyqt6 ^
--include-module=svgwrite ^
--include-module=svglib ^
--include-module=tempfile ^
--windows-console-mode=disable ^
--onefile