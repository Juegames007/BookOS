import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QGraphicsBlurEffect, 
    QLabel, QFrame, QSpacerItem, QSizePolicy, QApplication, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QPoint, QEvent, QUrl, QSize, QTimer
from PySide6.QtGui import QIcon, QPainter, QPixmap, QMouseEvent, QFont, QDesktopServices, QScreen

from gui.components.result_list_widget import ResultListWidget
from gui.components.book_detail_widget import BookDetailWidget
from gui.components.book_list_view_widget import BookListViewWidget
from gui.common.styles import FONTS, COLORS

# Attempt to get icon paths, provide defaults if not found
try:
    CURRENT_SCRIPT_DIR_SRW = os.path.dirname(os.path.abspath(__file__))
    # Navigate two levels up (dialogs -> gui -> project_root) then to app/imagenes/
    ICON_BASE_PATH_SRW = os.path.join(os.path.dirname(os.path.dirname(CURRENT_SCRIPT_DIR_SRW)), "app", "imagenes")
    BACK_ICON_PATH = os.path.join(ICON_BASE_PATH_SRW, "atras.png") # Changed to atras.png
    VIEW_TOGGLE_ICON_PATH = os.path.join(ICON_BASE_PATH_SRW, "view_toggle_icon.png") # Icon for view toggle
except NameError:
    BACK_ICON_PATH = ""
    VIEW_TOGGLE_ICON_PATH = ""
    print("Warning: Icon path for atras.png or view_toggle_icon.png could not be determined.")

class SearchResultsWindow(QDialog):
    # INACTIVITY_TIMEOUT_MS_RESULTS = 120000 # Timer logic removed

    def __init__(self, libros_encontrados: list, termino_busqueda: str, parent: QWidget = None, blur_effect=None):
        super().__init__(parent)
        # Removed original setWindowTitle, new title is static
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Darker, more opaque base for better glass effect depth
        self.setStyleSheet("QDialog { background-color: rgba(30, 30, 35, 0.99); border-radius: 12px; }") # Corrected and increased alpha

        self._drag_pos = QPoint()
        self.top_bar_height = 42 # Slightly increased top bar height
        self.setMinimumSize(800, 410) # Reduced minimum height
        self.libros_actuales = [] # Store current books for view updates
        self.termino_busqueda_actual = termino_busqueda

        # Usar el efecto de desenfoque pasado desde el padre
        self._blur_effect = blur_effect
        if self._blur_effect:
            self._blur_effect.setEnabled(False) # Asegurar que empieza deshabilitado

        # --- Main Layout --- (Vertical: Top Bar, Content Area)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6) # Reduced main margin for the card
        self.main_layout.setSpacing(0) 

        # --- Top Bar --- (Horizontal: Back Button, Title, Spacer)
        self.top_bar_widget = QFrame() # Use QFrame for styling options
        self.top_bar_widget.setFixedHeight(self.top_bar_height)
        self.top_bar_widget.setObjectName("topBarResults") # For specific styling if needed
        # Style of top_bar_widget will now be part of the unified_content_card

        top_bar_layout = QHBoxLayout(self.top_bar_widget)
        top_bar_layout.setContentsMargins(8, 0, 8, 0) # Reduced top bar margins
        top_bar_layout.setSpacing(6)

        self.back_button = QPushButton()
        if os.path.exists(BACK_ICON_PATH):
            self.back_button.setIcon(QIcon(BACK_ICON_PATH))
            self.back_button.setIconSize(QSize(18,18))
            # If you have a dark version of the back arrow, use it here.
            # For now, we assume the icon is neutral or we tint it via stylesheet if possible (QIcon doesn't tint easily)
        else:
            self.back_button.setText("<") # Simpler fallback text
        self.back_button.setFixedSize(28, 28)
        # Darker icon/text for light top bar, subtle hover
        self.back_button.setStyleSheet("QPushButton { background-color: transparent; border: none; color: #555555; } QPushButton:hover { background-color: rgba(0,0,0,0.05); border-radius: 4px; }")
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(self.accept) # Back button closes the dialog
        top_bar_layout.addWidget(self.back_button)

        self.window_title_label = QLabel("Search results")
        # Darker text for better visibility on lighter top bar
        title_font = QFont(FONTS.get("family", "Arial"), FONTS.get("size_large", 14), QFont.Weight.DemiBold) # Reduced font size
        self.window_title_label.setFont(title_font)
        self.window_title_label.setStyleSheet(f"color: {COLORS.get('text_primary', '#222222')}; background-color: transparent;")
        top_bar_layout.addWidget(self.window_title_label)

        top_bar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # View Toggle Button
        self.view_toggle_button = QPushButton()
        if os.path.exists(VIEW_TOGGLE_ICON_PATH):
            self.view_toggle_button.setIcon(QIcon(VIEW_TOGGLE_ICON_PATH))
            self.view_toggle_button.setIconSize(QSize(18,18))
        else:
            self.view_toggle_button.setText("≡") # Placeholder for three stripes
        self.view_toggle_button.setFixedSize(28, 28)
        self.view_toggle_button.setStyleSheet("QPushButton { background-color: transparent; border: none; color: #555555; } QPushButton:hover { background-color: rgba(0,0,0,0.05); border-radius: 4px; }")
        self.view_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_toggle_button.clicked.connect(self._toggle_view)
        top_bar_layout.addWidget(self.view_toggle_button)

        # Add other icons (search, menu) here if needed later, as per image

        self.main_layout.addWidget(self.top_bar_widget)

        # --- Unified Content Card (QFrame) --- 
        self.unified_content_card = QFrame()
        self.unified_content_card.setObjectName("unifiedResultsCard")
        # Styles for the card and its embedded top bar
        self.unified_content_card.setStyleSheet(f"""
            QFrame#unifiedResultsCard {{
                background-color: rgba(255, 255, 255, 0.22); /* Less transparent light card */
                border-radius: 10px; /* Slightly less rounded */
                /* border: 1px solid rgba(255, 255, 255, 0.25); Optional subtle border */
            }}
            QFrame#topBarResults {{
                background-color: rgba(255, 255, 255, 0.18); /* Light, slightly more transparent top bar */
                border-bottom: 1px solid rgba(255, 255, 255, 0.2); /* Subtle light separator */
                border-top-left-radius: 10px; 
                border-top-right-radius: 10px;
                border-bottom-left-radius: 0px; 
                border-bottom-right-radius: 0px;
            }}
        """)
        card_main_layout = QVBoxLayout(self.unified_content_card)
        card_main_layout.setContentsMargins(0,0,0,8) # Reduced bottom margin
        card_main_layout.setSpacing(0)

        card_main_layout.addWidget(self.top_bar_widget) # Add top bar to the card

        # --- Stacked Widget for different views ---
        self.view_stack = QStackedWidget()
        self.view_stack.setStyleSheet("background-color: transparent;")

        # --- View 1: Detail View (Current Sidebar + Detail Pane) ---
        self.detail_view_widget = QWidget()
        self.detail_view_widget.setStyleSheet("background-color: transparent;")
        detail_view_layout = QHBoxLayout(self.detail_view_widget)
        detail_view_layout.setContentsMargins(8, 8, 8, 0)
        detail_view_layout.setSpacing(8)

        self.result_list_widget = ResultListWidget()
        # Set a maximum width for the list widget to control its size
        self.result_list_widget.setMaximumWidth(240) # Increased width
        self.book_detail_widget = BookDetailWidget()
        self.book_detail_widget.setStyleSheet("QFrame#bookDetailFrame { background-color: transparent; border: none; }")

        detail_view_layout.addWidget(self.result_list_widget, 2) # Adjusted stretch factor (e.g. 2 out of 5 parts)
        detail_view_layout.addWidget(self.book_detail_widget, 3) # Adjusted stretch factor (e.g. 3 out of 5 parts)
        
        self.view_stack.addWidget(self.detail_view_widget)

        # --- View 2: Row/List View ---
        self.book_list_view_widget = BookListViewWidget() 
        self.view_stack.addWidget(self.book_list_view_widget)

        card_main_layout.addWidget(self.view_stack, 1)
        self.main_layout.addWidget(self.unified_content_card, 1)
        
        # Connect signals
        self.result_list_widget.item_selected.connect(self.book_detail_widget.update_details)
        self.book_detail_widget.image_view_requested.connect(self._handle_image_view_request)
        # Connect the BookListViewWidget's signal as well
        if hasattr(self, 'book_list_view_widget') and self.book_list_view_widget:
            self.book_list_view_widget.image_view_requested.connect(self._handle_image_view_request)

        # Initial content update
        self.update_content(libros_encontrados, termino_busqueda)
        
        self.setModal(True) # Set dialog to be modal
        # Timer logic removed
        # Event filter for timer removed

    def _center_window(self):
        # Use frameGeometry().size() for dimensions including the window frame
        dialog_frame_size = self.frameGeometry().size() 
        parent = self.parent()

        if parent:
            parent_geometry = parent.geometry()
            # Center relative to the parent's client area
            target_center_x = parent_geometry.x() + parent_geometry.width() / 2
            target_center_y = parent_geometry.y() + parent_geometry.height() / 2
        else:
            current_screen = self.screen()
            if not current_screen: # Fallback if self.screen() is None early
                current_screen = QApplication.primaryScreen()
            
            if current_screen:
                screen_geometry = current_screen.availableGeometry()
                # Center relative to the screen's available geometry
                target_center_x = screen_geometry.x() + screen_geometry.width() / 2
                target_center_y = screen_geometry.y() + screen_geometry.height() / 2
            else:
                return # Cannot center if no screen info
            
        # Calculate new top-left position for the dialog's frame
        new_x = target_center_x - dialog_frame_size.width() / 2
        new_y = target_center_y - dialog_frame_size.height() / 2
        
        self.move(int(new_x), int(new_y))

    def _handle_image_view_request(self, image_url: str):
        if image_url:
            print(f"[SearchResultsWindow] Handling image_view_request for URL: {image_url}")
            QDesktopServices.openUrl(QUrl(image_url))

    # Event filter for timer removed
    # def eventFilter(self, obj, event: QEvent):
    #     return super().eventFilter(obj, event)

    # Blur enabling/disabling logic (kept as is for now)
    def _enable_blur(self, enable: bool):
        if self._blur_effect:
            self._blur_effect.setEnabled(enable)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent(): self._enable_blur(True)
        QTimer.singleShot(0, self._center_window) # Defer centering

    def exec(self):
        if self.parent(): self._enable_blur(True)
        result = super().exec()
        if self.parent() and self._blur_effect: self._enable_blur(False)
        return result

    def accept(self):
        if self.parent() and self._blur_effect: self._enable_blur(False)
        super().accept()

    def reject(self):
        if self.parent() and self._blur_effect: self._enable_blur(False)
        super().reject()
    
    def closeEvent(self, event):
        if self.parent() and self._blur_effect: self._enable_blur(False)
        super().closeEvent(event)

    # Mouse events for dragging (now considers top_bar_widget as part of unified_content_card)
    def mousePressEvent(self, event: QMouseEvent):
        # Dragging should be based on the position relative to the unified_content_card's top bar area
        if event.button() == Qt.MouseButton.LeftButton and \
           self.unified_content_card.geometry().contains(event.pos()) and \
           event.pos().y() < (self.unified_content_card.y() + self.top_bar_height): # Check y relative to main dialog
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event) 

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = QPoint()
        super().mouseReleaseEvent(event)

    # PaintEvent is likely not needed for main dialog if children handle their backgrounds
    # and WA_TranslucentBackground is used. If a specific overall background image or effect
    # for the dialog itself is needed (behind the semi-transparent main_layout), it would go here.
    # For now, main_layout's QFrame and QDialog's WA_TranslucentBackground handle it.
    # def paintEvent(self, event):
    #     super().paintEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.accept()
        # Up/Down arrow keys are now primarily handled by ResultListWidget if it has focus.
        # However, SearchResultsWindow can also catch them if ResultListWidget doesn't consume them.
        # Let's delegate to ResultListWidget's methods if it's the one that should react.
        elif event.key() == Qt.Key_Up:
            self.result_list_widget._scroll_up() # Call the method directly
        elif event.key() == Qt.Key_Down:
            self.result_list_widget._scroll_down() # Call the method directly
        else:
            super().keyPressEvent(event)

    def _toggle_view(self):
        current_index = self.view_stack.currentIndex()
        next_index = (current_index + 1) % self.view_stack.count()
        # Ensure count is not zero to prevent modulo by zero if stack is empty (shouldn't happen here)
        if self.view_stack.count() > 0:
            next_index = (current_index + 1) % self.view_stack.count()
            self.view_stack.setCurrentIndex(next_index)
        # Potentially update button icon/text based on current view
        # if next_index == 0: self.view_toggle_button.setText("≡") 
        # else: self.view_toggle_button.setText("□") # Example for switching icon

    def update_content(self, libros_encontrados: list, termino_busqueda: str):
        self.libros_actuales = libros_encontrados
        self.termino_busqueda_actual = termino_busqueda
        
        self.result_list_widget.update_results(libros_encontrados)
        if libros_encontrados:
            self.book_detail_widget.update_details(libros_encontrados[0])
            self.result_list_widget.set_selected_index(0)
        else:
            self.book_detail_widget.update_details({})
        
        # Update other views if they exist and are implemented
        if hasattr(self, 'book_list_view_widget') and self.book_list_view_widget:
            self.book_list_view_widget.update_results(libros_encontrados)

# Example Usage for the new SearchResultsWindow
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    
    # Mock FONTS and COLORS if not available in your project structure
    if 'FONTS' not in globals():
        FONTS = {"family": "Arial", "size_large": 16, "size_normal": 12}
    if 'COLORS' not in globals():
        COLORS = {"text_primary": "#222222", "text_light": "#EAEAEA"}

    # Mock data
    mock_libros = [
        {"Título": "El Viaje del Descubridor Cósmico Extralargo para Probar Truncamiento", "Autor": "Aurora Sendero Estelar", "Categorías": ["Sci-Fi Galáctico"], "Posición": "SF-A1-Omega", "Imagen": ""},
        {"Título": "Secretos de Cocina Antigua", "Autor": "Gastón Gourmet III", "Categorías": ["Cocina Milenaria"], "Posición": "CK-B3-Delta", "Imagen": "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?q=80&w=100&auto=format&fit=crop"},
        {"Título": "Aventuras en Bosque Nublado", "Autor": "Natura Amiga del Bosque", "Categorías": ["Aventura Selvática", "Naturaleza Virgen"], "Posición": "AV-C9-Gamma", "Imagen": ""}
    ]
    empty_libros = []

    dialog = SearchResultsWindow(mock_libros, "prueba", parent=None) # Pass None if no parent for test
    # dialog = SearchResultsWindow(empty_libros, "nada", parent=None)
    dialog.show()
    
    sys.exit(app.exec()) 