from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Qt, QSize, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from typing import List, Dict, Any

from .book_list_item_widget import BookListItemWidget

class BookListViewWidget(QWidget):
    # Signal to be emitted when an image view is requested from one of the items
    image_view_requested = Signal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QListWidget()
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                padding: 5px;
                outline: 0; /* Remove focus outline */
            }
            QListWidget::item {
                border: none; /* Remove default item border, custom widget handles it */
                background-color: transparent; /* Item background is handled by BookListItemWidget or its style */
                padding: 0px; /* No padding for the QListWidgetItem itself */
                margin-bottom: 5px; /* Spacing between custom widgets */
            }
            QListWidget::item:selected {
                background-color: rgba(200, 200, 230, 0.35); /* Subtle selection highlight for the item container */
                border-radius: 4px;
            }
            /* Hover effects can be managed by BookListItemWidget or here if desired */
            /* QListWidget::item:hover:!selected { background-color: rgba(240,240,248,0.15); border-radius: 4px; } */
        """)
        self.main_layout.addWidget(self.list_widget)

    def update_results(self, books_data: List[Dict[str, Any]]):
        self.list_widget.clear()
        if not books_data:
            return

        for book in books_data:
            list_item_widget = BookListItemWidget(book)
            # Connect the item's signal to the handler in this widget
            list_item_widget.image_view_requested.connect(self._handle_item_image_view_request)
            
            q_list_item = QListWidgetItem(self.list_widget)
            
            q_list_item.setSizeHint(list_item_widget.sizeHint())
            
            self.list_widget.addItem(q_list_item)
            self.list_widget.setItemWidget(q_list_item, list_item_widget)
            
            q_list_item.setData(Qt.ItemDataRole.UserRole, book)

    def get_current_selected_book_data(self) -> Dict[str, Any] | None:
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def _handle_item_image_view_request(self, image_url: str):
        # This method is called when a BookListItemWidget requests an image view.
        # It now emits the BookListViewWidget's own signal.
        if image_url:
            print(f"BookListViewWidget: Relaying image view request for URL: {image_url}")
            self.image_view_requested.emit(image_url)

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    
    book_list_view = BookListViewWidget()
    layout.addWidget(book_list_view)

    mock_data = [
        {"Título": "The Great Gatsby", "Autor": "F. Scott Fitzgerald", "Categorías": ["Classic"], "Precio": "10.99", "Posición": "A1", "Imagen": "path/to/gatsby_image.png"},
        {"Título": "To Kill a Mockingbird", "Autor": "Harper Lee", "Categorías": ["Classic", "Fiction"], "Precio": "12.50", "Posición": "A2", "Imagen": ""},
        {"Título": "1984", "Autor": "George Orwell", "Categorías": ["Dystopian", "Sci-Fi"], "Precio": "9.75", "Posición": "B1", "Imagen": "path/to/1984_image.png"},
        {"Título": "A Very Long Title Indeed To Test Truncation Capabilities of The Widget", "Autor": "A Prolific Author with an Equally Long Name", "Categorías": ["Test", "Long Data"], "Precio": "100.00", "Posición": "Z99-Omega", "Imagen": ""}
    ]
    book_list_view.update_results(mock_data)
    
    window.resize(700, 500)
    window.show()
    sys.exit(app.exec()) 