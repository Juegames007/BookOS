"""
Diálogo específico para agregar un nuevo libro al inventario.
Este módulo actúa como un 'wrapper' o envoltorio alrededor de BookFormDialog,
configurándolo para el modo de adición y manejando la lógica de guardado final.
"""

from PySide6.QtWidgets import QMessageBox
from .book_form_dialog import BookFormDialog
from features.book_service import BookService
from typing import Dict

class AddBookDialog(BookFormDialog):
    """
    Diálogo para agregar libros, que utiliza BookFormDialog en modo 'ADD'.
    """
    def __init__(self, book_service: BookService, parent=None, blur_effect=None):
        # Inicializa el formulario base en modo "Agregar"
        super().__init__(book_service, mode='ADD', parent=parent, blur_effect=blur_effect)
        
        # Conecta la señal genérica de guardado a la función específica de este diálogo
        self.save_requested.connect(self.handle_save_request)

    def handle_save_request(self, book_data: Dict[str, any]):
        """
        Maneja la lógica de guardado para un libro nuevo.
        Llama a los métodos del servicio para guardar la info y el inventario.
        """
        isbn = book_data["ISBN"]
        posicion = book_data["Posición"]

        # 1. Guardar o actualizar la información principal del libro en la tabla 'libros'
        success_book, message_book = self.book_service.guardar_libro(book_data)
        if not success_book:
            QMessageBox.critical(self, "Error de Base de Datos", message_book)
            return

        # 2. Agregar el libro al inventario o incrementar su cantidad
        success_inv, message_inv, cantidad_inv = self.book_service.guardar_libro_en_inventario(isbn, posicion)
        if success_inv:
            msg_exito = f"Cantidad incrementada en {posicion}. Nueva cantidad: {cantidad_inv}." if cantidad_inv > 1 else "Libro agregado al inventario exitosamente."
            QMessageBox.information(self, "Éxito", msg_exito)
            
            if self.cerrar_al_terminar_toggle.isChecked():
                self.accept()
            else:
                self.ultima_posicion_ingresada = posicion
                self._reset_for_next_book()
        else:
            QMessageBox.warning(self, "Error de Inventario", message_inv)