import sqlite3
from core.interfaces import DataManagerInterface
from typing import Dict, Any, Tuple, List
import logging

class ReturnService:
    def __init__(self, data_manager: DataManagerInterface):
        """
        Inicializa el servicio de devoluciones.
        """
        self.data_manager = data_manager

    def find_item_for_return(self, identifier: str) -> Dict[str, Any]:
        """
        Busca un artículo para devolución.
        - Para ISBN, verifica que el libro exista y que se haya vendido en los últimos 30 días.
        - Para 'disco' o 'promocion', crea un item genérico.
        """
        identifier_lower = identifier.lower().strip()

        # Manejar discos y promociones genéricas
        if identifier_lower.startswith('disc'):
            return self._create_generic_item('disc', 'Disco', 5000) # Precio base de ejemplo
        if identifier_lower.startswith('promo'):
            return self._create_generic_item('promo_10000', 'Promoción', 10000)

        # Manejar libros por ISBN
        return self._find_book_by_isbn(identifier)

    def _create_generic_item(self, item_id: str, title: str, price: float) -> Dict[str, Any]:
        return {
            "status": "success",
            "item_data": {'id': item_id, 'titulo': title, 'precio': price, 'cantidad': 1}
        }

    def _find_book_by_isbn(self, isbn: str) -> Dict[str, Any]:
        """
        Verifica si un libro (ISBN) es elegible para devolución.
        """
        try:
            connection = self.data_manager.get_connection()
            cursor = connection.cursor()

            # 1. Verificar si el libro fue vendido en los últimos 30 días
            cursor.execute("""
                SELECT 1 FROM detalles_venta dv
                JOIN ventas v ON dv.id_venta = v.id_venta
                WHERE dv.libro_isbn = ? AND v.fecha_venta >= date('now', '-30 days')
            """, (isbn,))
            
            if not cursor.fetchone():
                return {"status": "not_found", "message": "Este libro no ha sido vendido en los últimos 30 días."}

            # 2. Obtener el precio base del libro desde la tabla de libros.
            cursor.execute("SELECT precio_venta FROM libros WHERE isbn = ?", (isbn,))
            result = cursor.fetchone()

            if not result:
                return {"status": "not_found", "message": "El libro no existe en la base de datos."}

            precio_base = result[0]
            
            return {
                "status": "success",
                "item_data": {
                    'id': isbn,
                    'titulo': f'Devolución: Libro ({isbn})',
                    'precio': precio_base,
                    'cantidad': 1
                }
            }
        except sqlite3.Error as e:
            logging.error(f"Error en la base de datos al buscar libro para devolución: {e}")
            return {"status": "error", "message": str(e)}

    def process_return(self, items: List[Dict[str, Any]], total_amount: float) -> Tuple[bool, str]:
        """
        Procesa la devolución de una lista de artículos.
        """
        if not items:
            return False, "No hay artículos para devolver."

        connection = self.data_manager.get_connection()
        cursor = connection.cursor()

        try:
            # Iniciar transacción
            cursor.execute("BEGIN TRANSACTION")

            # 1. Registrar la devolución principal
            cursor.execute(
                "INSERT INTO devoluciones (monto_total) VALUES (?)",
                (total_amount,)
            )
            id_devolucion = cursor.lastrowid

            # 2. Registrar el egreso
            concepto = f"Devolución #{id_devolucion}"
            cursor.execute(
                "INSERT INTO egresos (monto, concepto) VALUES (?, ?)",
                (total_amount, concepto)
            )

            # 3. Procesar cada artículo devuelto
            for item in items:
                cantidad = item.get('cantidad', 1)
                isbn = item.get('id') if not item.get('id').startswith(('disc_', 'promo_')) else None
                
                # Insertar en detalles de devolución
                cursor.execute("""
                    INSERT INTO detalles_devolucion 
                    (id_devolucion, libro_isbn, descripcion_item, cantidad, precio_unitario_devolucion)
                    VALUES (?, ?, ?, ?, ?)
                """, (id_devolucion, isbn, item.get('titulo') if not isbn else None, cantidad, item.get('precio')))

                # Si es un libro, actualizar inventario
                if isbn:
                    cursor.execute("""
                        UPDATE inventario SET cantidad = cantidad + ? 
                        WHERE libro_isbn = ?
                    """, (cantidad, isbn))

            # Confirmar transacción
            connection.commit()
            return True, f"Devolución #{id_devolucion} procesada exitosamente."

        except sqlite3.Error as e:
            connection.rollback()
            logging.error(f"Error al procesar la devolución: {e}")
            return False, f"Error en la base de datos: {e}" 