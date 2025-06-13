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

    def _get_or_create_generic_client_id(self, cursor) -> int:
        """
        Busca el 'Cliente Genérico'. Si no existe, lo crea.
        Devuelve el ID del cliente.
        """
        generic_client_name = "Cliente Genérico"
        generic_client_phone = "000000000"  # Teléfono único para identificarlo

        cursor.execute("SELECT id_cliente FROM clientes WHERE telefono = ?", (generic_client_phone,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            cursor.execute(
                "INSERT INTO clientes (nombre, telefono) VALUES (?, ?)",
                (generic_client_name, generic_client_phone)
            )
            return cursor.lastrowid

    def process_sale(self, items: List[Dict[str, Any]], total_amount: float, notes: str = "") -> (bool, str):
        """
        Procesa una venta, actualiza el inventario y registra la transacción.
        """
        if not items:
            return False, "No se puede procesar una venta sin artículos."

        connection = self.data_manager.get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("BEGIN")

            # 1. Obtener o crear el ID del cliente genérico
            client_id = self._get_or_create_generic_client_id(cursor)

            # 2. Verificar el stock de todos los artículos antes de cualquier modificación
            for item in items:
                isbn = item.get('id')
                # Solo verificar stock para libros, no para promociones o discos
                if not str(isbn).startswith(('promo_', 'disc_')):
                    quantity_to_sell = item.get('cantidad', 1)
                    cursor.execute("SELECT SUM(cantidad) FROM inventario WHERE libro_isbn = ?", (isbn,))
                    stock_result = cursor.fetchone()
                    current_stock = stock_result[0] if stock_result and stock_result[0] is not None else 0
                    if current_stock < quantity_to_sell:
                        raise ValueError(f"Stock insuficiente para el libro con ISBN {isbn}. Solicitado: {quantity_to_sell}, Disponible: {current_stock}")

            # 3. Crear un nuevo registro en la tabla 'ventas'
            sale_data = (client_id, total_amount, notes)
            cursor.execute("INSERT INTO ventas (id_cliente, monto_total, notas) VALUES (?, ?, ?)", sale_data)
            sale_id = cursor.lastrowid
            if not sale_id:
                raise Exception("No se pudo crear el registro de venta.")

            # 4. Registrar el ingreso total de la venta
            income_data = (total_amount, f"Ingreso por Venta #{sale_id}", sale_id)
            cursor.execute("INSERT INTO ingresos (monto, concepto, id_venta) VALUES (?, ?, ?)", income_data)

            # 5. Iterar sobre los artículos, registrarlos en 'detalles_venta' y actualizar 'inventario'
            for item in items:
                isbn = item.get('id')
                quantity_to_sell = item.get('cantidad', 1)
                unit_price = item.get('precio', 0)

                # a. Insertar en 'detalles_venta'
                detail_data = (sale_id, isbn, quantity_to_sell, unit_price)
                cursor.execute("INSERT INTO detalles_venta (id_venta, libro_isbn, cantidad, precio_unitario) VALUES (?, ?, ?, ?)", detail_data)

                # b. Actualizar inventario solo para libros reales
                if not str(isbn).startswith(('promo_', 'disc_')):
                    cursor.execute("SELECT id_inventario, cantidad FROM inventario WHERE libro_isbn = ? AND cantidad > 0 ORDER BY id_inventario", (isbn,))
                    inventory_entries = cursor.fetchall()
                    
                    remaining_to_sell = quantity_to_sell
                    for entry_id, stock in inventory_entries:
                        if remaining_to_sell <= 0: break
                        
                        units_to_take = min(remaining_to_sell, stock)
                        new_stock = stock - units_to_take
                        
                        cursor.execute("UPDATE inventario SET cantidad = ?, fecha_actualizacion_cantidad = datetime('now') WHERE id_inventario = ?", (new_stock, entry_id))
                        remaining_to_sell -= units_to_take
                    
                    if remaining_to_sell > 0:
                        # Esta comprobación es una salvaguarda; el chequeo inicial debería haberlo prevenido.
                        raise Exception(f"Inconsistencia de stock para ISBN {isbn} durante la actualización.")

            connection.commit()
            return True, f"Venta #{sale_id} procesada con éxito."

        except Exception as e:
            connection.rollback()
            return False, f"Ocurrió un error al procesar la venta: {e}" 