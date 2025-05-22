"""
Servicio de gestión de libros.

Este módulo contiene la lógica de negocio relacionada con la gestión de libros,
separada de la interfaz de usuario. Proporciona métodos para buscar, agregar,
modificar y eliminar libros, así como para gestionar el inventario.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from core.interfaces import DataManagerInterface

class BookService:
    """
    Servicio para operaciones relacionadas con libros e inventario.
    
    Esta clase encapsula toda la lógica de negocio relacionada con libros,
    permitiendo que las interfaces de usuario (GUI, CLI, etc.) se centren
    solo en la interacción con el usuario y la presentación de datos.
    """
    
    # Posiciones válidas en el formato: 01A, 01B, ..., 99J
    posiciones_validas = [f"{i:02d}{letra}" for i in range(1, 100) for letra in "ABCDEFGHIJ"]
    
    def __init__(self, data_manager: DataManagerInterface, book_info_service):
        """
        Inicializa el servicio de libros.
        
        Args:
            data_manager: Gestor de datos que implementa DataManagerInterface
            book_info_service: Servicio para obtener información de libros desde APIs
        """
        self.data_manager = data_manager
        self.book_info_service = book_info_service
    
    def buscar_libro_por_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """
        Busca información de un libro por ISBN.
        
        Primero intenta obtener la información desde una API externa.
        Si no la encuentra, busca en la base de datos local.
        
        Args:
            isbn: El ISBN del libro a buscar.
            
        Returns:
            Un diccionario con la información del libro o None si no se encuentra.
        """
        # Buscar en APIs externas
        book_data = self.book_info_service.extraer_info_json(isbn)
        if book_data:
            return book_data
            
        # Si no lo encuentra, buscar en la base de datos local
        query = """
            SELECT isbn, titulo, autor, editorial, imagen_url AS Imagen, 
                   categorias, precio_venta AS Precio
            FROM libros 
            WHERE isbn = ?
        """
        results = self.data_manager.fetch_query(query, (isbn,))
        
        if results and len(results) > 0:
            # Convertir el resultado de la base de datos al formato esperado
            db_book = results[0]
            return {
                "ISBN": db_book["isbn"],
                "Título": db_book["titulo"],
                "Autor": db_book["autor"],
                "Editorial": db_book["editorial"],
                "Imagen": db_book.get("Imagen", ""),
                "Categorías": db_book["categorias"].split(",") if db_book["categorias"] else [],
                "Precio": db_book.get("Precio", 0)
            }
            
        return None
    
    def guardar_libro(self, book_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Guarda un libro en la base de datos.
        
        Si el libro ya existe, actualiza sus datos.
        
        Args:
            book_info: Diccionario con los datos del libro.
            
        Returns:
            Una tupla con (éxito, mensaje).
        """
        try:
            isbn = book_info["ISBN"]
            
            # Guardar en la tabla libros
            columnas = ["isbn", "titulo", "autor", "editorial", "imagen_url", "categorias", "precio_venta"]
            valores = (
                isbn,
                book_info.get("Título", ""),
                book_info.get("Autor", ""),
                book_info.get("Editorial", ""),
                book_info.get("Imagen", ""),
                ",".join(book_info.get("Categorías", [])),
                book_info.get("Precio", 0)
            )
            
            query_libros = f"""
                INSERT INTO libros ({', '.join(columnas)})
                VALUES ({', '.join(['?'] * len(columnas))})
                ON CONFLICT(isbn) DO UPDATE SET
                titulo = excluded.titulo,
                autor = excluded.autor,
                editorial = excluded.editorial,
                imagen_url = excluded.imagen_url,
                categorias = excluded.categorias,
                precio_venta = excluded.precio_venta;
            """
            
            cursor = self.data_manager.execute_query(query_libros, valores)
            if cursor is None:
                return False, "Error al guardar la información del libro en la base de datos."
                
            return True, "Libro guardado correctamente."
                
        except Exception as e:
            return False, f"Error al guardar el libro: {str(e)}"
    
    def guardar_libro_en_inventario(self, isbn: str, posicion: str) -> Tuple[bool, str, int]:
        """
        Guarda un libro en el inventario o incrementa su cantidad si ya existe.
        
        Args:
            isbn: El ISBN del libro.
            posicion: La posición del libro en el inventario.
            
        Returns:
            Una tupla con (éxito, mensaje, nueva_cantidad).
        """
        try:
            # Convertir posición a mayúsculas para consistencia
            posicion = posicion.upper()
            
            # Primero intentar actualizar si ya existe
            query_update = """
                UPDATE inventario
                SET cantidad = cantidad + 1, fecha_actualizacion_cantidad = date('now')
                WHERE libro_isbn = ? AND posicion = ?;
            """
            
            cursor_upd = self.data_manager.execute_query(query_update, (isbn, posicion))
            
            # Obtener la cantidad actual
            cantidad_actual = 0
            if cursor_upd and cursor_upd.rowcount > 0:
                # Se incrementó un libro existente, obtener su nueva cantidad
                select_query = "SELECT cantidad FROM inventario WHERE libro_isbn = ? AND posicion = ?;"
                select_params = (isbn, posicion)
                resultado_cantidad = self.data_manager.fetch_query(select_query, select_params)
                if resultado_cantidad and len(resultado_cantidad) > 0:
                    cantidad_actual = resultado_cantidad[0]['cantidad']
                return True, f"Se incrementó la cantidad del libro en la posición {posicion}.", cantidad_actual
            
            # Si no se actualizó ninguna fila, insertar nuevo registro
            if cursor_upd and cursor_upd.rowcount == 0:
                query_insert = """
                    INSERT INTO inventario (libro_isbn, posicion, cantidad, fecha_adquisicion, fecha_actualizacion_cantidad)
                    VALUES (?, ?, 1, date('now'), date('now'));
                """
                
                cursor_ins = self.data_manager.execute_query(query_insert, (isbn, posicion))
                
                if cursor_ins and cursor_ins.rowcount > 0:
                    return True, "Libro agregado correctamente al inventario.", 1
                else:
                    return False, "No se pudo agregar el libro al inventario.", 0
            
            return False, "Error desconocido al guardar el libro en el inventario.", 0
                
        except Exception as e:
            return False, f"Error al guardar el libro en inventario: {str(e)}", 0
    
    def buscar_libros(self, termino: str) -> List[Dict[str, Any]]:
        """
        Busca libros que coincidan con el término de búsqueda.
        
        Busca en los campos de título, autor, editorial e ISBN.
        
        Args:
            termino: El término a buscar.
            
        Returns:
            Una lista de diccionarios con la información de los libros encontrados.
        """
        query = """
            SELECT l.isbn, l.titulo, l.autor, l.editorial, l.imagen_url, 
                   l.categorias, l.precio_venta,
                   i.posicion, i.cantidad
            FROM libros l
            LEFT JOIN inventario i ON l.isbn = i.libro_isbn
            WHERE l.titulo LIKE ? OR l.autor LIKE ? OR l.editorial LIKE ? OR l.isbn LIKE ?
            ORDER BY l.titulo
        """
        
        # Añadir comodines al término de búsqueda
        search_term = f"%{termino}%"
        params = (search_term, search_term, search_term, search_term)
        
        results = self.data_manager.fetch_query(query, params)
        
        # Convertir los resultados al formato deseado
        books = []
        for row in results:
            book = {
                "ISBN": row["isbn"],
                "Título": row["titulo"],
                "Autor": row["autor"],
                "Editorial": row["editorial"],
                "Imagen": row.get("imagen_url", ""),
                "Categorías": row["categorias"].split(",") if row["categorias"] else [],
                "Precio": row.get("precio_venta", 0),
                "Posición": row.get("posicion", ""),
                "Cantidad": row.get("cantidad", 0)
            }
            books.append(book)
            
        return books 