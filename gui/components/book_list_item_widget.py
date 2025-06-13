from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt, Signal, QSize

from gui.common.styles import FONTS, COLORS
from gui.components.image_manager import ImageManager

class BookListItemWidget(QWidget):
    """
    Custom widget for a row in the book list view.
    """
    image_view_requested = Signal(str)

    def __init__(self, book_data: dict, image_manager: ImageManager, parent=None):
        super().__init__(parent)
        self.book_data = book_data
        self.image_manager = image_manager
        self.isbn = book_data.get("ISBN")

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(250, 250, 250, 0.95);
                border-radius: 6px;
                padding: 8px;
            }
            QLabel { background-color: transparent; }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignVCenter)

        # 1. Image
        self.image_label = QLabel()
        self.image_label.setFixedSize(45, 60)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0,0,0,0.05); 
                border-radius: 3px; 
                color: {COLORS['text_secondary']}; 
                font-size: 9px;
            }}
        """)
        self.image_label.setText("...")
        main_layout.addWidget(self.image_label)

        # 2. Title and Author
        title_author_layout = QVBoxLayout()
        self.title_label = QLabel(book_data.get("Título", "N/A"))
        self.title_label.setFont(QFont(FONTS["family"], FONTS["size_normal"], QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.author_label = QLabel(book_data.get("Autor", "N/A"))
        self.author_label.setFont(QFont(FONTS["family"], FONTS["size_small"]))
        self.author_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        title_author_layout.addWidget(self.title_label)
        title_author_layout.addWidget(self.author_label)
        main_layout.addLayout(title_author_layout, 3) # Give more space to title/author

        # 3. Details (Category, Position, Price)
        details_layout = QHBoxLayout()
        details_layout.setSpacing(15)

        categories = book_data.get("Categorías", ["N/A"])
        category_text = (categories[0] if categories else 'N/A')
        self.category_label = QLabel(f"{category_text}")
        
        self.position_label = QLabel(f"{book_data.get('Posición', 'N/A')}")
        
        price = book_data.get('Precio', 0)
        price_text = f"$ {int(price):,}".replace(",", ".") if isinstance(price, (int, float)) else f"$ {price}"
        self.price_label = QLabel(price_text)

        for label in [self.category_label, self.position_label, self.price_label]:
            label.setFont(QFont(FONTS["family"], FONTS["size_normal"]))
            label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            label.setMinimumWidth(100)
            details_layout.addWidget(label)
        
        main_layout.addLayout(details_layout, 2)


        # Load Image
        self.image_manager.image_loaded.connect(self.on_image_loaded)
        image_url = self.book_data.get("Imagen", "")
        if image_url and self.isbn:
            self.image_manager.get_image(self.isbn, image_url)
        else:
            self.image_label.setText("NO IMG")

    def on_image_loaded(self, image_id, pixmap):
        if self.isbn == image_id:
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                Qt.TransformationMode.SmoothTransformation
            ))
            self.image_label.setText("")

    # By removing minimumSizeHint, we let the layout determine the optimal size.
    # def minimumSizeHint(self):
    #     return QSize(200, 75)

