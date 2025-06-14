from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QMessageBox, QButtonGroup, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon

from features.return_service import ReturnService
from gui.dialogs.base_transaction_dialog import BaseTransactionDialog
from gui.common.styles import FONTS, STYLES, COLORS
from gui.common.utils import get_icon_path

class ReturnDialog(BaseTransactionDialog):
    
    def __init__(self, return_service: ReturnService, parent=None):
        super().__init__(parent)
        self.return_service = return_service
        self.payment_method = None

    def get_dialog_title(self) -> str:
        return "Procesar Devolución"

    def get_confirm_button_text(self) -> str:
        return "Confirmar Devolución"

    def get_isbn_placeholder(self) -> str:
        return "Ingresar ISBN o ID del artículo a devolver..."

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

        self.disc_btn.clicked.connect(self._add_disc_return)
        self.promo_btn.clicked.connect(self._add_promo_return)

    def setup_extra_widgets(self, layout: QVBoxLayout):
        payment_widget = QWidget()
        payment_layout = QHBoxLayout(payment_widget)
        payment_layout.setContentsMargins(0, 10, 0, 5)
        payment_layout.setSpacing(15)

        label = QLabel("Método de Pago para la Devolución:")
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

        self.payment_button_group.buttonClicked.connect(lambda btn: setattr(self, 'payment_method', btn.text().strip()))
        
        payment_layout.addStretch()
        layout.addWidget(payment_widget)

    def _add_disc_return(self):
        """Añade un disco genérico a la devolución."""
        result = self.return_service.find_item_for_return('disc')
        if result and result["status"] == "success":
            self.add_item_to_transaction(result['item_data'])
        else:
            QMessageBox.warning(self, "Error", "No se pudo añadir el disco para devolución.")

    def _add_promo_return(self):
        """Añade una promoción genérica a la devolución."""
        result = self.return_service.find_item_for_return('promo')
        if result and result["status"] == "success":
            self.add_item_to_transaction(result['item_data'])
        else:
            QMessageBox.warning(self, "Error", "No se pudo añadir la promoción para devolución.")

    def _handle_add_item_from_isbn(self):
        identifier = self.isbn_input.text().strip()
        if not identifier:
            return

        result = self.return_service.find_item_for_return(identifier)
        
        if result and result["status"] == "success":
            item_data = result['item_data']
            self.add_item_to_transaction(item_data)
        else:
            message = result.get("message", f"No se encontró un artículo con el identificador: {identifier}")
            QMessageBox.warning(self, "Artículo no encontrado", message)
        
        self.isbn_input.clear()

    def handle_confirm(self):
        if not self.transaction_items:
            QMessageBox.warning(self, "Devolución Vacía", "No hay artículos para devolver.")
            return

        if not self.payment_method:
            QMessageBox.warning(self, "Método de Pago", "Por favor, seleccione un método de pago para la devolución.")
            return

        total_amount = self.manual_total if self.manual_total is not None else self._calculate_base_total()
        final_items = self._group_items(self.transaction_items)
        
        success, message = self.return_service.process_return(
            items=final_items,
            total_amount=total_amount,
            payment_method=self.payment_method
        )

        if success:
            QMessageBox.information(self, "Devolución Exitosa", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error en la Devolución", message) 