from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QMessageBox
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon

from features.return_service import ReturnService
from gui.dialogs.base_transaction_dialog import BaseTransactionDialog
from gui.common.styles import FONTS, STYLES
from gui.common.utils import get_icon_path

class ReturnDialog(BaseTransactionDialog):
    
    def __init__(self, return_service: ReturnService, parent=None):
        super().__init__(parent)
        self.return_service = return_service

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

        total_amount = self.manual_total if self.manual_total is not None else self._calculate_base_total()
        final_items = self._group_items(self.transaction_items)
        
        success, message = self.return_service.process_return(
            items=final_items,
            total_amount=total_amount
        )

        if success:
            QMessageBox.information(self, "Devolución Exitosa", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error en la Devolución", message) 