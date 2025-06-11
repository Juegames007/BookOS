# sfsymbols.py

import os
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QSize, Qt

class SFSymbols:
    _instance = None
    _symbols = {}
    _symbols_path = os.path.join(os.path.dirname(__file__), 'svg')

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SFSymbols, cls).__new__(cls)
            cls._instance._load_symbols()
        return cls._instance

    def _load_symbols(self):
        if not os.path.exists(self._symbols_path):
            print(f"Advertencia: El directorio de símbolos no existe: {self._symbols_path}")
            return
        for filename in os.listdir(self._symbols_path):
            if filename.endswith(".svg"):
                symbol_name = os.path.splitext(filename)[0]
                self._symbols[symbol_name] = os.path.join(self._symbols_path, filename)

    @classmethod
    def get_icon(cls, name: str, color: str = "black") -> QIcon:
        """
        Obtiene un QIcon para un símbolo SVG, coloreado dinámicamente.
        """
        if cls._instance is None:
            cls()  # Llama a __new__ para crear la instancia
        
        filepath = cls._symbols.get(name)
        if not filepath:
            print(f"Advertencia: Símbolo '{name}' no encontrado.")
            return QIcon() # Devuelve un icono vacío

        # Crear un QPixmap para renderizar el SVG coloreado
        pixmap = SFSymbols.render_svg_to_pixmap(filepath, QSize(128, 128), color)
        return QIcon(pixmap)

    @staticmethod
    def render_svg_to_pixmap(svg_path: str, size: QSize, color: str) -> QPixmap:
        """
        Renderiza un archivo SVG en un QPixmap con un color específico.
        """
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
        except FileNotFoundError:
            print(f"Error: No se pudo encontrar el archivo SVG en {svg_path}")
            return QPixmap()

        # Reemplazar 'currentColor' de forma más robusta, manejando comillas simples y dobles.
        colored_svg = svg_content.replace('"currentColor"', f'"{color}"')
        colored_svg = colored_svg.replace("'currentColor'", f"'{color}'")

        renderer = QSvgRenderer(colored_svg.encode('utf-8'))
        
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent) # Usar Qt.transparent explícitamente

        painter = QPainter(pixmap)
        renderer.render(painter)
        
        # Limpieza
        del painter 
        
        return pixmap 