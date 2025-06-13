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
    def __init__(self, book_service: BookService, isbn_to_modify: Optional[str] = None, parent=None, blur_effect=None):
        # Guarda la posición original para una actualización más precisa
        self.old_position = None
        
        # La lógica para obtener la posición ahora debe ser condicional
        if isbn_to_modify:
            book_info = book_service.buscar_libro_por_isbn(isbn_to_modify)
            if book_info and book_info.get("inventory_entries"):
                self.old_position = book_info["inventory_entries"][0].get("posicion")

        # Inicializa el formulario base en modo "Modificar" y carga el ISBN si se proporcionó
        super().__init__(book_service, mode='MODIFY', initial_isbn=isbn_to_modify, parent=parent, blur_effect=blur_effect)
        
        # Conecta la señal genérica de guardado a la función específica de este diálogo
        self.save_requested.connect(self.handle_save_request)

    def handle_save_request(self, book_data: Dict[str, any]):
        """
        Maneja la lógica de guardado para modificar un libro existente.
        Incluye una confirmación detallada si el toggle está activado.
        """
        # 1. Comprobar si se debe mostrar la confirmación
        if self.cerrar_al_terminar_toggle.isChecked() and self.original_book_data:
            changes = []
            old_data = self.original_book_data
            
            # Mapeo de claves del formulario a nombres legibles para el mensaje
            field_map = {
                "Título": "Título", "Autor": "Autor", "Editorial": "Editorial",
                "Precio": "Precio", "Posición": "Posición"
            }

            for key, name in field_map.items():
                old_value = old_data.get(key)
                new_value = book_data.get(key)
                # Convertir a string para una comparación simple y segura
                if str(old_value).strip() != str(new_value).strip():
                    changes.append(f'  - {name}: de "{old_value}" a "{new_value}"')

            # Comparación especial para categorías (lista)
            old_cats = set(old_data.get('Categorías', []))
            new_cats = set(book_data.get('Categorías', []))
            if old_cats != new_cats:
                changes.append(f'  - Categorías: de "{", ".join(old_cats) or "Ninguna"}" a "{", ".join(new_cats) or "Ninguna"}"')

            # Comparación especial para la URL de la imagen
            if old_data.get('Imagen', '').strip() != book_data.get('Imagen', '').strip():
                changes.append('  - URL de la Imagen ha sido modificada.')

            # 2. Si hubo cambios, mostrar el diálogo de confirmación
            if changes:
                message = "¿Estás seguro de que quieres guardar los siguientes cambios?\n\n" + "\n".join(changes)
                reply = QMessageBox.question(self, "Confirmar Modificación", message,
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return  # Cancelar la operación de guardado si el usuario dice "No"

        # 3. Si la confirmación fue aceptada (o no fue necesaria), proceder con el guardado
        isbn = book_data["ISBN"]
        nueva_posicion = book_data["Posición"]

        # Actualizar la información principal del libro
        success_book, message_book = self.book_service.guardar_libro(book_data)
        if not success_book:
            QMessageBox.critical(self, "Error de Base de Datos", message_book)
            return

        # Actualizar la posición en el inventario (si cambió)
        if self.old_position and self.old_position.upper() != nueva_posicion.upper():
            success_inv, message_inv = self.book_service.modificar_libro_en_inventario(isbn, nueva_posicion, self.old_position)
            if not success_inv:
                QMessageBox.warning(self, "Error de Inventario", message_inv)
                return
        
        QMessageBox.information(self, "Éxito", "El libro ha sido actualizado correctamente.")
        self.accept() # Cierra el diálogo de modificar