from core.interfaces import DataManagerInterface
from typing import List, Dict, Any, Optional
from features.book_service import BookService

class SellService:
    def __init__(self, data_manager: DataManagerInterface, book_service: BookService):
        self.data_manager = data_manager
        self.book_service = book_service

    def find_book_by_isbn_for_sale(self, isbn: str) -> Optional[Dict[str, Any]]:
        """
        Busca un libro por su ISBN y verifica si hay stock para la venta.
        Devuelve un diccionario con los datos del libro y el stock disponible.
        """
        search_result = self.book_service.buscar_libro_por_isbn(isbn)
        
        if search_result["status"] in ["encontrado_completo"] and search_result["inventory_entries"]:
            total_quantity = sum(entry.get('cantidad', 0) for entry in search_result["inventory_entries"])
            
            if total_quantity > 0:
                book_details = search_result["book_details"]
                return {
                    'book_data': {
                        'id': book_details["ISBN"],
                        'titulo': book_details["Título"],
                        'precio': book_details.get("Precio", 0),
                        'cantidad': 1
                    },
                    'stock': total_quantity
                }
                
        return None

    def process_sale(self, items: List[Dict[str, Any]], total_amount: float) -> (bool, str):
        """
        Procesa una venta, actualiza el inventario y registra la transacción.
        - Para libros (con ISBN), disminuye la cantidad en la tabla 'inventario'.
        - Para otros artículos (discos, promos), solo los registra en la venta.
        - Registra los detalles de la venta en las tablas 'ventas' y 'detalles_venta'.
        
        NOTA: Esta es una implementación simulada. La lógica real de la base de datos
        se añadirá en pasos posteriores.
        """
        if not items:
            return False, "No se puede procesar una venta sin artículos."

        try:
            # Aquí iría la lógica de la transacción de la base de datos.
            # 1. Iniciar una transacción.
            # 2. Crear un nuevo registro en la tabla 'ventas'.
            # 3. Iterar sobre `items`:
            #    a. Para cada item, crear un registro en 'detalles_venta'.
            #    b. Si es un libro, buscar su 'id_inventario' y disminuir la cantidad.
            # 4. Si todo va bien, confirmar la transacción.
            # 5. Si algo falla, hacer rollback.
            print("Procesando venta (simulado)...")
            print(f"Total de la venta: {total_amount}")
            for item in items:
                print(f" - Artículo: {item.get('titulo', item.get('id'))}, Cantidad: {item.get('cantidad', 1)}")

            return True, "Venta procesada con éxito (simulado)."

        except Exception as e:
            # En un caso real, aquí se registraría el error.
            return False, f"Ocurrió un error al procesar la venta: {e}" 