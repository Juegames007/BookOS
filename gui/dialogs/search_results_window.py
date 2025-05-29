import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QGraphicsBlurEffect, 
    QLabel, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPoint, QEvent, QUrl, QSize
from PySide6.QtGui import QIcon, QPainter, QPixmap, QMouseEvent, QFont, QDesktopServices

from gui.components.result_list_widget import ResultListWidget
from gui.components.book_detail_widget import BookDetailWidget
from gui.common.styles import FONTS, COLORS

# Attempt to get icon paths, provide defaults if not found
try:
    CURRENT_SCRIPT_DIR_SRW = os.path.dirname(os.path.abspath(__file__))
    # Navigate two levels up (dialogs -> gui -> project_root) then to app/imagenes/
    ICON_BASE_PATH_SRW = os.path.join(os.path.dirname(os.path.dirname(CURRENT_SCRIPT_DIR_SRW)), "app", "imagenes")
    BACK_ICON_PATH = os.path.join(ICON_BASE_PATH_SRW, "back_arrow.png") # Create/get a suitable back arrow icon
except NameError:
    BACK_ICON_PATH = ""
    print("Warning: Icon path for back_arrow.png could not be determined.")

class SearchResultsWindow(QDialog):
    # INACTIVITY_TIMEOUT_MS_RESULTS = 120000 # Timer logic removed

    def __init__(self, libros_encontrados: list, termino_busqueda: str, parent: QWidget = None):
        super().__init__(parent)
        # Removed original setWindowTitle, new title is static
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Darker, more opaque base for better glass effect depth
        self.setStyleSheet("QDialog { background-color: rgba(30, 30, 35, 0.85); border-radius: 12px; }")

        self._drag_pos = QPoint()
        self.top_bar_height = 45 # Reduced top bar height
        self.setMinimumSize(780, 530) # Slightly reduced overall size

        # Blur effect logic (kept as is for now)
        self._blur_effect = None
        if self.parent():
            self._blur_effect = QGraphicsBlurEffect()
            self._blur_effect.setBlurRadius(15) # Increased blur radius for more glass effect
            self._blur_effect.setEnabled(False)
            target_widget_for_blur = None
            if hasattr(self.parent(), 'centralWidget') and self.parent().centralWidget():
                 target_widget_for_blur = self.parent().centralWidget()
            elif hasattr(self.parent(), 'current_stacked_widget') and self.parent().current_stacked_widget:
                 target_widget_for_blur = self.parent().current_stacked_widget
            
            if target_widget_for_blur:
                target_widget_for_blur.setGraphicsEffect(self._blur_effect)
            else:
                print("Advertencia: SearchResultsWindow no pudo encontrar un widget central en el padre para aplicar el desenfoque.")

        # --- Main Layout --- (Vertical: Top Bar, Content Area)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8) # Reduced main margin for the card
        self.main_layout.setSpacing(0) 

        # --- Top Bar --- (Horizontal: Back Button, Title, Spacer)
        self.top_bar_widget = QFrame() # Use QFrame for styling options
        self.top_bar_widget.setFixedHeight(self.top_bar_height)
        self.top_bar_widget.setObjectName("topBarResults") # For specific styling if needed
        # Style of top_bar_widget will now be part of the unified_content_card

        top_bar_layout = QHBoxLayout(self.top_bar_widget)
        top_bar_layout.setContentsMargins(10, 0, 10, 0) # Reduced top bar margins
        top_bar_layout.setSpacing(8)

        self.back_button = QPushButton()
        if os.path.exists(BACK_ICON_PATH):
            self.back_button.setIcon(QIcon(BACK_ICON_PATH))
            self.back_button.setIconSize(QSize(20,20))
            # If you have a dark version of the back arrow, use it here.
            # For now, we assume the icon is neutral or we tint it via stylesheet if possible (QIcon doesn't tint easily)
        else:
            self.back_button.setText("<") # Simpler fallback text
        self.back_button.setFixedSize(30, 30)
        # Darker icon/text for light top bar, subtle hover
        self.back_button.setStyleSheet("QPushButton { background-color: transparent; border: none; color: #555555; } QPushButton:hover { background-color: rgba(0,0,0,0.05); border-radius: 4px; }")
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(self.accept) # Back button closes the dialog
        top_bar_layout.addWidget(self.back_button)

        self.window_title_label = QLabel("Search results")
        # Darker text for better visibility on lighter top bar
        title_font = QFont(FONTS.get("family", "Arial"), FONTS.get("size_large", 16), QFont.Weight.DemiBold)
        self.window_title_label.setFont(title_font)
        self.window_title_label.setStyleSheet(f"color: {COLORS.get('text_primary', '#222222')}; background-color: transparent;")
        top_bar_layout.addWidget(self.window_title_label)

        top_bar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
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
        card_main_layout.setContentsMargins(0,0,0,10) # Reduced bottom margin
        card_main_layout.setSpacing(0)

        card_main_layout.addWidget(self.top_bar_widget) # Add top bar to the card

        # --- Content Area within the Card --- 
        self.content_area_widget_internal = QWidget() # This QWidget is inside the card_main_layout
        self.content_area_widget_internal.setStyleSheet("background-color: transparent;")
        content_area_layout_internal = QHBoxLayout(self.content_area_widget_internal)
        content_area_layout_internal.setContentsMargins(10, 10, 10, 0) # Reduced padding
        content_area_layout_internal.setSpacing(10) # Reduced spacing

        self.result_list_widget = ResultListWidget()
        # Set a maximum width for the list widget to control its size
        self.result_list_widget.setMaximumWidth(280) # Adjust as needed
        self.book_detail_widget = BookDetailWidget()
        self.book_detail_widget.setStyleSheet("QFrame#bookDetailFrame { background-color: transparent; border: none; }")

        content_area_layout_internal.addWidget(self.result_list_widget, 2) # Adjusted stretch factor (e.g. 2 out of 5 parts)
        content_area_layout_internal.addWidget(self.book_detail_widget, 3) # Adjusted stretch factor (e.g. 3 out of 5 parts)
        
        card_main_layout.addWidget(self.content_area_widget_internal, 1)
        self.main_layout.addWidget(self.unified_content_card, 1)
        
        # Connect signals
        self.result_list_widget.item_selected.connect(self.book_detail_widget.update_details)
        self.book_detail_widget.image_view_requested.connect(self._handle_image_view_request)

        # Initial content update
        self.update_content(libros_encontrados, termino_busqueda)
        
        self.setModal(False)
        # Timer logic removed
        # Event filter for timer removed

    def _handle_image_view_request(self, image_url: str):
        if image_url:
            QDesktopServices.openUrl(QUrl(image_url))

    # Event filter for timer removed
    # def eventFilter(self, obj, event: QEvent):
    #     return super().eventFilter(obj, event)

    # Blur enabling/disabling logic (kept as is for now)
    def _enable_blur(self, enable: bool):
        if not self.parent() or not self._blur_effect:
            return
        target_widget = None
        if hasattr(self.parent(), 'centralWidget') and self.parent().centralWidget():
            target_widget = self.parent().centralWidget()
        elif hasattr(self.parent(), 'current_stacked_widget') and self.parent().current_stacked_widget:
            target_widget = self.parent().current_stacked_widget
        if not target_widget: return
        if enable:
            if target_widget.graphicsEffect() != self._blur_effect:
                target_widget.setGraphicsEffect(self._blur_effect)
            self._blur_effect.setEnabled(True)
        else:
            if target_widget.graphicsEffect() == self._blur_effect:
                self._blur_effect.setEnabled(False)
                target_widget.setGraphicsEffect(None)
        target_widget.update()

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent(): self._enable_blur(True)

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

    def update_content(self, libros_encontrados: list, termino_busqueda: str):
        # The window title in the top bar is static "Search results"
        # self.window_title_label.setText(f"Search results for: '{termino_busqueda}'") # If dynamic title needed
        self.result_list_widget.update_results(libros_encontrados)
        # Automatically select first item and update detail view if results exist
        if libros_encontrados:
            self.book_detail_widget.update_details(libros_encontrados[0])
            self.result_list_widget.set_selected_index(0)
        else:
            self.book_detail_widget.update_details({}) # Clear details if no results

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