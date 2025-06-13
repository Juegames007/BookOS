from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon # For icons on buttons
import os
from typing import List, Dict, Any

from .search_result_item_widget import SearchResultItemWidget
from gui.components.image_manager import ImageManager

MAX_CHARS_SIDEBAR_TITLE = 25 # Increased max characters

# --- Icon Paths for Navigation Buttons (assuming they are in app/imagenes) ---
try:
    CURRENT_SCRIPT_DIR_RLW = os.path.dirname(os.path.abspath(__file__))
    ICON_BASE_PATH_RLW = os.path.join(os.path.dirname(os.path.dirname(CURRENT_SCRIPT_DIR_RLW)), "app", "imagenes")
    UP_ARROW_ICON_PATH = os.path.join(ICON_BASE_PATH_RLW, "arriba.png")
    DOWN_ARROW_ICON_PATH = os.path.join(ICON_BASE_PATH_RLW, "abajo.png")
except NameError:
    UP_ARROW_ICON_PATH = ""
    DOWN_ARROW_ICON_PATH = ""
    print("Warning: Icon paths for up/down arrows could not be determined.")

def truncate_title_sidebar(title: str, max_chars: int = MAX_CHARS_SIDEBAR_TITLE) -> str:
    if not title:
        return "N/A"
    if len(title) <= max_chars:
        return title

    words = title.split()
    if not words:
        return "N/A"

    # If the first word itself is longer than max_chars
    if len(words[0]) > max_chars:
        return words[0][:max_chars - 3] + "..."
    
    current_truncated_title = ""
    for i, word in enumerate(words):
        if i == 0:
            next_title_part = word
        else:
            next_title_part = current_truncated_title + " " + word

        if len(next_title_part) <= max_chars:
            current_truncated_title = next_title_part
        else:
            if not current_truncated_title: 
                 return word[:max_chars - 3] + "..." 
            if len(current_truncated_title + "...") <= max_chars:
                 return current_truncated_title + "..."
            else:
                 if len(current_truncated_title) > 3 and ' ' in current_truncated_title:
                     temp_title_parts = current_truncated_title.split(' ')
                     shorter_title = ""
                     for k_part, part in enumerate(temp_title_parts):
                         if k_part == 0:
                             if len(part + "...") <= max_chars:
                                 shorter_title = part
                             else:
                                 return part[:max_chars-3] + "..."
                         else:
                             if len(shorter_title + " " + part + "...") <= max_chars:
                                 shorter_title += " " + part
                             else:
                                 break
                     if shorter_title: return shorter_title + "..."
                 return current_truncated_title[:max_chars-3] + "..."

    if len(current_truncated_title) < len(title) and not current_truncated_title.endswith("..."):
        if len(current_truncated_title + "...") <= max_chars:
            return current_truncated_title + "..."
        else:
            return current_truncated_title[:max_chars-3] + "..."
            
    return current_truncated_title

class ResultListWidget(QWidget):
    item_selected = Signal(dict) # Emits the full book data of the selected item
    # item_hovered = Signal(dict) # Optional: for hover effects if needed

    def __init__(self, image_manager: ImageManager, books: List[Dict[str, Any]] = None, parent: QWidget = None):
        super().__init__(parent)
        self.books_data = [] 
        self.image_manager = image_manager

        self.main_v_layout = QVBoxLayout(self) # Main layout for list + buttons
        self.main_v_layout.setContentsMargins(0,0,0,0)
        self.main_v_layout.setSpacing(5)

        self.list_widget = QListWidget()
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent; /* Main list bg is transparent, items are cards */
                border: none; /* No border for the list widget itself */
                padding: 4px; /* Slightly increased padding */
                font-size: 13.5px; /* Slightly increased font size */
                outline: 0; /* Remove focus outline */
            }
            QListWidget::item {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin-bottom: 5px;
            }
            QListWidget::item:selected {
                background-color: rgba(0, 0, 0, 0.05); /* Highlight behind the widget */
                border-radius: 6px;
            }
        """)
        self.main_v_layout.addWidget(self.list_widget, 1) # List takes most space

        # Navigation Buttons Layout
        nav_buttons_layout = QHBoxLayout()
        nav_buttons_layout.setSpacing(8) # Reduced spacing
        nav_buttons_layout.addStretch()

        self.up_button = QPushButton()
        if os.path.exists(UP_ARROW_ICON_PATH):
            self.up_button.setIcon(QIcon(UP_ARROW_ICON_PATH))
            self.up_button.setIconSize(QSize(16,16)) # Further reduced icon size
        else:
            self.up_button.setText("^")
        self.up_button.setFixedSize(26,26) # Further reduced button size
        self.up_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.3); /* Slightly less transparent button */
                border: 1px solid rgba(255, 255, 255, 0.35);
                color: #444444; /* Darker text/icon for light buttons */
                border-radius: 14px; /* More rounded for small buttons */ 
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.4); }
            QPushButton:pressed { background-color: rgba(255, 255, 255, 0.35); }
            QPushButton:disabled { background-color: rgba(200, 200, 200, 0.15); color: rgba(150,150,150,0.7); border-color: rgba(200,200,200,0.25); }
        """)
        self.up_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.up_button.clicked.connect(self._scroll_up)
        nav_buttons_layout.addWidget(self.up_button)

        self.down_button = QPushButton()
        if os.path.exists(DOWN_ARROW_ICON_PATH):
            self.down_button.setIcon(QIcon(DOWN_ARROW_ICON_PATH))
            self.down_button.setIconSize(QSize(16,16)) # Further reduced icon size
        else:
            self.down_button.setText("v")
        self.down_button.setFixedSize(26,26) # Further reduced button size
        self.down_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.3); /* Slightly less transparent button */
                border: 1px solid rgba(255, 255, 255, 0.35);
                color: #444444; /* Darker text/icon for light buttons */
                border-radius: 14px; /* More rounded for small buttons */ 
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.4); }
            QPushButton:pressed { background-color: rgba(255, 255, 255, 0.35); }
            QPushButton:disabled { background-color: rgba(200, 200, 200, 0.15); color: rgba(150,150,150,0.7); border-color: rgba(200,200,200,0.25); }
        """)
        self.down_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.down_button.clicked.connect(self._scroll_down)
        nav_buttons_layout.addWidget(self.down_button)
        
        nav_buttons_layout.addStretch()
        self.main_v_layout.addLayout(nav_buttons_layout)
        self.main_v_layout.setStretchFactor(self.list_widget, 1)

        self.list_widget.currentItemChanged.connect(self._on_item_selection_changed)
        # self.list_widget.itemEntered.connect(self._on_item_hovered) # If hover signal is needed

        if books:
            self.update_results(books)
        self._update_nav_buttons_state() # Initial state

    def _scroll_up(self):
        current_row = self.list_widget.currentRow()
        if current_row > 0:
            self.list_widget.setCurrentRow(current_row - 1)

    def _scroll_down(self):
        current_row = self.list_widget.currentRow()
        if current_row < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(current_row + 1)

    def _update_nav_buttons_state(self):
        count = self.list_widget.count()
        current_row = self.list_widget.currentRow()
        self.up_button.setEnabled(count > 0 and current_row > 0)
        self.down_button.setEnabled(count > 0 and current_row < count - 1)

    def update_results(self, books: List[Dict[str, Any]]):
        self.list_widget.clear()
        self.books_data = list(books) 

        if not self.books_data:
            no_results_item = QListWidgetItem("No results found")
            no_results_item.setFlags(no_results_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            no_results_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            no_results_item.setForeground(Qt.GlobalColor.gray) # Make it look disabled
            self.list_widget.addItem(no_results_item)
            self.item_selected.emit({}) # Emit empty dict if no results
            self._update_nav_buttons_state() # Ensure buttons are updated for empty list
            return

        for book in self.books_data:
            list_item = QListWidgetItem(self.list_widget)
            item_widget = SearchResultItemWidget(book, self.image_manager)
            
            list_item.setSizeHint(item_widget.sizeHint())
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, item_widget)
            
            # Store the original data in the item
            list_item.setData(Qt.ItemDataRole.UserRole, book)
        
        if self.list_widget.count() > 0:
            # Check if the first item is selectable before trying to select it
            first_item = self.list_widget.item(0)
            if first_item and (first_item.flags() & Qt.ItemFlag.ItemIsSelectable):
                self.list_widget.setCurrentRow(0)
                if self.books_data: 
                    self.item_selected.emit(self.books_data[0])
            elif self.books_data: # If first is not selectable (e.g. "No results"), but there is data
                 self.item_selected.emit({}) # Clear details or emit first valid book if logic changes
        self._update_nav_buttons_state()

    def _on_item_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        self._update_nav_buttons_state()
        if current and (current.flags() & Qt.ItemFlag.ItemIsSelectable): # Check if selectable
            row = self.list_widget.row(current)
            if 0 <= row < len(self.books_data):
                selected_book = self.books_data[row]
                self.item_selected.emit(selected_book)
                self.list_widget.scrollToItem(current, QListWidget.ScrollHint.EnsureVisible) # Ensure selected is visible
        # else: # If item is not selectable (e.g. "No results found") or list cleared
            # If you want to clear details when "No results found" is effectively selected:
            # if current and not (current.flags() & Qt.ItemFlag.ItemIsSelectable):
            #     self.item_selected.emit({}) 

    # def _on_item_hovered(self, item: QListWidgetItem): # Example for hover
    #     row = self.list_widget.row(item)
    #     if 0 <= row < len(self.books_data):
    #         hovered_book = self.books_data[row]
    #         self.item_hovered.emit(hovered_book)

    def set_selected_index(self, index: int):
        if 0 <= index < self.list_widget.count() and self.list_widget.item(index).flags() & Qt.ItemFlag.ItemIsSelectable:
            self.list_widget.setCurrentRow(index)
        elif self.list_widget.count() > 0:
            first_selectable = -1
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).flags() & Qt.ItemFlag.ItemIsSelectable:
                    first_selectable = i
                    break
            if first_selectable != -1:
                self.list_widget.setCurrentRow(first_selectable)
        self._update_nav_buttons_state()

    def get_current_selected_book_data(self) -> Dict[str, Any] | None:
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None 