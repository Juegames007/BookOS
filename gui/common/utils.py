from PySide6.QtGui import QFontDatabase, QIcon
import os

def format_price(price: float) -> str:
    """
    Formatea un número de punto flotante a una cadena de texto representando
    un precio en pesos colombianos, sin decimales y con separadores de miles.
    """
    try:
        return f"{int(price):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "0"

def get_icon_path(icon_name: str) -> str:
    """Obtiene la ruta completa de un icono en la carpeta de imágenes."""
    # Navega desde gui/common -> gui/ -> project_root/ -> app/imagenes
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, 'app', 'imagenes', icon_name)

def load_fonts():
    """Carga las fuentes personalizadas desde la carpeta de recursos."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fonts_dir = os.path.join(base_dir, 'gui', 'resources', 'fonts')
    
    # Listar y cargar fuentes
    try:
        for font_file in os.listdir(fonts_dir):
            if font_file.lower().endswith(".ttf"):
                font_path = os.path.join(fonts_dir, font_file)
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id == -1:
                    print(f"Advertencia: No se pudo cargar la fuente: {font_path}")
    except FileNotFoundError:
        print(f"Advertencia: El directorio de fuentes no se encontró en: {fonts_dir}") 