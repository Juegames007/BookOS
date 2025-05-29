import sqlite3
import os

# Obtener la ruta absoluta al directorio del script actual (data)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Subir un nivel para llegar a Pyside6-Libreria
project_root = os.path.dirname(current_dir)
# Construir la ruta a la base de datos
DB_PATH = os.path.join(project_root, 'data', 'library_app.db')

def test_database_query(search_term_param):
    print(f"Conectando a la base de datos en: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"Error: La base de datos no se encontró en {DB_PATH}")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row # Para acceder a las columnas por nombre
        cursor = conn.cursor()

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
        sql_search_term = f"%{search_term_param}%"
        params = (sql_search_term, sql_search_term, sql_search_term, sql_search_term)
        
        print(f"Ejecutando consulta con término: '{search_term_param}' (SQL: '{sql_search_term}')")
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        print(f"Número de resultados obtenidos: {len(results)}")
        
        if not results:
            print("No se encontraron libros para el término de búsqueda.")
            return

        print("\n--- Resultados Detallados ---")
        for row_num, row in enumerate(results):
            # Convertir sqlite3.Row a un diccionario para facilitar la inspección
            row_dict = dict(row)
            isbn = row_dict.get("isbn")
            titulo = row_dict.get("titulo")
            autor = row_dict.get("autor")
            posicion_db = row_dict.get("posicion") # Accedemos con "posicion" (minúscula)
            
            print(f"\nLibro #{row_num + 1}:")
            print(f"  ISBN: {isbn}")
            print(f"  Título: {titulo}")
            print(f"  Autor: {autor}")
            print(f"  Columna 'posicion' (valor crudo de DB): '{posicion_db}' (Tipo: {type(posicion_db)})")
            
            # Simular la lógica del BookService
            posicion_procesada = posicion_db if posicion_db else "-"
            print(f"  Posición (procesada como en BookService): '{posicion_procesada}'")

    except sqlite3.Error as e:
        print(f"Error de SQLite: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        if conn:
            conn.close()
            print("\nConexión a la base de datos cerrada.")

if __name__ == '__main__':
    # --- Configura aquí el término de búsqueda que quieres probar --- 
    termino_a_buscar = "a" # Puedes cambiar esto por cualquier término
    # Por ejemplo, si sabes de un ISBN que DEBERÍA tener posición:
    # termino_a_buscar = "9789587046755" 
    
    print(f"Iniciando prueba para el término: '{termino_a_buscar}'")
    test_database_query(termino_a_buscar)
