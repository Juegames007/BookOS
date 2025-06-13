from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QMessageBox

from features.return_service import ReturnService
from gui.dialogs.base_transaction_dialog import BaseTransactionDialog

class ReturnDialog(BaseTransactionDialog):
    
    def __init__(self, return_service: ReturnService, parent=None):
        self.return_service = return_service
        super().__init__(parent)

    def get_dialog_title(self) -> str:
        return "Procesar Devolución"

    def get_confirm_button_text(self) -> str:
        return "Confirmar Devolución"

    def get_isbn_placeholder(self) -> str:
        return "Ingresar ISBN o ID del artículo a devolver..."

    def setup_action_buttons(self, layout: QHBoxLayout):
        # No se necesitan botones de acción especiales para la devolución por ahora.
        pass

    def _handle_add_item_from_isbn(self):
        identifier = self.isbn_input.text().strip()
        if not identifier:
            return

        result = self.return_service.find_item_for_return(identifier)
        
        if result and result["status"] == "success":
            item_data = result['item_data']
            self.add_item_to_transaction(item_data)
        else:
            QMessageBox.warning(self, "Artículo no encontrado", 
                                f"No se encontró un artículo con el identificador: {identifier}")
        
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