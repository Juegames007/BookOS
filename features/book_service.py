"""
Servicio de gestión de libros.

Este módulo contiene la lógica de negocio relacionada con la gestión de libros,
separada de la interfaz de usuario. Proporciona métodos para buscar, agregar,
modificar y eliminar libros, así como para gestionar el inventario.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from core.interfaces import DataManagerInterface
from .utils import normalize_for_search


class BookService:
    """
    Servicio para operaciones relacionadas con libros e inventario.
    
    Esta clase encapsula toda la lógica de negocio relacionada con libros,
    permitiendo que las interfaces de usuario (GUI, CLI, etc.) se centren
    solo en la interacción con el usuario y la presentación de datos.
    """
    
    posiciones_validas = [f"{i:02d}{letra}" for i in range(1, 100) for letra in "ABCDEFGHIJ"]
    
    def __init__(self, data_manager: DataManagerInterface, book_info_service):
        self.data_manager = data_manager
        self.book_info_service = book_info_service
    
    def buscar_libro_por_isbn(self, isbn: str) -> Dict[str, Any]:
        query_libros = "SELECT * FROM libros WHERE isbn = ?"
        db_book_results = self.data_manager.fetch_query(query_libros, (isbn,))
        
        book_details_from_db = None
        if db_book_results:
            db_book = db_book_results[0]
            book_details_from_db = {
                "ISBN": db_book["isbn"], "Título": db_book["titulo"], "Autor": db_book["autor"],
                "Editorial": db_book["editorial"], "Imagen": db_book.get("imagen_url", ""),
                "Categorías": db_book["categorias"].split(",") if db_book["categorias"] else [],
                "Precio": db_book.get("precio_venta", 0)
            }

        inventory_entries = []
        if book_details_from_db:
            query_inventario = "SELECT * FROM inventario WHERE libro_isbn = ? ORDER BY posicion"
            db_inventory_results = self.data_manager.fetch_query(query_inventario, (isbn,))
            for inv_entry in db_inventory_results:
                inventory_entries.append({
                    "id_inventario": inv_entry["id_inventario"], "posicion": inv_entry["posicion"], 
                    "cantidad": inv_entry["cantidad"], "precio_venta_registrado": book_details_from_db["Precio"]
                })
            
            status = "encontrado_completo" if inventory_entries else "encontrado_en_libros"
            return {"status": status, "book_details": book_details_from_db, "inventory_entries": inventory_entries}

        api_book_data = self.book_info_service.extraer_info_json(isbn)
        if api_book_data:
            return {"status": "solo_api", "book_details": api_book_data, "inventory_entries": []}
            
        return {"status": "no_encontrado", "book_details": None, "inventory_entries": []}
    
    def guardar_libro(self, book_info: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            isbn = book_info["ISBN"]
            precio = book_info.get("Precio", 0)
            if not isinstance(precio, (int, float)) or precio < 1000:
                return False, "El precio debe ser un número igual o mayor a 1000."
            
            columnas = ["isbn", "titulo", "autor", "editorial", "imagen_url", "categorias", "precio_venta"]
            valores = (
                isbn, book_info.get("Título", ""), book_info.get("Autor", ""), book_info.get("Editorial", ""),
                book_info.get("Imagen", ""), ",".join(book_info.get("Categorías", [])), book_info.get("Precio", 0)
            )
            
            query = f"""
                INSERT INTO libros ({', '.join(columnas)}) VALUES ({', '.join(['?'] * len(columnas))})
                ON CONFLICT(isbn) DO UPDATE SET
                titulo=excluded.titulo, autor=excluded.autor, editorial=excluded.editorial,
                imagen_url=excluded.imagen_url, categorias=excluded.categorias, precio_venta=excluded.precio_venta;
            """
            
            if self.data_manager.execute_query(query, valores) is None:
                return False, "Error al guardar información del libro."
            return True, "Libro guardado/actualizado correctamente."
                
        except Exception as e:
            return False, f"Error al guardar libro: {str(e)}"
    
    def guardar_libro_en_inventario(self, isbn: str, posicion: str) -> Tuple[bool, str, int]:
        try:
            posicion = posicion.upper()
            query_update = "UPDATE inventario SET cantidad = cantidad + 1, fecha_actualizacion_cantidad = date('now') WHERE libro_isbn = ? AND posicion = ?;"
            cursor_upd = self.data_manager.execute_query(query_update, (isbn, posicion))
            
            if cursor_upd and cursor_upd.rowcount > 0:
                resultado_cantidad = self.data_manager.fetch_query("SELECT cantidad FROM inventario WHERE libro_isbn = ? AND posicion = ?;", (isbn, posicion))
                cantidad_actual = resultado_cantidad[0]['cantidad'] if resultado_cantidad else 0
                return True, f"Cantidad incrementada en {posicion}.", cantidad_actual
            
            query_insert = "INSERT INTO inventario (libro_isbn, posicion, cantidad, fecha_adquisicion, fecha_actualizacion_cantidad) VALUES (?, ?, 1, date('now'), date('now'));"
            cursor_ins = self.data_manager.execute_query(query_insert, (isbn, posicion))
            if cursor_ins and cursor_ins.rowcount > 0:
                return True, "Libro agregado a inventario.", 1
            
            return False, "No se pudo agregar el libro al inventario.", 0
                
        except Exception as e:
            return False, f"Error al guardar en inventario: {str(e)}", 0
    
    def modificar_libro_en_inventario(self, isbn: str, nueva_posicion: str, old_posicion: Optional[str] = None) -> Tuple[bool, str]:
        """
        Modifica la posición de una entrada de inventario existente.
        Si se da la posición antigua, es más preciso. Si no, actualiza la primera que encuentra.
        """
        try:
            nueva_posicion = nueva_posicion.upper()
            if old_posicion:
                query = "UPDATE inventario SET posicion = ? WHERE libro_isbn = ? AND posicion = ?"
                params = (nueva_posicion, isbn, old_posicion.upper())
            else:
                # Actualiza la primera entrada encontrada para ese ISBN (menos preciso pero funciona)
                query = "UPDATE inventario SET posicion = ? WHERE id_inventario = (SELECT id_inventario FROM inventario WHERE libro_isbn = ? LIMIT 1)"
                params = (nueva_posicion, isbn)
            
            cursor = self.data_manager.execute_query(query, params)
            
            if cursor and cursor.rowcount > 0:
                return True, f"Posición actualizada a {nueva_posicion}."
            else:
                # Si no actualizó, es porque no existía. Lo agregamos como un nuevo item.
                exito, msg, _ = self.guardar_libro_en_inventario(isbn, nueva_posicion)
                return exito, msg if exito else "No se encontró el libro para modificar y no se pudo agregar."

        except Exception as e:
            return False, f"Error al modificar inventario: {str(e)}"

    def buscar_libros(self, termino: str, filtros: Optional[Dict[str, bool]] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT l.isbn, l.titulo, l.autor, l.editorial, l.imagen_url, l.categorias, l.precio_venta, i.posicion, i.cantidad
            FROM libros l LEFT JOIN inventario i ON l.isbn = i.libro_isbn
        """
        
        where_clauses = []
        params = []
        
        normalized_search_term = f"%{normalize_for_search(termino)}%"
        isbn_search_term = f"%{termino}%"

        # Si no hay filtros o están todos en False, buscar en todo.
        if not filtros or not any(filtros.values()):
            where_clauses.extend([
                "normalize(l.titulo) LIKE ?",
                "normalize(l.autor) LIKE ?",
                "normalize(l.editorial) LIKE ?",
                "normalize(l.categorias) LIKE ?",
                "l.isbn LIKE ?"
            ])
            params.extend([normalized_search_term, normalized_search_term, normalized_search_term, normalized_search_term, isbn_search_term])
        else:
            # Construir cláusula WHERE basada en filtros activos
            if filtros.get("titulo"):
                where_clauses.append("normalize(l.titulo) LIKE ?")
                params.append(normalized_search_term)
            if filtros.get("autor"):
                where_clauses.append("normalize(l.autor) LIKE ?")
                params.append(normalized_search_term)
            if filtros.get("categoria"):
                where_clauses.append("normalize(l.categorias) LIKE ?")
                params.append(normalized_search_term)
            
            # Siempre incluir búsqueda por ISBN
            where_clauses.append("l.isbn LIKE ?")
            params.append(isbn_search_term)

        if not where_clauses:
            return []

        query += f" WHERE {' OR '.join(where_clauses)} ORDER BY l.titulo"
        
        results = self.data_manager.fetch_query(query, tuple(params))
        
        books = []
        for row in results:
            books.append({
                "ISBN": row["isbn"], "Título": row["titulo"], "Autor": row["autor"], "Editorial": row["editorial"],
                "Imagen": row.get("imagen_url", ""), "Categorías": row["categorias"].split(",") if row["categorias"] else [],
                "Precio": row.get("precio_venta", 0), "Posición": row.get("posicion") or "-", "Cantidad": row.get("cantidad", 0)
            })
        return books