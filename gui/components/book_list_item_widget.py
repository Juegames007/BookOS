from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QDesktopServices
from gui.common.styles import COLORS
import os

# Placeholder for icon path, adjust as needed
try:
    CURRENT_SCRIPT_DIR_BLIW = os.path.dirname(os.path.abspath(__file__))
    ICON_BASE_PATH_BLIW = os.path.join(os.path.dirname(os.path.dirname(CURRENT_SCRIPT_DIR_BLIW)), "app", "imagenes")
    IMAGE_ICON_PATH = os.path.join(ICON_BASE_PATH_BLIW, "ver.png")
    NO_VER_ICON_PATH_BLIW = os.path.join(ICON_BASE_PATH_BLIW, "no_ver.png")
except NameError:
    IMAGE_ICON_PATH = ""
    NO_VER_ICON_PATH_BLIW = ""

class BookListItemWidget(QWidget):
    image_view_requested = Signal(str) # Signal to request opening an image URL

    def __init__(self, book_data: dict, parent: QWidget = None):
        super().__init__(parent)
        label_text_color = COLORS.get('text_primary', '#202427') 
        self.book_data = book_data

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5) # Margins for the content within the item
        self.main_layout.setSpacing(10)

        # --- Create labels for each piece of information ---
        self.title_label = QLabel(self._truncate_text(book_data.get("Título", "N/A"), 40)) # Increased truncation slightly
        self.title_label.setToolTip(book_data.get("Título", "N/A")) 
        self.title_label.setStyleSheet(f"font-weight: bold; font-size: 10pt; color : {label_text_color}") # Slightly smaller title for rows
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.author_label = QLabel(self._truncate_text(book_data.get("Autor", "N/A"), 20))
        self.author_label.setToolTip(book_data.get("Autor", "N/A"))
        self.author_label.setFixedWidth(140) # Fixed width for Author
        self.author_label.setStyleSheet(f"font-size: 9pt; color : {label_text_color}")

        categories = book_data.get("Categorías", [])
        category_text = ", ".join(categories) if isinstance(categories, list) else "N/A"
        self.category_label = QLabel(self._truncate_text(category_text, 22))
        self.category_label.setToolTip(category_text)
        self.category_label.setFixedWidth(160) # Fixed width for Category
        self.category_label.setStyleSheet(f"font-size: 9pt; color : {label_text_color}")
        
        price_value = book_data.get('Precio')
        if price_value is not None:
            try: 
                # Format as integer with thousands separator for Colombian pesos
                price_text = f"$ {int(price_value):,}".replace(",", ".")
            except (ValueError, TypeError): price_text = str(price_value)
        else: price_text = "N/A"
        self.price_label = QLabel(price_text)
        self.price_label.setFixedWidth(70) # Fixed width for Price
        self.price_label.setStyleSheet(f"font-size: 9pt; color : {label_text_color}")
        self.price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) # Align price to right

        self.position_label = QLabel(book_data.get("Posición", "N/A"))
        self.position_label.setFixedWidth(60) # Fixed width for Position
        self.position_label.setStyleSheet(f"font-size: 9pt; color : {label_text_color}")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Align position to center

        self.image_button = QPushButton()
        self.image_button.clicked.connect(self._handle_image_click) # Conectar una sola vez en __init__
        
        has_image_url = bool(book_data.get("Imagen"))
        icon_to_use_if_url_exists = IMAGE_ICON_PATH
        icon_to_use_if_no_url = NO_VER_ICON_PATH_BLIW

        # print(f"[BookListItemWidget] For book '{book_data.get('Título', 'N/A')}': Has image URL: {has_image_url}") # Less verbose

        if has_image_url:
            # print(f"[BookListItemWidget] Attempting to load icon from: {icon_to_use_if_url_exists}")
            if os.path.exists(icon_to_use_if_url_exists):
                # print(f"[BookListItemWidget] Icon '{os.path.basename(icon_to_use_if_url_exists)}' exists.")
                self.image_button.setIcon(QIcon(icon_to_use_if_url_exists))
                self.image_button.setToolTip("View Image")
                self.image_button.setText("")
            else:
                # print(f"[BookListItemWidget] Advertencia: Icon '{os.path.basename(icon_to_use_if_url_exists)}' NOT FOUND. Using text 'Img'.")
                self.image_button.setIcon(QIcon()) # Clear icon
                self.image_button.setText("Img")
                self.image_button.setToolTip(f"Icon {os.path.basename(icon_to_use_if_url_exists)} not found")
            self.image_button.setEnabled(True)
        else: # No image URL in book data
            # print(f"[BookListItemWidget] No image URL. Attempting to load icon from: {icon_to_use_if_no_url}")
            if os.path.exists(icon_to_use_if_no_url):
                # print(f"[BookListItemWidget] Icon '{os.path.basename(icon_to_use_if_no_url)}' exists for no image URL.")
                self.image_button.setIcon(QIcon(icon_to_use_if_no_url))
                self.image_button.setToolTip("No image available")
                self.image_button.setText("")
            else:
                # print(f"[BookListItemWidget] Advertencia: Fallback icon '{os.path.basename(icon_to_use_if_no_url)}' NOT FOUND. Using text 'No Img'.")
                self.image_button.setIcon(QIcon()) # Clear icon
                self.image_button.setText("NoIm") # Shortened text
                self.image_button.setToolTip(f"No image available and icon {os.path.basename(icon_to_use_if_no_url)} not found")
            self.image_button.setEnabled(False)

        self.image_button.setIconSize(QSize(18, 18))
        self.image_button.setFixedSize(28, 28)
        self.image_button.setCursor(Qt.CursorShape.PointingHandCursor)
        # Basic styling for the button, can be refined
        self.image_button.setStyleSheet("""
            QPushButton { 
                background-color: transparent; 
                border: none; 
                color: #555555; /* Icon/Text color */
            }
            QPushButton:hover { background-color: rgba(0,0,0,0.05); border-radius: 4px; }
        """)

        # Add widgets to layout with stretch factors if needed
        self.main_layout.addWidget(self.title_label, 4) # Title takes more space
        self.main_layout.addWidget(self.author_label, 0) # No stretch, fixed width
        self.main_layout.addWidget(self.category_label, 0) # No stretch, fixed width
        self.main_layout.addWidget(self.price_label, 0) # No stretch, fixed width
        self.main_layout.addWidget(self.position_label, 0) # No stretch, fixed width
        self.main_layout.addWidget(self.image_button, 0) 

        # Set a subtle background for the entire item widget if it's not handled by QListWidget::item style
        # self.setStyleSheet("background-color: rgba(255,255,255,0.05); border-radius: 3px;")


    def _truncate_text(self, text: str, max_length: int) -> str:
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text

    def _handle_image_click(self):
        image_url = self.book_data.get("Imagen")
        if image_url:
            print(f"BookListItemWidget: Image button clicked for: {self.book_data.get('Título')}, URL: {image_url}")
            self.image_view_requested.emit(image_url)
        else:
            print(f"BookListItemWidget: No image URL for {self.book_data.get('Título')}")
    
    def sizeHint(self):
        # Provide a size hint, especially for height, to ensure items are sized consistently
        return QSize(super().sizeHint().width(), 60) # Adjust height as needed

    def update_content(self, book_data: dict):
        self.book_data = book_data
        self.title_label.setText(self._truncate_text(book_data.get("Título", "N/A"), 40))
        self.title_label.setToolTip(book_data.get("Título", "N/A"))
        self.author_label.setText(self._truncate_text(book_data.get("Autor", "N/A"), 20))
        self.author_label.setToolTip(book_data.get("Autor", "N/A"))
        
        categories = book_data.get("Categorías", [])
        category_text = ", ".join(categories) if isinstance(categories, list) else "N/A"
        self.category_label.setText(self._truncate_text(category_text, 22))
        self.category_label.setToolTip(category_text)

        price_value = book_data.get('Precio')
        if price_value is not None:
            try: 
                # Format as integer with thousands separator for Colombian pesos
                price_text = f"$ {int(price_value):,}".replace(",", ".")
            except (ValueError, TypeError): price_text = str(price_value)
        else: price_text = "N/A"
        self.price_label.setText(price_text)
        
        self.position_label.setText(book_data.get("Posición", "N/A"))

        # Update icon/text/state based on image availability
        has_image_url = bool(book_data.get("Imagen"))
        icon_to_use_if_url_exists = IMAGE_ICON_PATH
        icon_to_use_if_no_url = NO_VER_ICON_PATH_BLIW

        # print(f"[BookListItemWidget Update] For book '{book_data.get('Título', 'N/A')}': Has image URL: {has_image_url}")

        if has_image_url:
            if os.path.exists(icon_to_use_if_url_exists):
                self.image_button.setIcon(QIcon(icon_to_use_if_url_exists))
                self.image_button.setToolTip("View Image")
                self.image_button.setText("")
            else:
                self.image_button.setIcon(QIcon()) 
                self.image_button.setText("Img")
                self.image_button.setToolTip(f"Icon {os.path.basename(icon_to_use_if_url_exists)} not found")
            self.image_button.setEnabled(True)
        else: # No image URL in book data
            if os.path.exists(icon_to_use_if_no_url):
                self.image_button.setIcon(QIcon(icon_to_use_if_no_url))
                self.image_button.setToolTip("No image available")
                self.image_button.setText("")
            else:
                self.image_button.setIcon(QIcon()) 
                self.image_button.setText("NoIm") # Shortened text
                self.image_button.setToolTip(f"No image available and icon {os.path.basename(icon_to_use_if_no_url)} not found")
            self.image_button.setEnabled(False)

        # self.image_button.setIconSize(QSize(18, 18)) # Already set in init and update logic

