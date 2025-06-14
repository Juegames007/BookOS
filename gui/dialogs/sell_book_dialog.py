from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
                             QSpacerItem, QSizePolicy, QPushButton, QLineEdit, QScrollArea, QWidget, QMessageBox, QGridLayout, QButtonGroup)
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QFont, QIcon, QPainter, QScreen
import uuid
from features.book_service import BookService
from features.sell_service import SellService
from gui.dialogs.price_input_dialog import PriceInputDialog
from gui.common.styles import FONTS, COLORS, STYLES
from gui.common.utils import get_icon_path, format_price
from .base_transaction_dialog import BaseTransactionDialog

class ElidedLabel(QLabel):
    """Un QLabel que trunca el texto con '...' si no cabe."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumWidth(1)

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = self.fontMetrics()
        elided_text = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment() | Qt.AlignVCenter, elided_text)

class PlaceholderWidget(QFrame):
    """Widget marcador de posición para un espacio vacío en la rejilla de venta."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setFixedSize(320, 70)
        self.setStyleSheet("""
            PlaceholderWidget {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)

class SaleItemWidget(QFrame):
    """Widget para mostrar un artículo en la lista de venta, con el nuevo diseño."""
    remove_item = Signal(str)

    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self._init_ui()

    def _init_ui(self):
        self.setFixedSize(320, 70)
        self.setStyleSheet("""
            SaleItemWidget {
                background-color: #FFFFFF;
                border: 2px solid #6D28D9;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # Usar QGridLayout para un control preciso de la alineación
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)
        
        # --- Icono ---
        item_id = self.item_data.get('id', '')
        if item_id.startswith('promo_'):
            icon_name = "descuento.png"
        elif item_id.startswith('disc_'):
            icon_name = "dvd.png"
        else:
            icon_name = "libro.png"

        pixmap = QIcon(get_icon_path(icon_name)).pixmap(QSize(28, 28))
        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background-color: transparent; border: none;")

        # --- Textos (Título y detalles) ---
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        
        title = self.item_data.get('titulo', 'Artículo desconocido')
        quantity = self.item_data.get('cantidad', 1)

        title_label = ElidedLabel(title)
        title_label.setFont(QFont("Montserrat", 10, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #1A202C; background: transparent; border: none;")

        details_text = f"Cantidad: {quantity}"
        
        details_label = QLabel(details_text)
        details_label.setFont(QFont("Montserrat", 9))
        details_label.setStyleSheet("color: #718096; background: transparent; border: none;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(details_label)

        # --- Precio ---
        unit_price = self.item_data.get('precio', 0)
        total_price = unit_price * quantity
        price_label = QLabel(f"${format_price(total_price)}")
        price_label.setFont(QFont("Montserrat", 10, QFont.Weight.Normal))
        price_label.setStyleSheet("color: #4A5568; background: transparent; border: none;")

        # --- Ensamblado en la rejilla ---
        main_layout.addWidget(icon_label, 0, 0, Qt.AlignCenter)
        main_layout.addLayout(text_layout, 0, 1)
        main_layout.addWidget(price_label, 0, 2, Qt.AlignCenter)
        
        # Configurar las columnas para que el tegxto se expanda
        main_layout.setColumnStretch(1, 1)
        main_layout.setColumnMinimumWidth(0, 40)
        main_layout.setColumnMinimumWidth(2, 60)

        # --- Botón de Eliminar ---
        remove_btn = QPushButton("×", self)
        remove_btn.setFixedSize(22, 22)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEE2E2;
                color: #EF4444;
                border: none;
                border-radius: 11px;
                font-family: "Arial";
                font-size: 16px;
                font-weight: bold;
                padding-bottom: 2px;
            }
            QPushButton:hover { background-color: #FECACA; }
            QPushButton:pressed { background-color: #FCA5A5; }
        """)
        remove_btn.move(self.width() - remove_btn.width() - 5, 5)
        remove_btn.raise_()
        
        item_id_to_remove = self.item_data.get('id')
        remove_btn.clicked.connect(lambda: self.remove_item.emit(item_id_to_remove))

class SellBookDialog(BaseTransactionDialog):
    
    def __init__(self, book_service: BookService, sell_service: SellService, parent=None):
        super().__init__(parent)
        self.book_service = book_service
        self.sell_service = sell_service
        self.payment_method = None

    def get_dialog_title(self) -> str:
        return "Vender Artículos"

    def get_confirm_button_text(self) -> str:
        return "Confirmar Venta"

    def get_isbn_placeholder(self) -> str:
        return "Ingresar ISBN del libro..."

    def setup_action_buttons(self, layout: QHBoxLayout):
        self.disc_btn = QPushButton(QIcon(get_icon_path("dvd.png")), " CD")
        self.promo_btn = QPushButton(QIcon(get_icon_path("descuento.png")), " Promoción")
        
        for btn in [self.disc_btn, self.promo_btn]:
            btn.setIconSize(QSize(20, 20))
            btn.setFixedHeight(45)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setAutoDefault(False)
            btn.setFont(QFont(FONTS["family"], 10, QFont.Weight.Bold))
            btn.setStyleSheet(STYLES['button_secondary_full'])

        layout.addWidget(self.disc_btn)
        layout.addWidget(self.promo_btn)

        self.disc_btn.clicked.connect(self._add_disc_item)
        self.promo_btn.clicked.connect(self._add_promo_item)

    def setup_extra_widgets(self, layout: QVBoxLayout):
        payment_widget = QWidget()
        payment_layout = QHBoxLayout(payment_widget)
        payment_layout.setContentsMargins(0, 10, 0, 5)
        payment_layout.setSpacing(15)

        label = QLabel("Método de pago:")
        label.setFont(QFont(FONTS["family"], 10, QFont.Weight.Bold))
        label.setStyleSheet(f"color: {COLORS['text_primary']};")
        payment_layout.addWidget(label)

        self.payment_button_group = QButtonGroup(self)
        self.payment_button_group.setExclusive(True)

        buttons_data = [
            {"text": "Efectivo", "icon": "dinero.png"},
            {"text": "Nequi", "icon": "nequi.png"},
            {"text": "Daviplata", "icon": "daviplata.png"},
            {"text": "Bold", "icon": "Bold.png"}
        ]

        for data in buttons_data:
            btn = QPushButton(QIcon(get_icon_path(data["icon"])), f" {data['text']}")
            btn.setIconSize(QSize(24, 24))
            btn.setCheckable(True)
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont(FONTS["family"], 10))
            btn.setStyleSheet(STYLES['button_toggle_style'])
            self.payment_button_group.addButton(btn)
            payment_layout.addWidget(btn)

        self.payment_button_group.buttonClicked.connect(self._on_payment_method_selected)

        payment_layout.addStretch()
        layout.addWidget(payment_widget)

    def _on_payment_method_selected(self, button):
        self.payment_method = button.text().strip()

    def _handle_add_item_from_isbn(self):
        isbn = self.isbn_input.text().strip()
        if not isbn:
            return

        current_count_in_cart = sum(1 for item in self.transaction_items if item.get('id') == isbn)
        
        result = self.sell_service.find_book_by_isbn_for_sale(isbn)
        
        if result:
            book_data = result['book_data']
            stock = result['stock']
            
            if current_count_in_cart < stock:
                self.add_item_to_transaction(book_data)
            else:
                QMessageBox.warning(self, "Stock insuficiente", 
                                    f"No hay más unidades disponibles para el ISBN: {isbn}. "
                                    f"Ya tiene {current_count_in_cart} en la venta.")
        else:
            QMessageBox.warning(self, "Libro no encontrado", f"No se encontró un libro disponible con el ISBN: {isbn}")
        
        self.isbn_input.clear()

    def _add_disc_item(self):
        dialog = PriceInputDialog(self, title="Añadir Disco", show_quantity=True, default_price=5000)
        if dialog.exec() == QDialog.Accepted:
            price, quantity = dialog.get_values()
            
            if price > 0 and quantity > 0:
                disc_data = {
                    'id': f'disc_{int(price)}',
                    'titulo': 'Disco Musical',
                    'precio': price,
                    'cantidad': quantity
                }
                self.add_item_to_transaction(disc_data)

    def _add_promo_item(self):
        promo_data = {
            'id': 'promo_10000',
            'titulo': 'Promoción de Libro',
            'precio': 10000,
            'cantidad': 1
        }
        self.add_item_to_transaction(promo_data)

    def handle_confirm(self):
        if not self.transaction_items:
            QMessageBox.warning(self, "Venta Vacía", "No hay artículos para vender.")
            return

        if not self.payment_method:
            QMessageBox.warning(self, "Método de Pago", "Por favor, seleccione un método de pago.")
            return

        total_amount = self.manual_total if self.manual_total is not None else self._calculate_base_total()
        final_items = self._group_items(self.transaction_items)
        
        success, message = self.sell_service.process_sale(
            items=final_items,
            total_amount=total_amount,
            payment_method=self.payment_method
        )

        if success:
            QMessageBox.information(self, "Venta Exitosa", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error en la Venta", message)