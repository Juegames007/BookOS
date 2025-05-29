from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy, QHBoxLayout
from PySide6.QtGui import QFont, QDesktopServices, QIcon
from PySide6.QtCore import Qt, QUrl, Signal, QSize
from typing import Dict, Any
import os

# Attempt to get styles, provide defaults if not found
try:
    from gui.common.styles import FONTS, COLORS, STYLES
except ImportError:
    print("Warning: gui.common.styles not found. Using default styles for BookDetailWidget.")
    FONTS = {"family": "Arial", "size_large": 16, "size_medium": 13, "size_normal": 12, "size_small": 11, "size_uniform": 14}
    COLORS = {"text_primary": "#222222", "text_secondary": "#555555", "accent_blue": "#007AFF", "text_label": "#666666"}
    STYLES = {"button_primary": ""}

# Icon path for the image button
try:
    CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # Navigate two levels up (components -> gui -> project_root) then to app/imagenes/
    VER_ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(CURRENT_SCRIPT_DIR)), "app", "imagenes", "ver.png")
except NameError: # Fallback if __file__ is not defined
    VER_ICON_PATH = os.path.join("app", "imagenes", "ver.png")


class BookDetailWidget(QFrame):
    image_view_requested = Signal(str) # Signal to request opening an image URL

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("bookDetailFrame")
        # Make the QFrame itself transparent, as its parent (unified_content_card) will provide the visual background.
        self.setStyleSheet("QFrame#bookDetailFrame { background-color: transparent; border: none; }")
        self.font_family = FONTS.get("family", "Arial")

        # Main layout for this widget, allows content to scroll if it overflows
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.content_widget = QWidget() # Widget that will contain all the labels and button
        self.content_widget.setStyleSheet("QWidget { background: transparent; }")
        self.scroll_area.setWidget(self.content_widget)

        self.details_layout = QVBoxLayout(self.content_widget) # Layout for labels and button
        self.details_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.details_layout.setSpacing(10) # Adjusted spacing for label pairs
        self.details_layout.setContentsMargins(15, 10, 15, 10)

        text_color_primary = COLORS.get('text_primary', '#222222')
        text_color_secondary = COLORS.get('text_secondary', '#444444')
        label_text_color = COLORS.get('text_label', '#666666')
        label_font_size = FONTS.get("size_small", 11)
        # Uniform font size for all data values
        value_font_size_uniform = FONTS.get("size_uniform", 14)

        # --- Title --- 
        self.title_static_label = QLabel("Título:")
        self.title_static_label.setFont(QFont(self.font_family, label_font_size, QFont.Weight.Normal))
        self.title_static_label.setStyleSheet(f"color: {label_text_color}; background-color: transparent; margin-bottom: -3px;")
        self.details_layout.addWidget(self.title_static_label)

        self.title_label = QLabel("Título del Libro")
        # Title remains bold, but uses uniform size
        title_font = QFont(self.font_family, value_font_size_uniform, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {text_color_primary}; background-color: transparent;")
        self.title_label.setWordWrap(True)
        self.details_layout.addWidget(self.title_label)
        self.details_layout.addSpacing(6) # Adjusted spacing

        # --- Author --- 
        self.author_static_label = QLabel("Autor:")
        self.author_static_label.setFont(QFont(self.font_family, label_font_size, QFont.Weight.Normal))
        self.author_static_label.setStyleSheet(f"color: {label_text_color}; background-color: transparent; margin-bottom: -3px;")
        self.details_layout.addWidget(self.author_static_label)

        self.author_label = QLabel("Autor")
        author_font = QFont(self.font_family, value_font_size_uniform) # Uniform size
        self.author_label.setFont(author_font)
        self.author_label.setStyleSheet(f"color: {text_color_secondary}; background-color: transparent;")
        self.author_label.setWordWrap(True)
        self.details_layout.addWidget(self.author_label)
        self.details_layout.addSpacing(6)

        # --- Category --- 
        self.category_static_label = QLabel("Categoría:")
        self.category_static_label.setFont(QFont(self.font_family, label_font_size, QFont.Weight.Normal))
        self.category_static_label.setStyleSheet(f"color: {label_text_color}; background-color: transparent; margin-bottom: -3px;")
        self.details_layout.addWidget(self.category_static_label)

        self.category_label = QLabel("Categoría")
        category_font = QFont(self.font_family, value_font_size_uniform) # Uniform size
        self.category_label.setFont(category_font)
        self.category_label.setStyleSheet(f"color: {text_color_secondary}; background-color: transparent;")
        self.category_label.setWordWrap(True)
        self.details_layout.addWidget(self.category_label)
        self.details_layout.addSpacing(6)

        # --- Position --- 
        self.position_static_label = QLabel("Posición:")
        self.position_static_label.setFont(QFont(self.font_family, label_font_size, QFont.Weight.Normal))
        self.position_static_label.setStyleSheet(f"color: {label_text_color}; background-color: transparent; margin-bottom: -3px;")
        self.details_layout.addWidget(self.position_static_label)

        self.position_label = QLabel("Posición")
        position_font = QFont(self.font_family, value_font_size_uniform) # Uniform size
        self.position_label.setFont(position_font)
        self.position_label.setStyleSheet(f"color: {text_color_secondary}; background-color: transparent;")
        self.position_label.setWordWrap(True)
        self.details_layout.addWidget(self.position_label)

        self.details_layout.addStretch(1) # Pushes button to bottom
        
        # --- Image Button --- 
        self.view_image_button = QPushButton(" Ver Imagen")
        neutral_button_style = ("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.45); /* Adjusted transparency */
                border: 1px solid rgba(255, 255, 255, 0.55);
                color: #222222; 
                padding: 8px 12px; 
                border-radius: 6px; 
                font-size: {FONTS.get("size_normal", 12)}px;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.6); }
            QPushButton:pressed { background-color: rgba(255, 255, 255, 0.5); }
        """)
        self.view_image_button.setStyleSheet(neutral_button_style)
        self.view_image_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_image_button.clicked.connect(self._on_view_image_clicked)
        self.view_image_button.setVisible(False)
        self.view_image_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.view_image_button.setMinimumHeight(36)
        self.view_image_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        if os.path.exists(VER_ICON_PATH):
            self.view_image_button.setIcon(QIcon(VER_ICON_PATH))
            self.view_image_button.setIconSize(QSize(18,18))
        else:
            print(f"Advertencia: Ícono 'ver.png' no encontrado en {VER_ICON_PATH}")

        self.details_layout.addWidget(self.view_image_button, 0, Qt.AlignmentFlag.AlignLeft)
        
        # Set up the main layout for the QFrame itself, containing the scroll area
        frame_main_layout = QVBoxLayout(self)
        frame_main_layout.addWidget(self.scroll_area)
        frame_main_layout.setContentsMargins(0,0,0,0)

        # Store current book data
        self._current_book_data = None
        self.update_details({}) # Initialize with empty details

    def update_details(self, book_data: Dict[str, Any]):
        self._current_book_data = book_data
        is_book_selected = bool(book_data)

        self.title_static_label.setVisible(is_book_selected)
        self.author_static_label.setVisible(is_book_selected)
        self.category_static_label.setVisible(is_book_selected)
        self.position_static_label.setVisible(is_book_selected)

        if not is_book_selected:
            self.title_label.setText("Seleccione un libro") # Keep this centered or styled for prompt
            self.author_label.setText("")
            self.category_label.setText("")
            self.position_label.setText("")
            self.view_image_button.setVisible(False)
            return

        self.title_label.setText(book_data.get("Título", "N/A"))
        self.author_label.setText(book_data.get('Autor', 'N/A')) # Removed "Autor: " prefix
        categories = book_data.get("Categorías", [])
        if isinstance(categories, list):
            self.category_label.setText(', '.join(categories) if categories else 'N/A') # Removed "Categoría: " prefix
        else: self.category_label.setText(categories if categories else 'N/A')
        self.position_label.setText(book_data.get('Posición', 'N/A')) # Removed "Posición: " prefix
        image_url = book_data.get("Imagen", "")
        self.view_image_button.setVisible(bool(image_url))

    def _on_view_image_clicked(self):
        if self._current_book_data:
            image_url = self._current_book_data.get("Imagen", "")
            if image_url:
                print(f"Intentando abrir URL de imagen: {image_url}")
                # QDesktopServices.openUrl(QUrl(image_url)) # This is the standard way
                self.image_view_requested.emit(image_url) # Emit signal instead
            else:
                print("No hay URL de imagen para mostrar.")

# Example Usage (for testing this component standalone)
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication, QMainWindow
    import sys

    app = QApplication(sys.argv)

    # Mock data for testing
    sample_book = {
        "Título": "El Gran Libro de los Sueños Cósmicos",
        "Autor": "Dr. Fantástico Programador",
        "Categorías": ["Ciencia Ficción", "Aventura"],
        "Posición": "A1-01-Alpha",
        "Imagen": "https://www.ejemplo.com/imagen_libro.jpg" # Replace with a real image URL for testing button
    }
    no_image_book = {
        "Título": "Manual de Instrucciones para Objetos Inanimados",
        "Autor": "Profesor Anónimo",
        "Categorías": ["No Ficción", "Guías Prácticas"],
        "Posición": "Z9-99-Zeta",
        "Imagen": "" 
    }

    main_window = QMainWindow()
    main_window.setWindowTitle("Book Detail Widget Test")
    main_window.resize(380, 500) # Adjusted height for new layout
    
    # Simulate common styles if not available (adjust as needed for your project)
    if 'FONTS' not in globals():
        FONTS = {"family": "Segoe UI", "size_large": 16, "size_medium": 13, "size_normal": 12, "size_small": 11, "size_uniform": 14}
    if 'COLORS' not in globals():
        COLORS = {"text_primary": "#222222", "text_secondary": "#444444", "accent_blue": "#0078D4", "text_label": "#666666"}
    if 'STYLES' not in globals():
        STYLES = {"button_primary": ""}

    detail_widget = BookDetailWidget()
    detail_widget.update_details(sample_book)
    # detail_widget.update_details(no_image_book) # Test with no image
    # detail_widget.update_details({}) # Test empty

    def open_image_test(url):
        print(f"MAIN WINDOW: Image view requested for {url}")
        QDesktopServices.openUrl(QUrl(url))

    detail_widget.image_view_requested.connect(open_image_test)

    main_window.setCentralWidget(detail_widget)
    main_window.setStyleSheet("QMainWindow { background-color: #777788; }") # Darker bg for contrast test
    main_window.show()

    sys.exit(app.exec()) 