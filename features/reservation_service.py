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

        Una copia está "disponible" si su cantidad en el inventario es mayor que 0.

        :param isbn: El ISBN del libro a buscar.
        :return: Un diccionario con el estado de la búsqueda y los resultados.
                 - "status": "no_encontrado" | "no_disponible" | "encontrado_uno" | "encontrado_multiple"
        """
        query = """
            SELECT i.id_inventario, i.posicion, i.cantidad, l.titulo, l.precio_venta, l.isbn as libro_isbn
            FROM inventario i
            JOIN libros l ON i.libro_isbn = l.isbn
            WHERE i.libro_isbn = ?
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

    def get_or_create_client(self, nombre: str, telefono: str) -> Optional[int]:
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
        Crea una nueva reserva, actualiza el inventario y registra el abono inicial en 'ingresos'.
        """
        if not book_items:
            return False, "No se puede crear una reserva sin libros."
        if paid_amount <= 0:
            return False, "Para una reserva, se requiere un abono inicial mayor a cero."

        try:
            # 1. Crear la entrada en la tabla 'reservas'
            reserva_query = """
                INSERT INTO reservas (id_cliente, monto_total, estado, notas, fecha_creacion, fecha_actualizacion)
                VALUES (?, ?, 'PENDIENTE', ?, datetime('now'), datetime('now'))
            """
            reserva_params = (client_id, total_amount, notes)
            cursor = self.data_manager.execute_query(reserva_query, reserva_params)

            if not cursor or not cursor.lastrowid:
                return False, "Error al crear el registro de la reserva."
            
            id_reserva = cursor.lastrowid

            # 2. Registrar el abono inicial como un ingreso
            ingreso_query = "INSERT INTO ingresos (monto, concepto, id_reserva) VALUES (?, ?, ?)"
            concepto_ingreso = f"Abono inicial para reserva #{id_reserva}"
            self.data_manager.execute_query(ingreso_query, (paid_amount, concepto_ingreso, id_reserva))

            # 3. Procesar inventario y detalles de la reserva
            from collections import defaultdict
            
            books_by_isbn = defaultdict(lambda: {'count': 0, 'total_price': 0.0})
            generic_items = []

            for item in book_items:
                if 'libro_isbn' in item:
                    isbn = item['libro_isbn']
                    books_by_isbn[isbn]['count'] += 1
                    books_by_isbn[isbn]['total_price'] += item.get('precio_venta', 0)
                else:
                    generic_items.append(item)

            # Guardar libros en detalles_reserva y actualizar inventario
            for isbn, data in books_by_isbn.items():
                count = data['count']
                unit_price = data['total_price'] / count if count > 0 else 0
                
                decrement_query = "UPDATE inventario SET cantidad = cantidad - ? WHERE libro_isbn = ? AND cantidad >= ?"
                self.data_manager.execute_query(decrement_query, (count, isbn, count))

                detalle_query = "INSERT INTO detalles_reserva (id_reserva, libro_isbn, cantidad, precio_unitario) VALUES (?, ?, ?, ?)"
                self.data_manager.execute_query(detalle_query, (id_reserva, isbn, count, unit_price))

            # Guardar items genéricos en detalles_reserva
            for item in generic_items:
                item_id = item.get('id')
                price = item.get('precio_venta', 0)
                detalle_query = "INSERT INTO detalles_reserva (id_reserva, libro_isbn, cantidad, precio_unitario) VALUES (?, ?, ?, ?)"
                self.data_manager.execute_query(detalle_query, (id_reserva, item_id, 1, price))

            return True, f"Reserva #{id_reserva} creada con éxito."

        except Exception as e:
            return False, f"Error inesperado al crear la reserva: {str(e)}"

    def create_direct_sale(self, client_id: int, book_items: List[Dict], total_amount: float, notes: str = "") -> Tuple[bool, str]:
        """
        Crea una venta directa, descuenta del inventario y registra el ingreso total.
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

            # 2. Registrar el pago total como un ingreso
            ingreso_query = "INSERT INTO ingresos (monto, concepto, id_venta) VALUES (?, ?, ?)"
            concepto_ingreso = f"Pago completo de venta directa #{id_venta}"
            self.data_manager.execute_query(ingreso_query, (total_amount, concepto_ingreso, id_venta))

            # 3. Agrupar items por ISBN y procesar el inventario y los detalles
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

    def get_all_reservations(self) -> List[Dict[str, Any]]:
        """Alias para obtener todas las reservas activas."""
        return self.get_all_active_reservations()

    def get_all_active_reservations(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las reservas que están en estado 'PENDIENTE'.

        Recupera información del cliente y calcula el monto total abonado
        sumando los ingresos asociados a cada reserva.

        :return: Una lista de diccionarios, cada uno representando una reserva activa.
        """
        query = """
            SELECT
                r.id_reserva,
                c.nombre as cliente_nombre,
                c.telefono as cliente_telefono,
                r.fecha_creacion as fecha_reserva,
                r.monto_total,
                (SELECT SUM(monto) FROM ingresos WHERE id_reserva = r.id_reserva) as monto_abonado
            FROM reservas r
            JOIN clientes c ON r.id_cliente = c.id_cliente
            WHERE r.estado = 'PENDIENTE'
            ORDER BY r.fecha_creacion DESC
        """
        try:
            reservations = self.data_manager.fetch_query(query)
            return reservations if reservations else []
        except Exception as e:
            print(f"Error al obtener las reservas activas: {e}")
            return []

    def get_reservation_details(self, reservation_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene los detalles completos de una reserva específica.
        Esto incluye datos del cliente, libros reservados y estado financiero.
        :param reservation_id: El ID de la reserva a buscar.
        :return: Un diccionario con los detalles de la reserva, o None si no se encuentra.
        """
        # 1. Obtener detalles básicos de la reserva y del cliente
        base_query = """
            SELECT
                r.id_reserva,
                r.monto_total,
                r.notas,
                r.fecha_creacion as fecha_reserva,
                c.nombre as cliente_nombre,
                c.telefono as cliente_telefono
            FROM reservas r
            JOIN clientes c ON r.id_cliente = c.id_cliente
            WHERE r.id_reserva = ?
        """
        results = self.data_manager.fetch_query(base_query, (reservation_id,))
        reservation_details = results[0] if results else None

        if not reservation_details:
            return None

        # 2. Obtener la suma de abonos de la tabla de ingresos
        paid_amount_query = "SELECT SUM(monto) as total_abonado FROM ingresos WHERE id_reserva = ?"
        paid_amount_results = self.data_manager.fetch_query(paid_amount_query, (reservation_id,))
        paid_amount_result = paid_amount_results[0] if paid_amount_results else None
        reservation_details['monto_abonado'] = paid_amount_result['total_abonado'] if paid_amount_result and paid_amount_result['total_abonado'] else 0

        # 3. Obtener los libros asociados a la reserva
        books_query = """
            SELECT
                dr.libro_isbn,
                l.titulo,
                dr.cantidad,
                dr.precio_unitario
            FROM detalles_reserva dr
            LEFT JOIN libros l ON dr.libro_isbn = l.isbn
            WHERE dr.id_reserva = ?
        """
        books = self.data_manager.fetch_query(books_query, (reservation_id,))
        
        if books:
            for book in books:
                if not book.get('titulo'):
                    if book['libro_isbn'].startswith('promo_'):
                        book['titulo'] = 'Promoción'
                    elif book['libro_isbn'].startswith('disc_'):
                        book['titulo'] = 'Disco'
                    else:
                        book['titulo'] = 'Artículo Genérico'

        reservation_details['libros'] = books if books else []

        return reservation_details

    def add_deposit_to_reservation(self, reservation_id: int, amount: float) -> Tuple[bool, str]:
        """
        Añade un abono a una reserva existente y lo registra en la tabla de ingresos.

        :param reservation_id: El ID de la reserva.
        :param amount: El monto a abonar.
        :return: Una tupla (éxito, mensaje).
        """
        if amount <= 0:
            return False, "El monto del abono debe ser positivo."
        try:
            # Registrar el abono como un ingreso
            ingreso_query = "INSERT INTO ingresos (monto, concepto, id_reserva) VALUES (?, ?, ?)"
            concepto = f"Abono adicional para reserva #{reservation_id}"
            self.data_manager.execute_query(ingreso_query, (amount, concepto, reservation_id))
            return True, "Abono añadido con éxito."
        except Exception as e:
            return False, f"Error al añadir el abono: {str(e)}"

    def cancel_reservation(self, reservation_id: int, with_refund: bool) -> Tuple[bool, str]:
        """
        Cancela una reserva, revierte el inventario y maneja la contabilidad.

        :param reservation_id: El ID de la reserva a cancelar.
        :param with_refund: Si es True, el dinero se marca como devuelto (egreso).
                            Si es False, el dinero se considera una ganancia.
        :return: Una tupla (éxito, mensaje).
        """
        try:
            details = self.get_reservation_details(reservation_id)
            if not details:
                return False, "La reserva no existe."

            # 1. Revertir el inventario
            for book in details['libros']:
                update_inv_query = "UPDATE inventario SET cantidad = cantidad + ? WHERE libro_isbn = ?"
                self.data_manager.execute_query(update_inv_query, (book['cantidad'], book['libro_isbn']))

            # 2. Manejar la contabilidad del abono
            paid_amount = details.get('monto_abonado', 0)
            if paid_amount > 0:
                if with_refund:
                    # Registrar un egreso por el dinero devuelto
                    egreso_query = "INSERT INTO egresos (monto, concepto, id_reserva) VALUES (?, ?, ?)"
                    concepto = f"Devolución de abono por cancelación de reserva #{reservation_id}"
                    self.data_manager.execute_query(egreso_query, (paid_amount, concepto, reservation_id))
                
                # En ambos casos (con o sin devolución), el ingreso original se anula o reclasifica.
                # Para simplificar, marcaremos el estado de la reserva como CANCELADO.
                # No eliminamos el ingreso para mantener un registro histórico.
                
            # 3. Actualizar el estado de la reserva
            update_res_query = "UPDATE reservas SET estado = 'CANCELADO', fecha_actualizacion = datetime('now') WHERE id_reserva = ?"
            self.data_manager.execute_query(update_res_query, (reservation_id,))
            
            return True, f"Reserva #{reservation_id} cancelada con éxito."
        except Exception as e:
            return False, f"Error al cancelar la reserva: {str(e)}"

    def convert_reservation_to_sale(self, reservation_id: int, final_payment: float) -> Tuple[bool, str]:
        """
        Convierte una reserva en una venta final.

        :param reservation_id: El ID de la reserva a convertir.
        :param final_payment: El monto final pagado (además de los abonos ya hechos).
        :return: Una tupla (éxito, mensaje).
        """
        try:
            details = self.get_reservation_details(reservation_id)
            if not details:
                return False, "La reserva no existe."
            
            client_id_query = "SELECT id_cliente FROM reservas WHERE id_reserva = ?"
            client_id = self.data_manager.fetch_query(client_id_query, (reservation_id,))[0]['id_cliente']

            # 1. Crear la entrada en la tabla 'ventas'
            total_amount = details['monto_total']
            notes = details.get('notas', '')
            venta_query = "INSERT INTO ventas (id_cliente, monto_total, notas, fecha_venta, id_reserva_origen) VALUES (?, ?, ?, datetime('now'), ?)"
            cursor = self.data_manager.execute_query(venta_query, (client_id, total_amount, notes, reservation_id))
            
            if not cursor or not cursor.lastrowid:
                return False, "Error al crear el registro de la venta."
            id_venta = cursor.lastrowid

            # 2. Registrar el pago final como un ingreso (si lo hay)
            if final_payment > 0:
                ingreso_query = "INSERT INTO ingresos (monto, concepto, id_venta, id_reserva) VALUES (?, ?, ?, ?)"
                concepto = f"Pago final para completar reserva #{reservation_id} (Venta #{id_venta})"
                self.data_manager.execute_query(ingreso_query, (final_payment, concepto, id_venta, reservation_id))

            # 3. Mover los detalles de 'detalles_reserva' a 'detalles_venta'
            for book in details['libros']:
                detalle_query = "INSERT INTO detalles_venta (id_venta, libro_isbn, cantidad, precio_unitario) VALUES (?, ?, ?, ?)"
                self.data_manager.execute_query(detalle_query, (id_venta, book['libro_isbn'], book['cantidad'], book['precio_unitario']))

            # 4. Actualizar estado de la reserva original
            update_res_query = "UPDATE reservas SET estado = 'COMPLETADO', fecha_actualizacion = datetime('now') WHERE id_reserva = ?"
            self.data_manager.execute_query(update_res_query, (reservation_id,))

            return True, f"Venta #{id_venta} creada a partir de la reserva."
        except Exception as e:
            return False, f"Error al convertir la reserva en venta: {str(e)}" 