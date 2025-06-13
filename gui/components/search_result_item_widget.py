from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt, QSize

from gui.common.styles import FONTS, COLORS

class SearchResultItemWidget(QWidget):
    """
    Custom widget for an item in the search results list, showing book details.
    """
    def __init__(self, book_data, image_manager, parent=None):
        super().__init__(parent)
        self.book_data = book_data

        self.setMinimumHeight(60) # Reduced height as there is no image
        self.setStyleSheet("""
            QWidget {
                background-color: transparent; /* Card is now transparent, selection handled by QListWidget */
                border-radius: 6px;
                padding: 8px;
            }
            QWidget:hover {
                /* The hover is now handled by the item:selected style in the list view for consistency */
            }
            QLabel {
                background-color: transparent;
                border: none;
            }
        """)

        # Main layout is now vertical
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)
        main_layout.addStretch(1)


        # Title
        self.title_label = QLabel(book_data.get("Título", "N/A"))
        self.title_label.setFont(QFont(FONTS["family"], FONTS["size_normal"], QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.title_label.setWordWrap(True)
        main_layout.addWidget(self.title_label)

        # Author
        self.author_label = QLabel(book_data.get("Autor", "N/A"))
        self.author_label.setFont(QFont(FONTS["family"], FONTS["size_small"]))
        self.author_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        main_layout.addWidget(self.author_label)
        
        main_layout.addStretch(1)


    def on_image_loaded(self, image_id, pixmap):
        # This is no longer needed as we are not displaying images here.
        pass 