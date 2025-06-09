"""
Servicio de gestión de reservas.

Este módulo contiene la lógica de negocio para la creación y gestión de reservas de libros.
"""
from typing import Dict, Any, List, Optional, Tuple
from core.interfaces import DataManagerInterface

class ReservationService:
    """
    Servicio para operaciones relacionadas con las reservas de libros.
    """
    
    def __init__(self, data_manager: DataManagerInterface):
        """
        Inicializa el servicio de reservas.

        :param data_manager: Una instancia de un gestor de datos que cumpla con DataManagerInterface.
        """
        self.data_manager = data_manager

    def find_book_by_isbn_for_reservation(self, isbn: str) -> Dict[str, Any]:
        """
        Busca copias de un libro disponibles para reservar por su ISBN.

        Una copia está "disponible" si su posición no es 'APARTADO' o 'VENDIDO'.
        La disponibilidad se infiere de la existencia de copias en el inventario.

        :param isbn: El ISBN del libro a buscar.
        :return: Un diccionario con el estado de la búsqueda y los resultados.
                 - "status": "no_encontrado" | "no_disponible" | "encontrado_uno" | "encontrado_multiple"
        """
        query = """
            SELECT i.id_inventario, i.posicion, i.cantidad, l.titulo, l.precio_venta, l.isbn as libro_isbn
            FROM inventario i
            JOIN libros l ON i.libro_isbn = l.isbn
            WHERE i.libro_isbn = ?
              AND (i.posicion IS NOT NULL AND i.posicion NOT IN ('APARTADO', 'VENDIDO'))
              AND i.cantidad > 0
        """
        params = (isbn,)
        available_items = self.data_manager.fetch_query(query, params)

        if not available_items:
            # Si no hay copias disponibles, verificar si el libro existe en el catálogo para dar un feedback más claro.
            book_info_query = "SELECT titulo, precio_venta FROM libros WHERE isbn = ?"
            book_info = self.data_manager.fetch_query(book_info_query, (isbn,))
            if book_info:
                # Si el libro existe en el catálogo pero no tiene copias disponibles en inventario.
                return {"status": "no_disponible", "details": book_info[0]}
            # Si el libro ni siquiera existe en el catálogo.
            return {"status": "no_encontrado"}

        if len(available_items) == 1:
            return {"status": "encontrado_uno", "item": available_items[0]}
        else:
            return {"status": "encontrado_multiple", "items": available_items}

    def find_or_create_client(self, nombre: str, telefono: str) -> Optional[int]:
        """
        Busca un cliente por su número de teléfono. Si no existe, lo crea.

        :param nombre: Nombre del cliente.
        :param telefono: Teléfono del cliente (usado como identificador único).
        :return: El ID del cliente (existente o nuevo), o None si hay un error.
        """
        try:
            # Primero, intentar encontrar el cliente
            find_query = "SELECT id_cliente FROM clientes WHERE telefono = ?"
            result = self.data_manager.fetch_query(find_query, (telefono,))
            if result:
                return result[0]['id_cliente']

            # Si no se encuentra, crearlo
            insert_query = "INSERT INTO clientes (nombre, telefono) VALUES (?, ?)"
            cursor = self.data_manager.execute_query(insert_query, (nombre, telefono))
            if cursor and cursor.lastrowid is not None:
                return cursor.lastrowid
            return None
        except Exception:
            # Considerar registrar el error
            return None

    def create_reservation(self, client_id: int, book_items: List[Dict], total_amount: float, paid_amount: float, notes: str = "") -> Tuple[bool, str]:
        """
        Crea una nueva reserva, actualiza el inventario y registra el pago.

        :param client_id: El ID del cliente que hace la reserva.
        :param book_items: Lista de diccionarios, donde cada uno representa un libro a reservar.
        :param total_amount: El monto total de la reserva.
        :param paid_amount: El monto pagado inicialmente.
        :param notes: Notas adicionales para la reserva.
        :return: Una tupla (éxito, mensaje).
        """
        if not book_items:
            return False, "No se puede crear una reserva sin libros."

        # Determinar el estado de la reserva
        estado = 'COMPLETADA' if paid_amount >= total_amount else 'PENDIENTE'

        try:
            # 1. Crear la entrada en la tabla 'reservas'
            reserva_query = """
                INSERT INTO reservas (id_cliente, monto_total, monto_pagado, estado, notas, fecha_creacion, fecha_actualizacion)
                VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """
            reserva_params = (client_id, total_amount, paid_amount, estado, notes)
            cursor = self.data_manager.execute_query(reserva_query, reserva_params)

            if not cursor or not cursor.lastrowid:
                return False, "Error al crear el registro de la reserva."
            
            id_reserva = cursor.lastrowid

            # 2. Agrupar items por ISBN y procesar el inventario y los detalles
            from collections import defaultdict
            items_by_isbn = defaultdict(lambda: {'count': 0, 'price': 0})
            for item in book_items:
                isbn = item.get('libro_isbn')
                if isbn:
                    items_by_isbn[isbn]['count'] += 1
                    items_by_isbn[isbn]['price'] = item.get('precio_venta', 0)

            for isbn, data in items_by_isbn.items():
                count = data['count']
                price = data['price']
                
                # Decrementar la cantidad del inventario
                decrement_query = "UPDATE inventario SET cantidad = cantidad - ? WHERE libro_isbn = ? AND cantidad >= ?"
                self.data_manager.execute_query(decrement_query, (count, isbn, count))

                # Añadir a detalles_reserva
                detalle_query = "INSERT INTO detalles_reserva (id_reserva, libro_isbn, cantidad, precio_unitario) VALUES (?, ?, ?, ?)"
                self.data_manager.execute_query(detalle_query, (id_reserva, isbn, count, price))

            return True, f"Reserva #{id_reserva} creada con éxito."

        except Exception as e:
            return False, f"Error inesperado al crear la reserva: {str(e)}"

    def create_direct_sale(self, client_id: int, book_items: List[Dict], total_amount: float, notes: str = "") -> Tuple[bool, str]:
        """
        Crea una venta directa, actualiza el inventario y la registra.

        :param client_id: El ID del cliente.
        :param book_items: Lista de libros vendidos.
        :param total_amount: El monto total de la venta (que se asume pagado).
        :param notes: Notas adicionales para la venta.
        :return: Una tupla (éxito, mensaje).
        """
        if not book_items:
            return False, "No se puede crear una venta sin libros."

        try:
            # 1. Crear la entrada en la tabla 'ventas'
            venta_query = """
                INSERT INTO ventas (id_cliente, monto_total, notas, fecha_venta)
                VALUES (?, ?, ?, datetime('now'))
            """
            venta_params = (client_id, total_amount, notes)
            cursor = self.data_manager.execute_query(venta_query, venta_params)

            if not cursor or not cursor.lastrowid:
                return False, "Error al crear el registro de la venta."

            id_venta = cursor.lastrowid

            # 2. Agrupar items por ISBN y procesar el inventario y los detalles
            from collections import defaultdict
            items_by_isbn = defaultdict(lambda: {'count': 0, 'price': 0})
            for item in book_items:
                isbn = item.get('libro_isbn')
                if isbn:
                    items_by_isbn[isbn]['count'] += 1
                    items_by_isbn[isbn]['price'] = item.get('precio_venta', 0)

            for isbn, data in items_by_isbn.items():
                count = data['count']
                price = data['price']

                # Decrementar la cantidad del inventario
                decrement_query = "UPDATE inventario SET cantidad = cantidad - ? WHERE libro_isbn = ? AND cantidad >= ?"
                self.data_manager.execute_query(decrement_query, (count, isbn, count))
                
                # Registrar la venta en detalles_venta
                detalle_query = "INSERT INTO detalles_venta (id_venta, libro_isbn, cantidad, precio_unitario) VALUES (?, ?, ?, ?)"
                self.data_manager.execute_query(detalle_query, (id_venta, isbn, count, price))
            
            return True, f"Venta #{id_venta} registrada con éxito."

        except Exception as e:
            return False, f"Error inesperado al crear la venta: {str(e)}" 