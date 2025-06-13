from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QHBoxLayout
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt, Signal

from gui.common.styles import FONTS, COLORS
from gui.components.image_manager import ImageManager

class BookDetailWidget(QFrame):
    image_view_requested = Signal(str)

    def __init__(self, image_manager: ImageManager, parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("bookDetailFrame")
        self.setStyleSheet("QFrame#bookDetailFrame { background-color: transparent; border: none; }")
        
        self.image_manager = image_manager
        self.image_manager.image_loaded.connect(self._on_image_loaded)
        self._current_book_isbn = None

        # Main layout
        frame_main_layout = QHBoxLayout(self)
        frame_main_layout.setContentsMargins(10, 10, 10, 10)
        frame_main_layout.setSpacing(15)

        # Left side: Image
        self.image_label = QLabel()
        self.image_label.setFixedSize(180, 220)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0, 0, 0, 0.05);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 8px;
                color: {COLORS['text_secondary']};
                font-family: {FONTS['family']};
                font-size: {FONTS['size_normal']}px;
            }}
        """)
        
        # Right side: Details in a scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("QWidget { background: transparent; }")
        self.scroll_area.setWidget(self.content_widget)

        self.details_layout = QVBoxLayout(self.content_widget)
        self.details_layout.setAlignment(Qt.AlignTop)
        self.details_layout.setSpacing(10)
        
        # --- Title ---
        self.title_label = self._create_label(FONTS['size_large'], QFont.Weight.Bold, COLORS['text_primary'])
        self.details_layout.addWidget(self.title_label)

        # --- Author ---
        self.author_label = self._create_label(FONTS['size_medium'], QFont.Weight.Normal, COLORS['text_secondary'], "Autor: ")
        self.details_layout.addWidget(self.author_label)

        # --- Category ---
        self.category_label = self._create_label(FONTS['size_normal'], QFont.Weight.Normal, COLORS['text_secondary'], "Categoría: ")
        self.details_layout.addWidget(self.category_label)
        
        # --- Quantity ---
        self.quantity_label = self._create_label(FONTS['size_normal'], QFont.Weight.Normal, COLORS['text_secondary'], "Cantidad: ")
        self.details_layout.addWidget(self.quantity_label)

        # --- Price ---
        self.price_label = self._create_label(FONTS['size_medium'], QFont.Weight.Bold, COLORS['accent_green'], "Precio: ")
        self.details_layout.addWidget(self.price_label)

        # --- Position ---
        self.position_label = self._create_label(FONTS['size_normal'], QFont.Weight.Normal, COLORS['text_secondary'], "Posición: ")
        self.details_layout.addWidget(self.position_label)

        frame_main_layout.addWidget(self.scroll_area, 1)
        frame_main_layout.addWidget(self.image_label)
        self.update_details({})

    def _create_label(self, font_size, font_weight, color, prefix=""):
        label = QLabel(prefix)
        label.setFont(QFont(FONTS['family'], font_size, font_weight))
        label.setStyleSheet(f"color: {color}; background-color: transparent;")
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        return label

    def update_details(self, book_data: dict):
        self._current_book_isbn = book_data.get("ISBN")

        if not book_data:
            self.title_label.setText("Seleccione un libro")
            self.author_label.setVisible(False)
            self.category_label.setVisible(False)
            self.quantity_label.setVisible(False)
            self.price_label.setVisible(False)
            self.position_label.setVisible(False)
            self.image_label.setText("SELECCIONE UN LIBRO")
            self.image_label.setPixmap(QPixmap())
            return

        self.author_label.setVisible(True)
        self.category_label.setVisible(True)
        self.quantity_label.setVisible(True)
        self.price_label.setVisible(True)
        self.position_label.setVisible(True)

        self.title_label.setText(book_data.get("Título", "N/A"))
        self.author_label.setText(f"Autor: {book_data.get('Autor', 'N/A')}")
        
        categories = book_data.get("Categorías", [])
        cat_text = ', '.join(categories) if isinstance(categories, list) else (categories or 'N/A')
        self.category_label.setText(f"Categoría: {cat_text}")

        self.quantity_label.setText(f"Cantidad: {book_data.get('Cantidad', 'N/A')}")

        price = book_data.get('Precio', 'N/A')
        price_text = f"$ {int(price):,}".replace(",", ".") if isinstance(price, (int, float)) else str(price)
        self.price_label.setText(f"Precio: {price_text}")
        
        self.position_label.setText(f"Posición: {book_data.get('Posición', 'N/A')}")

        image_url = book_data.get("Imagen")
        if image_url and self._current_book_isbn:
            self.image_label.setText("CARGANDO...")
            self.image_manager.get_image(self._current_book_isbn, image_url)
        else:
            self.image_label.setText("NO IMAGEN DISPONIBLE")
            self.image_label.setPixmap(QPixmap())

    def _on_image_loaded(self, image_id, pixmap):
        if self._current_book_isbn == image_id:
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
            self.image_label.setText("")