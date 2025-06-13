"""
Servicio de gestión de eliminación de libros.
"""
from typing import Dict, Any, List, Optional, Tuple
from core.interfaces import DataManagerInterface

class DeleteService:
    """
    Servicio para operaciones relacionadas con la eliminación de libros.
    """
    def __init__(self, data_manager: DataManagerInterface):
        self.data_manager = data_manager

    def find_book_for_deletion(self, isbn: str) -> Dict[str, Any]:
        """
        Busca un libro por ISBN y devuelve sus detalles y existencias en inventario.
        """
        query_libros = "SELECT * FROM libros WHERE isbn = ?"
        db_book_results = self.data_manager.fetch_query(query_libros, (isbn,))
        
        if not db_book_results:
            return {"status": "not_found", "book_details": None, "inventory_entries": []}

        db_book = db_book_results[0]
        book_details = {
            "ISBN": db_book["isbn"], "Título": db_book["titulo"], "Autor": db_book["autor"],
            "Editorial": db_book["editorial"], "Imagen": db_book.get("imagen_url", ""),
            "Categorías": db_book["categorias"].split(",") if db_book["categorias"] else [],
            "Precio": db_book.get("precio_venta", 0)
        }

        query_inventario = "SELECT * FROM inventario WHERE libro_isbn = ? ORDER BY posicion"
        db_inventory_results = self.data_manager.fetch_query(query_inventario, (isbn,))
        inventory_entries = [
            {"id_inventario": inv["id_inventario"], "posicion": inv["posicion"], "cantidad": inv["cantidad"]}
            for inv in db_inventory_results
        ]
        
        status = "found" if inventory_entries else "found_no_stock"
        return {"status": status, "book_details": book_details, "inventory_entries": inventory_entries}

    def decrease_book_quantity(self, isbn: str, posicion: str) -> Tuple[bool, str]:
        """
        Disminuye la cantidad de un libro en una posición específica.
        Si la cantidad llega a 0, elimina la entrada del inventario.
        """
        try:
            posicion = posicion.upper()
            query_check = "SELECT cantidad FROM inventario WHERE libro_isbn = ? AND posicion = ?"
            result = self.data_manager.fetch_query(query_check, (isbn, posicion))

            if not result:
                return False, f"No se encontró el libro con ISBN {isbn} en la posición {posicion}."

            current_quantity = result[0]['cantidad']
            if current_quantity > 1:
                query_update = "UPDATE inventario SET cantidad = cantidad - 1, fecha_actualizacion_cantidad = date('now') WHERE libro_isbn = ? AND posicion = ?;"
                self.data_manager.execute_query(query_update, (isbn, posicion))
                new_quantity = current_quantity - 1
                return True, f"Cantidad disminuida. Quedan {new_quantity} unidades en la posición {posicion}."
            else:
                query_delete = "DELETE FROM inventario WHERE libro_isbn = ? AND posicion = ?;"
                self.data_manager.execute_query(query_delete, (isbn, posicion))
                return True, f"Última unidad eliminada del inventario en la posición {posicion}."

        except Exception as e:
            return False, f"Error al disminuir la cantidad: {str(e)}"

    def permanently_delete_book(self, isbn: str) -> Tuple[bool, str]:
        """
        Elimina todas las entradas de inventario y el registro del libro.
        """
        try:
            query_delete_inv = "DELETE FROM inventario WHERE libro_isbn = ?;"
            self.data_manager.execute_query(query_delete_inv, (isbn,))

            query_delete_book = "DELETE FROM libros WHERE isbn = ?;"
            cursor = self.data_manager.execute_query(query_delete_book, (isbn,))

            if cursor and cursor.rowcount > 0:
                return True, "Libro y todas sus existencias han sido eliminados permanentemente."
            else:
                return False, "El libro no se encontró en la tabla principal, pero se ha limpiado el inventario de posibles remanentes."

        except Exception as e:
            return False, f"Error durante la eliminación permanente: {str(e)}" 