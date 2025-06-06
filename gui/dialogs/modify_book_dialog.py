"""
Diálogo específico para modificar un libro existente.
Este módulo actúa como un 'wrapper' o envoltorio alrededor de BookFormDialog,
configurándolo para el modo de modificación y manejando la lógica de actualización final.
"""

from PySide6.QtWidgets import QMessageBox
from .book_form_dialog import BookFormDialog
from features.book_service import BookService
from typing import Dict, Optional

class ModifyBookDialog(BookFormDialog):
    """
    Diálogo para modificar libros, que utiliza BookFormDialog en modo 'MODIFY'.
    """
    def __init__(self, book_service: BookService, isbn_to_modify: Optional[str] = None, parent=None):
        # Guarda la posición original para una actualización más precisa
        self.old_position = None
        
        # La lógica para obtener la posición ahora debe ser condicional
        if isbn_to_modify:
            book_info = book_service.buscar_libro_por_isbn(isbn_to_modify)
            if book_info and book_info.get("inventory_entries"):
                self.old_position = book_info["inventory_entries"][0].get("posicion")

        # Inicializa el formulario base en modo "Modificar" y carga el ISBN si se proporcionó
        super().__init__(book_service, mode='MODIFY', initial_isbn=isbn_to_modify, parent=parent)
        
        # Conecta la señal genérica de guardado a la función específica de este diálogo
        self.save_requested.connect(self.handle_save_request)

    def handle_save_request(self, book_data: Dict[str, any]):
        """
        Maneja la lógica de guardado para modificar un libro existente.
        """
        isbn = book_data["ISBN"]
        nueva_posicion = book_data["Posición"]

        # 1. Actualizar la información principal del libro en la tabla 'libros'
        success_book, message_book = self.book_service.guardar_libro(book_data)
        if not success_book:
            QMessageBox.critical(self, "Error de Base de Datos", message_book)
            return

        # 2. Actualizar la posición en el inventario (si cambió)
        if self.old_position and self.old_position.upper() != nueva_posicion.upper():
            success_inv, message_inv = self.book_service.modificar_libro_en_inventario(isbn, nueva_posicion, self.old_position)
            if not success_inv:
                QMessageBox.warning(self, "Error de Inventario", message_inv)
                return # Detener si la actualización del inventario falla
        
        QMessageBox.information(self, "Éxito", "El libro ha sido actualizado correctamente.")
        self.accept() # Siempre cierra después de modificar