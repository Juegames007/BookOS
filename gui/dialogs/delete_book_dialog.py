"""
Diálogo para la gestión de eliminación de libros.

Este módulo implementa la interfaz de usuario que permite a los usuarios
buscar un libro por su ISBN y luego elegir entre disminuir su cantidad
en inventario o eliminarlo permanentemente de la base de datos.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
    QWidget, QMessageBox, QSpacerItem, QSizePolicy, QScrollArea, QListWidget, QListWidgetItem, QInputDialog
)
from PySide6.QtGui import QFont, QPixmap, QIcon
from PySide6.QtCore import Qt, QSize, QTimer

from features.delete_service import DeleteService
from gui.common.styles import COLORS, FONTS, STYLES
from gui.common.utils import get_icon_path, format_price
from gui.common.widgets import CustomButton

class DeleteBookDialog(QDialog):
    """
    Diálogo para buscar y eliminar libros.
    """
    def __init__(self, delete_service: DeleteService, parent=None, blur_effect=None):
        super().__init__(parent)
        self.delete_service = delete_service
        self.current_book_data = None
        self.current_inventory = []

        self._blur_effect = blur_effect
        self.setWindowTitle("Eliminar / Reducir Existencias de Libro")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._setup_ui()
        self._connect_signals()
        
        QTimer.singleShot(0, self._initial_reposition)

    def _setup_ui(self):
        # Frame principal con estilo glassmorphism
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setStyleSheet(f"""
            #mainFrame {{
                background-color: rgba(255, 255, 255, 89);
                border-radius: 16px;
                border: 0.5px solid white;
            }}
        """)
        
        # Layout principal del diálogo
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        # Layout del contenido dentro del frame
        content_layout = QVBoxLayout(self.main_frame)
        content_layout.setContentsMargins(25, 20, 25, 25)
        content_layout.setSpacing(20)
        self.main_frame.setFixedWidth(500)

        # --- Cabecera ---
        header_layout = self._create_header()
        content_layout.addLayout(header_layout)

        # --- Búsqueda de ISBN ---
        search_layout = self._create_search_layout()
        content_layout.addLayout(search_layout)
        
        # --- Contenedor de Detalles (inicialmente oculto) ---
        self.details_container = QWidget()
        self.details_layout = QVBoxLayout(self.details_container)
        self.details_layout.setContentsMargins(0, 10, 0, 0)
        self.details_layout.setSpacing(15)
        content_layout.addWidget(self.details_container)
        self.details_container.setVisible(False)

        self._create_details_widgets()

    def _create_header(self):
        header_layout = QHBoxLayout()
        title_label = QLabel("Eliminar Libro")
        title_label.setFont(QFont(FONTS["family_title"], FONTS["size_large_title"], QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(STYLES.get('button_tertiary_full', ''))
        close_btn.setAutoDefault(False)
        close_btn.clicked.connect(self.reject)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        return header_layout

    def _create_search_layout(self):
        search_layout = QHBoxLayout()
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("Ingresar ISBN del libro a buscar...")
        self.isbn_input.setStyleSheet(STYLES['line_edit_style'])
        self.isbn_input.setFixedHeight(45)
        
        self.search_button = QPushButton(QIcon(get_icon_path("buscar.png")), "")
        self.search_button.setFixedSize(45, 45)
        self.search_button.setIconSize(QSize(20, 20))
        self.search_button.setCursor(Qt.PointingHandCursor)
        self.search_button.setStyleSheet(STYLES.get('button_primary_full', ''))
        self.search_button.setAutoDefault(False)

        search_layout.addWidget(self.isbn_input, 1)
        search_layout.addWidget(self.search_button)
        return search_layout

    def _create_details_widgets(self):
        # Widget para info básica del libro
        self.book_info_widget = QLabel("Info del libro...")
        self.book_info_widget.setWordWrap(True)
        self.book_info_widget.setStyleSheet("background-color: rgba(0,0,0,0.05); border-radius: 8px; padding: 10px;")
        
        # Título para la sección de inventario
        inventory_title = QLabel("Existencias en Inventario:")
        inventory_title.setFont(QFont(FONTS["family"], 11, QFont.Weight.Bold))
        inventory_title.setStyleSheet("background: transparent;")

        # Lista para mostrar las posiciones y cantidades
        self.inventory_list_widget = QListWidget()
        self.inventory_list_widget.setStyleSheet("background-color: rgba(0,0,0,0.05); border-radius: 8px;")
        self.inventory_list_widget.setFixedHeight(120)

        # Botón para eliminar permanentemente
        self.delete_permanently_button = QPushButton(QIcon(get_icon_path("eliminar.png")), " Eliminar Permanentemente")
        self.delete_permanently_button.setStyleSheet(STYLES.get('button_danger_full', ''))
        self.delete_permanently_button.setFixedHeight(40)
        self.delete_permanently_button.setIconSize(QSize(18, 18))
        self.delete_permanently_button.setAutoDefault(False)

        self.details_layout.addWidget(self.book_info_widget)
        self.details_layout.addWidget(inventory_title)
        self.details_layout.addWidget(self.inventory_list_widget)
        self.details_layout.addWidget(self.delete_permanently_button)

    def _connect_signals(self):
        self.search_button.clicked.connect(self._find_book)
        self.isbn_input.returnPressed.connect(self._find_book)
        self.inventory_list_widget.itemClicked.connect(self._on_inventory_item_clicked)
        self.delete_permanently_button.clicked.connect(self._delete_book_permanently)

    def _find_book(self):
        isbn = self.isbn_input.text().strip()
        if not isbn:
            return
        
        result = self.delete_service.find_book_for_deletion(isbn)
        
        if result["status"] == "not_found":
            QMessageBox.warning(self, "No Encontrado", f"No se encontró ningún libro con el ISBN: {isbn}")
            self._reset_view()
            return
        
        self.current_book_data = result["book_details"]
        self.current_inventory = result["inventory_entries"]
        
        self._display_book_info()
        self._display_inventory()
        self.details_container.setVisible(True)
        self.adjustSize()

    def _display_book_info(self):
        if not self.current_book_data:
            return
        
        title = self.current_book_data.get('Título', 'N/A')
        author = self.current_book_data.get('Autor', 'N/A')
        price = self.current_book_data.get('Precio', 0)
        
        info_text = (
            f"<b>Título:</b> {title}<br>"
            f"<b>Autor:</b> {author}<br>"
            f"<b>Precio de Venta Registrado:</b> {format_price(price)}"
        )
        self.book_info_widget.setText(info_text)

    def _display_inventory(self):
        self.inventory_list_widget.clear()
        if not self.current_inventory:
            item = QListWidgetItem("Este libro no tiene existencias en inventario.")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.inventory_list_widget.addItem(item)
            return
        
        for stock_item in self.current_inventory:
            widget = QWidget()
            layout = QHBoxLayout(widget)
            
            pos_label = QLabel(f"<b>Posición:</b> {stock_item['posicion']}")
            qty_label = QLabel(f"<b>Cantidad:</b> {stock_item['cantidad']}")
            
            decrease_btn = QPushButton("Disminuir Cantidad")
            decrease_btn.setCursor(Qt.PointingHandCursor)
            decrease_btn.setStyleSheet(STYLES.get('button_secondary_full', '').replace('border-radius: 8px', 'border-radius: 5px'))
            decrease_btn.setAutoDefault(False)
            decrease_btn.clicked.connect(lambda ch, p=stock_item['posicion']: self._decrease_quantity(p))

            layout.addWidget(pos_label)
            layout.addWidget(qty_label)
            layout.addStretch()
            layout.addWidget(decrease_btn)
            
            list_item = QListWidgetItem(self.inventory_list_widget)
            list_item.setSizeHint(widget.sizeHint())
            self.inventory_list_widget.addItem(list_item)
            self.inventory_list_widget.setItemWidget(list_item, widget)

    def _on_inventory_item_clicked(self, item):
        # En el futuro, podríamos querer hacer algo aquí.
        # Por ahora, la acción está en el botón de cada item.
        pass

    def _decrease_quantity(self, posicion: str):
        isbn = self.current_book_data.get("ISBN")
        if not isbn: return

        reply = QMessageBox.question(self, "Confirmar Acción",
                                     f"¿Está seguro de que desea disminuir en 1 la cantidad del libro en la posición <b>{posicion}</b>?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success, message = self.delete_service.decrease_book_quantity(isbn, posicion)
            if success:
                QMessageBox.information(self, "Éxito", message)
                self._find_book() # Recargar la info
            else:
                QMessageBox.critical(self, "Error", message)

    def _delete_book_permanently(self):
        isbn = self.current_book_data.get("ISBN")
        if not isbn: return

        # Advertencia 1
        reply1 = QMessageBox.warning(self, "¡ADVERTENCIA! (1/3)",
                                     "Está a punto de <b>eliminar permanentemente</b> este libro y <b>TODAS</b> sus existencias en inventario.<br><br>"
                                     "Esta acción <b>NO SE PUEDE DESHACER</b>.<br><br>¿Está seguro de que desea continuar?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply1 == QMessageBox.No: return

        # Advertencia 2
        reply2 = QMessageBox.warning(self, "Confirmación Final (2/3)",
                                     "<b>Confirmación final requerida.</b><br><br>"
                                     "Esto afectará los registros de inventario y el catálogo de libros de forma irreversible.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply2 == QMessageBox.No: return

        # Advertencia 3 - con input
        text, ok = QInputDialog.getText(self, "Última Verificación (3/3)",
                                        f"Para confirmar, escriba 'ELIMINAR' en el campo de abajo:")
        if not (ok and text.strip().upper() == 'ELIMINAR'):
            QMessageBox.information(self, "Cancelado", "La operación de eliminación ha sido cancelada.")
            return
            
        success, message = self.delete_service.permanently_delete_book(isbn)
        if success:
            QMessageBox.information(self, "Éxito", message)
            self._reset_view()
            self.isbn_input.clear()
        else:
            QMessageBox.critical(self, "Error", message)

    def _reset_view(self):
        self.details_container.setVisible(False)
        self.current_book_data = None
        self.current_inventory = []
        self.adjustSize()

    def _initial_reposition(self):
        self.adjustSize()
        if self.parent():
            p_geom = self.parent().geometry()
            self.move(p_geom.x() + (p_geom.width() - self.width()) // 2, 
                      p_geom.y() + (p_geom.height() - self.height()) // 2)

    def exec(self):
        if self._blur_effect:
            self._blur_effect.setEnabled(True)
        result = super().exec()
        if self._blur_effect:
            self._blur_effect.setEnabled(False)
        return result

    def reject(self):
        if self._blur_effect:
            self._blur_effect.setEnabled(False)
        super().reject() 