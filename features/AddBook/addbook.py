from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
from core.data_manager import DataManager
from core.input_handler import InputHandler
from features.book_info import GetBookInfo
from features.AddBook.book_ui import BookUI
import os
# import time # Eliminado porque BookUI maneja las pausas
# import sys # Eliminado, no parece usarse
# from .utils import format_price_with_thousands_separator # Eliminado, BookUI lo usa internamente

class AddBook:
    """Clase para manejar la adición de libros al inventario."""
    
    # Posiciones válidas en el formato: 01A, 01B, ..., 99J
    posiciones_validas = [f"{i:02d}{letra}" for i in range(1, 100) for letra in "ABCDEFGHIJ"]

    def __init__(self, get_book_info: GetBookInfo, input_handler: InputHandler, data_manager: DataManager):
        """
        Inicializa la clase AddBook.
        
        Args:
            input_handler: Manejador de entrada de usuario
            get_book_info: Cliente para obtener información de libros
            data_manager: Manejador de datos para guardar libros
            book_ui: Manejador de la interfaz de usuario para la adición de libros
        """
        self.input_handler = input_handler
        self.get_book_info = get_book_info
        self.data_manager = data_manager
        self.book_ui = BookUI()

    def _save_master_book_info(self, book_info: Dict[str, Any]) -> None:
        """
        Guarda la información maestra del libro en la tabla 'libros' si no existe,
        utilizando SQL INSERT ON CONFLICT DO NOTHING.
        """
        isbn = str(book_info["ISBN"])
        
        # Datos maestros del libro
        # fecha_registro se establecerá por DEFAULT (date('now')) en la BD si la tabla está configurada así.
        # Si no, habría que añadirla aquí también. Por ahora asumimos que la BD la maneja.
        columnas = ["isbn", "titulo", "autor", "editorial", "imagen_url", "categorias", "precio_venta"]
        valores = (
            isbn,
            book_info.get("Título", "Desconocido"),
            book_info.get("Autor", "Desconocido"),
            book_info.get("Editorial", "Desconocido"),
            book_info.get("Imagen", ""),
            ",".join(book_info.get("Categorías", [])),
            int(book_info.get("Precio", 0))  # Asegurar que sea int
        )

        query = f"""
            INSERT INTO libros ({', '.join(columnas)})
            VALUES ({', '.join(['?'] * len(columnas))})
            ON CONFLICT(isbn) DO NOTHING;
        """
        
        try:
            cursor = self.data_manager.execute_query(query, valores)
            if cursor and cursor.rowcount > 0: # Si el libro no existia, lo creamos.
                self.book_ui.mostrar_master_book_info_guardado(isbn)
            else:
                # Si rowcount es 0, o bien hubo un error que execute_query manejó e imprimió,
                # o el conflicto ocurrió y no se hizo nada (el libro ya existía).
                # SQLManager.execute_query devuelve None en caso de error de SQLite, 
                # y el error ya se habrá impreso desde allí.
                if cursor is not None: # Si el libro ya existia, no hay que modificar nada.
                    self.book_ui.mostrar_master_book_info_existente(isbn)
        except Exception as e:
            # Esta excepción sería por problemas no directamente relacionados con la ejecución SQL
            # que execute_query no capturó, o si execute_query no está disponible (aunque debería estarlo).
            self.book_ui.mostrar_error_guardar_master_book_info(isbn, e)

    def _save_book_to_inventory(self, book_info: Dict[str, Any]) -> None:
        """
        Guarda o actualiza el libro en la tabla 'inventario' utilizando execute_query.
        Primero intenta un UPDATE, si no afecta filas, intenta un INSERT.
        """
        isbn = str(book_info["ISBN"])
        posicion = book_info["Posición"]
        # Usamos la fecha pasada en book_info, que se establece en add()
        fecha_actual = book_info.get("Fecha", datetime.now().strftime("%Y-%m-%d"))

        # Intentar actualizar primero (incrementar cantidad)
        update_query = """
            UPDATE inventario
            SET cantidad = cantidad + 1, fecha_actualizacion_cantidad = ?
            WHERE libro_isbn = ? AND posicion = ?;
        """
        update_params = (fecha_actual, isbn, posicion)
        
        try:
            cursor = self.data_manager.execute_query(update_query, update_params)

            #1. Verificamos si hubieron cambios en la tabla.
            if cursor and cursor.rowcount > 0:

                if hasattr(self.data_manager, 'fetch_query'):
                    select_query = "SELECT cantidad FROM inventario WHERE libro_isbn = ? AND posicion = ?;"
                    select_params = (isbn, posicion)
                    resultado_cantidad = self.data_manager.fetch_query(select_query, select_params)
                    if resultado_cantidad and len(resultado_cantidad) > 0:
                        nueva_cantidad = resultado_cantidad[0]['cantidad']
                        self.book_ui.mostrar_inventario_incrementado(isbn, posicion, nueva_cantidad)
                    else:
                        # Esto no debería suceder si el UPDATE tuvo éxito, pero por si acaso.
                        self.book_ui.mostrar_inventario_incrementado_sin_cantidad(isbn, posicion)
                else:
                    self.book_ui.mostrar_warning_fetch_query(type(self.data_manager).__name__)
                self.book_ui.mostrar_inventario_actualizado_msg_base(isbn, posicion)
            
            #2. Si no hubo cambios, o hubo un error, debemos crear el libro.
            elif cursor is not None: # No hubo error en execute_query, pero rowcount fue 0 (no existía para actualizar)
                insert_query = """
                    INSERT INTO inventario (libro_isbn, posicion, cantidad, fecha_adquisicion, fecha_actualizacion_cantidad)
                    VALUES (?, ?, ?, ?, ?);
                """
                # Para una nueva inserción, la cantidad es 1.
                # fecha_adquisicion y fecha_actualizacion_cantidad son la misma en la inserción inicial.
                insert_params = (isbn, posicion, 1, fecha_actual, fecha_actual)
                
                insert_cursor = self.data_manager.execute_query(insert_query, insert_params)
                if insert_cursor and insert_cursor.rowcount > 0:
                    self.book_ui.mostrar_nuevo_libro_inventario(isbn, posicion)
                    self.book_ui.mostrar_inventario_actualizado_msg_base(isbn, posicion)
                elif insert_cursor is not None:
                     # Esto podría ocurrir si hubo un intento de inserción que falló silenciosamente
                     # (ej. una restricción UNIQUE no manejada con ON CONFLICT en ESTA query particular)
                     # o si execute_query retornó un cursor válido pero rowcount 0 por alguna razón.
                    self.book_ui.mostrar_error_agregar_nuevo_inventario(isbn, posicion)
                # Si insert_cursor es None, execute_query ya imprimió el error SQL.
            
            # Si el cursor original del UPDATE fue None, execute_query ya imprimió el error SQL.

        except Exception as e:
            self.book_ui.mostrar_error_guardar_inventario(isbn, posicion, e)

    def _get_book_info(self, isbn: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información del libro desde la API o manualmente.
        
        Args:
            isbn: ISBN del libro a buscar
            
        Returns:
            Diccionario con la información del libro o None si se cancela
        """
        # Intentar obtener información de la API
        book_info = self.get_book_info.extraer_info_json(isbn)
        
        if book_info is None:
            self.book_ui.mostrar_libro_no_encontrado_api()
            book_info = self._get_manual_book_info(isbn)
            if book_info is None:
                return None
        
        else:
            self.book_ui.mostrar_datos_api(book_info)
        
        processed_book_info = {
            "ISBN": isbn, # Aseguramos que el ISBN original esté
            "Título": book_info.get("Título", "Desconocido"),
            "Autor": book_info.get("Autor", "Desconocido"),
            "Editorial": book_info.get("Editorial", "Desconocido"),
            "Imagen": book_info.get("Imagen", ""),
            "Categorías": book_info.get("Categorías", []),
            "Precio": 0, # Se pedirá manualmente y se convertirá a int
            # "Fecha" se añadirá en add() antes de guardar
            # "Posición" se añadirá en add() antes de guardar
            # "Cantidad" inicial se maneja en _save_book_to_inventory
        }
        
        #Pedimos el precio manualmente.
        precio_manual_str = self.input_handler.get_valid_price("Precio del libro") # Devuelve string de un int
        if precio_manual_str == "cancelado":
            self.book_ui.mostrar_ingreso_precio_cancelado()
            return None
        else:
            # Convertir a int para asegurar que se almacene como número entero
            precio_int = int(precio_manual_str)
            processed_book_info["Precio"] = precio_int
            self.book_ui.mostrar_precio_establecido(precio_int)

        return processed_book_info

    def _get_manual_book_info(self, isbn: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información del libro manualmente del usuario.
        
        Args:
            isbn: ISBN del libro
            
        Returns:
            Diccionario con la información del libro o None si se cancela
        """
        self.book_ui.mostrar_ingreso_manual_header()
        
        titulo = self.input_handler.get_generic_input("Título", default_value="")
        if titulo == "cancelado": 
            self.book_ui.mostrar_operacion_cancelada()
            return None
            
        autor = self.input_handler.get_generic_input("Autor(es) (separados por coma si son varios)", default_value="")
        if autor == "cancelado": 
            self.book_ui.mostrar_operacion_cancelada()
            return None
            
        editorial = self.input_handler.get_generic_input("Editorial", default_value="Desconocido")
        if editorial == "cancelado": 
            self.book_ui.mostrar_operacion_cancelada()
            return None

        imagen_url = self.input_handler.get_generic_input("URL de Imagen (opcional)", default_value="Desconocido")
        if imagen_url == "cancelado":
            imagen_url = ""
        
        categorias_str = self.input_handler.get_generic_input("Categorías (separadas por coma)", default_value="")
        if categorias_str == "cancelado": 
            self.book_ui.mostrar_operacion_cancelada()
            return None
        categorias_list = [c.strip() for c in categorias_str.split(',') if c.strip()] if categorias_str else []
        
        return {
            "ISBN": isbn,
            "Título": titulo,
            "Autor": autor,
            "Editorial": editorial,
            "Imagen": imagen_url if imagen_url else "NO DISPONIBLE",
            "Categorías": categorias_list,
            "Precio": 0 
        }

    def add(self) -> None:
        """
        Proceso principal para añadir un libro a la tabla 'libros' (si es nuevo)
        y luego añadir/actualizar su entrada en la tabla 'inventario'.
        """
        while True:
            # Limpiar pantalla y mostrar encabezado
            os.system("cls" if os.name == "nt" else "clear")
            self.book_ui.mostrar_encabezado_agregar_libros()

            # Obtener ISBN
            isbn = self.input_handler.get_valid_isbn("ISBN del libro")
            if isbn == "cancelado":
                self.book_ui.mostrar_operacion_cancelada()
                break

            # Obtener información del libro
            book_info = self._get_book_info(isbn)
            if book_info is None:
                self.book_ui.mostrar_volviendo_con_pausa()
                continue

            # Añadir fecha actual al book_info, se usará para ambas tablas si es necesario.
            book_info["Fecha"] = datetime.now().strftime("%Y-%m-%d")

            # Siempre solicitar la posición para cada libro
            position_input = self.input_handler.get_is_in_list("Posición en estantería", lista_valida=self.posiciones_validas)
            if position_input == "cancelado":
                self.book_ui.mostrar_adicion_libro_cancelada_por_posicion()
                continue
                
            book_info["Posición"] = position_input

            # Guardar información maestra del libro (en tabla 'libros')
            self._save_master_book_info(book_info)

            # Guardar/Actualizar libro en el inventario
            self._save_book_to_inventory(book_info)
            
            self.book_ui.mostrar_libro_anadido_correctamente()

        self.book_ui.mostrar_proceso_finalizado()