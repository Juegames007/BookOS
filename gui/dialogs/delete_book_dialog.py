"""
Diálogo para la gestión de eliminación y reducción de existencias de libros.
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
    QWidget, QMessageBox, QInputDialog, QSpacerItem, QSizePolicy, QComboBox
)
from PySide6.QtGui import QFont, QPixmap, QIcon, QFontDatabase
from PySide6.QtCore import Qt, QSize, QTimer

from features.delete_service import DeleteService
from gui.common.utils import get_icon_path, format_price
from gui.components.image_manager import ImageManager

class DeleteBookDialog(QDialog):
    """
    Diálogo rediseñado para buscar, visualizar y gestionar la eliminación de libros.
    """
    def __init__(self, delete_service: DeleteService, parent=None):
        super().__init__(parent)
        self.delete_service = delete_service
        self.current_book_data = None
        self.inventory_entries = []

        self.image_manager = ImageManager()
        self.image_manager.image_loaded.connect(self._on_image_loaded)

        self.setWindowTitle("Eliminar Libro")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._load_fonts()
        self._setup_ui()
        self._connect_signals()
        
        QTimer.singleShot(0, self.adjustSize)
        self.isbn_input.setFocus()

    def _load_fonts(self):
        font_dir = os.path.join(os.path.dirname(__file__), '..', 'resources', 'fonts')
        for font_file in ["Montserrat-Regular.ttf", "Montserrat-Bold.ttf", "Montserrat-SemiBold.ttf"]:
            font_path = os.path.join(font_dir, font_file)
            if os.path.exists(font_path):
                QFontDatabase.addApplicationFont(font_path)

    def _setup_ui(self):
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.content_layout = QVBoxLayout(self.main_frame)
        self.content_layout.setContentsMargins(40, 30, 40, 30)
        self.content_layout.setSpacing(25)
        
        self.content_layout.addLayout(self._create_header())
        self.content_layout.addLayout(self._create_search_layout())

        self.details_container = QWidget()
        self.details_container.setVisible(False)
        self.content_layout.addWidget(self.details_container)
        
        details_main_layout = QHBoxLayout(self.details_container)
        details_main_layout.setContentsMargins(0, 15, 0, 0)
        details_main_layout.setSpacing(30)

        details_main_layout.addLayout(self._create_left_panel(), 2)
        details_main_layout.addLayout(self._create_right_panel(), 1)

        self._apply_stylesheet()

    def _create_header(self):
        header_layout = QHBoxLayout()
        title_label = QLabel("Eliminar Libro")
        title_label.setObjectName("dialogTitle")
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(35, 35)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setAutoDefault(False)
        close_btn.clicked.connect(self.reject)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        return header_layout

    def _create_search_layout(self):
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("Ingresar ISBN del libro a buscar...")
        self.isbn_input.setFixedHeight(50)

        self.search_button = QPushButton("Buscar")
        self.search_button.setObjectName("searchButton")
        self.search_button.setFixedHeight(50)
        self.search_button.setCursor(Qt.PointingHandCursor)
        self.search_button.setAutoDefault(False)

        search_layout.addWidget(self.isbn_input, 1)
        search_layout.addWidget(self.search_button)
        return search_layout

    def _create_left_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        self.book_title_label = QLabel("Título del Libro")
        self.book_title_label.setObjectName("bookTitle")
        self.book_title_label.setWordWrap(True)

        self.book_author_label = QLabel("Autor del Libro")
        self.book_author_label.setObjectName("bookInfo")

        self.book_price_label = QLabel("Precio: N/A")
        self.book_price_label.setObjectName("bookInfo")
        
        layout.addWidget(self.book_title_label, 0, Qt.AlignTop)
        layout.addWidget(self.book_author_label, 0, Qt.AlignTop)
        layout.addWidget(self.book_price_label, 0, Qt.AlignTop)
        
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        self.position_label = QLabel("Posición: N/A")
        self.position_label.setObjectName("bookInfo")
        
        self.inventory_combo = QComboBox()
        self.inventory_combo.setFixedHeight(40)
        
        self.book_quantity_label = QLabel("Cantidad: N/A")
        self.book_quantity_label.setObjectName("bookInfo")
        
        layout.addWidget(self.position_label)
        layout.addWidget(self.inventory_combo)
        layout.addWidget(self.book_quantity_label)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        self.decrease_qty_button = QPushButton("Disminuir Cantidad")
        self.decrease_qty_button.setObjectName("decreaseButton")
        self.decrease_qty_button.setEnabled(False)
        self.decrease_qty_button.setAutoDefault(False)
        self.decrease_qty_button.setCursor(Qt.PointingHandCursor)
        
        self.delete_permanently_button = QPushButton("Eliminar Libro")
        self.delete_permanently_button.setObjectName("deleteButton")
        self.delete_permanently_button.setAutoDefault(False)
        self.delete_permanently_button.setEnabled(False)
        self.delete_permanently_button.setCursor(Qt.PointingHandCursor)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.decrease_qty_button)
        buttons_layout.addWidget(self.delete_permanently_button)
        
        layout.addStretch()
        layout.addLayout(buttons_layout)
        return layout
        
    def _create_right_panel(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.image_label = QLabel()
        self.image_label.setFixedSize(220, 330)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setObjectName("imageLabel")
        layout.addWidget(self.image_label)
        return layout

    def _apply_stylesheet(self):
        self.main_frame.setStyleSheet("""
            #mainFrame {
                background-color: rgba(243, 244, 246, 0.5);
                border-radius: 20px;
                border: 1px solid rgba(0, 0, 0, 0.08);
            }
            #dialogTitle {
                font-family: 'Montserrat'; font-size: 30px; font-weight: bold;
                color: #1F2937; background: transparent;
            }
            #closeButton {
                font-size: 18px; font-weight: bold; color: #6B7280;
                background-color: #E5E7EB; border: none; border-radius: 17px;
            }
            #closeButton:hover { background-color: #D1D5DB; }
            QLineEdit, QComboBox {
                background-color: #FFFFFF; border: 1px solid #D1D5DB;
                font-size: 15px; border-radius: 10px; padding: 0 15px; color: #1F2937;
                font-family: 'Montserrat';
            }
            QComboBox::drop-down { border: none; }
            #searchButton {
                font-family: 'Montserrat'; font-size: 15px; font-weight: bold;
                padding: 10px 22px; border-radius: 10px; border: none;
                background-color: #1F2937; color: white;
            }
            #searchButton:hover { background-color: #111827; }
            #bookTitle {
                font-family: 'Montserrat'; font-size: 24px; font-weight: bold;
                color: #1F2937; background: transparent;
            }
            #bookInfo {
                font-family: 'Montserrat'; font-size: 17px;
                color: #4B5563; background: transparent;
            }
            #imageLabel {
                background-color: #E5E7EB; border-radius: 12px;
                color: #9CA3AF; font-size: 16px; border: 1px solid #D1D5DB;
            }
            #decreaseButton, #deleteButton {
                font-family: 'Montserrat'; font-size: 14px; font-weight: bold;
                padding: 12px 20px; border-radius: 10px; border: none;
            }
            #decreaseButton { background-color: #4B5563; color: white; }
            #decreaseButton:hover { background-color: #374151; }
            #decreaseButton:disabled { background-color: #D1D5DB; color: #9CA3AF; }
            #deleteButton { background-color: #EF4444; color: white; }
            #deleteButton:hover { background-color: #DC2626; }
            #deleteButton:disabled { background-color: #FCA5A5; color: #FEE2E2; }
        """)

    def _connect_signals(self):
        self.isbn_input.returnPressed.connect(self._find_book)
        self.search_button.clicked.connect(self._find_book)
        self.inventory_combo.currentIndexChanged.connect(self._update_quantity_label)
        self.decrease_qty_button.clicked.connect(self._decrease_quantity)
        self.delete_permanently_button.clicked.connect(self._delete_book_permanently)

    def _find_book(self):
        isbn = self.isbn_input.text().strip()
        if not isbn: return
        
        self._reset_view(is_new_search=False)
        result = self.delete_service.find_book_for_deletion(isbn)
        
        if result["status"] == "not_found":
            QMessageBox.warning(self, "No Encontrado", f"No se encontró ningún libro con el ISBN: {isbn}")
            self.isbn_input.selectAll()
            return
        
        self.current_book_data = result["book_details"]
        self.inventory_entries = result["inventory_entries"]
        self.image_manager.get_image(self.current_book_data.get('ISBN', ''), self.current_book_data.get('Imagen', ''))
        
        self._display_book_info()
        self._display_inventory_info()
        self.delete_permanently_button.setEnabled(True)
        self.details_container.setVisible(True)
        QTimer.singleShot(0, self.adjustSize)

    def _on_image_loaded(self, image_id, pixmap):
        if self.current_book_data and image_id == self.current_book_data.get('ISBN'):
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("Imagen no disponible")

    def _display_book_info(self):
        if not self.current_book_data: return
        self.book_title_label.setText(self.current_book_data.get('Título', 'N/A'))
        self.book_author_label.setText(f"Por: {self.current_book_data.get('Autor', 'N/A')}")
        self.book_price_label.setText(f"Precio: {format_price(self.current_book_data.get('Precio', 0))}")

    def _display_inventory_info(self):
        num_entries = len(self.inventory_entries)
        
        if num_entries == 0:
            self.position_label.setText("Posición: N/A")
            self.book_quantity_label.setText("Cantidad: 0")
            self.position_label.show()
            self.inventory_combo.hide()
            self.decrease_qty_button.setEnabled(False)
        elif num_entries == 1:
            entry = self.inventory_entries[0]
            self.position_label.setText(f"Posición: {entry['posicion']}")
            self.book_quantity_label.setText(f"Cantidad: {entry['cantidad']}")
            self.position_label.show()
            self.inventory_combo.hide()
            self.decrease_qty_button.setEnabled(True)
        else: # More than 1 entry
            self.inventory_combo.clear()
            for entry in self.inventory_entries:
                self.inventory_combo.addItem(f"{entry['posicion']} (Cantidad: {entry['cantidad']})", userData=entry)
            self.position_label.hide()
            self.inventory_combo.show()
            self._update_quantity_label(0)

        self.inventory_combo.setEnabled(len(self.inventory_entries) > 1)

    def _update_quantity_label(self, index):
        if index < 0:
            self.book_quantity_label.setText("Cantidad: -")
            self.decrease_qty_button.setEnabled(False)
            return

        selected_entry = self.inventory_combo.itemData(index)
        if selected_entry:
            self.book_quantity_label.setText(f"Cantidad: {selected_entry['cantidad']}")
            self.decrease_qty_button.setEnabled(True)
            self.delete_permanently_button.setEnabled(True)
        else:
            self.book_quantity_label.setText("Cantidad: 0")
            self.decrease_qty_button.setEnabled(False)
            self.delete_permanently_button.setEnabled(False)

    def _decrease_quantity(self):
        current_entry = self.inventory_combo.currentData()
        if not current_entry: return
        
        success, message = self.delete_service.decrease_inventory_quantity(current_entry['id_inventario'])
        
        if success:
            QMessageBox.information(self, "Éxito", "La cantidad ha sido disminuida en 1.")
            self._find_book() # Recargar
        else:
            QMessageBox.critical(self, "Error", message)

    def _delete_book_permanently(self):
        if not self.current_book_data: return
        
        isbn = self.current_book_data.get('ISBN')
        title = self.current_book_data.get('Título')
        
        reply = QMessageBox.question(self, "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar permanentemente el libro '{title}' (ISBN: {isbn}) "
            "y todas sus existencias del inventario? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
            
        if reply == QMessageBox.StandardButton.No:
            return
            
        success, message = self.delete_service.delete_book_permanently(isbn)
        if success:
            QMessageBox.information(self, "Éxito", f"El libro '{title}' ha sido eliminado.")
            self._reset_view()
        else:
            QMessageBox.critical(self, "Error", message)

    def _reset_view(self, is_new_search=True):
        self.details_container.setVisible(False)
        self.decrease_qty_button.setEnabled(False)
        self.delete_permanently_button.setEnabled(False)
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText("Portada del libro")
        self.inventory_combo.clear()
        if is_new_search:
            self.isbn_input.clear()
        self.isbn_input.setFocus()
        QTimer.singleShot(10, self.adjustSize)

    def reject(self):
        super().reject()
        
    def showEvent(self, event):
        super().showEvent(event)
        self._recenter()

    def adjustSize(self):
        self.main_frame.adjustSize()
        super().adjustSize()
        self._recenter()

    def _recenter(self):
        if self.parent():
            parent_geom = self.parent().geometry()
            self.move(parent_geom.x() + (parent_geom.width() - self.width()) / 2,
                      parent_geom.y() + (parent_geom.height() - self.height()) / 2)
    
print("hola")