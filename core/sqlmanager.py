import sqlite3
import pandas as pd
from typing import List, Optional, Any, Dict
from .interfaces import DataManagerInterface
import os # Para construir la ruta a la base de datos
from features.utils import normalize_for_search


class SQLManager(DataManagerInterface):
    def __init__(self, db_name="library_app.db", db_path: Optional[str] = None):
        """
        Inicializa el SQLManager.

        Args:
            db_name: Nombre del archivo de la base de datos SQLite.
            db_path: Ruta opcional al directorio donde se almacenará la base de datos.
                     Si es None, se usará el directorio del script actual o uno predefinido.
        """
        if db_path is None:
            # Por defecto, podríamos querer la BD en la raíz del proyecto o en una carpeta 'data'
            # Aquí, para simplicidad, la crearemos donde se ejecute el script, o
            # puedes especificar una ruta fija.
            # Ejemplo: self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', db_name)
            self.db_path = db_name # Crea la BD en el directorio de trabajo actual
        else:
            self.db_path = os.path.join(db_path, db_name)
        
        self._create_connection()

    def _create_connection(self) -> sqlite3.Connection:
        """Crea y retorna una conexión a la base de datos SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            # Habilitar claves foráneas (buena práctica)
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.create_function("normalize", 1, normalize_for_search)

            return conn
        except sqlite3.Error as e:
            print(f"Error al conectar con la base de datos SQLite '{self.db_path}': {e}")
            raise

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[sqlite3.Cursor]:
        """
        Ejecuta una consulta que no devuelve filas (INSERT, UPDATE, DELETE, CREATE).

        Args:
            query: La consulta SQL a ejecutar.
            params: Tupla opcional de parámetros para la consulta (para evitar inyección SQL).

        Returns:
            El cursor de la ejecución si tiene éxito, None si falla.
        """
        try:
            with self._create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                conn.commit()
                return cursor
        except sqlite3.Error as e:
            print(f"Error al ejecutar la consulta: {query}\nError: {e}")
            # Considerar si relanzar la excepción o cómo manejarla
            return None

    def fetch_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta que devuelve filas (SELECT) y las retorna como una lista de diccionarios.

        Args:
            query: La consulta SQL SELECT a ejecutar.
            params: Tupla opcional de parámetros para la consulta.

        Returns:
            Una lista de diccionarios, donde cada diccionario representa una fila.
            Retorna una lista vacía si no hay resultados o en caso de error.
        """
        try:
            with self._create_connection() as conn:
                conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                rows = cursor.fetchall()
                return [dict(row) for row in rows] # Convertir cada sqlite3.Row a un diccionario
        except sqlite3.Error as e:
            print(f"Error al ejecutar la consulta de búsqueda: {query}\nError: {e}")
            return []

    # --- Implementación de DataManagerInterface ---

    def crear_hoja_si_no_existe(self, hoja_nombre: str, columnas_definicion: str):
        """
        Crea una tabla en la base de datos si no existe.
        En SQL, una "hoja" es una tabla.

        Args:
            hoja_nombre: El nombre de la tabla a crear.
            columnas_definicion: Una cadena SQL que define las columnas y sus tipos.
                                 Debe estar formateada como "(col1 TIPO, col2 TIPO, ...)".
        """
        # Validación del nombre de la tabla
        # Permitimos alfanuméricos y guion bajo.
        cleaned_hoja_nombre = "".join(c for c in hoja_nombre if c.isalnum() or c == '_')
        if not hoja_nombre or hoja_nombre != cleaned_hoja_nombre:
            print(f"\033[1;31m❌ Error: Nombre de tabla '{hoja_nombre}' no es válido. Use solo caracteres alfanuméricos y guion bajo.\033[0m")
            return

        # Validación de columnas_definicion
        if not columnas_definicion or not isinstance(columnas_definicion, str):
            print(f"\033[1;31m❌ Error: La definición de columnas para la tabla '{hoja_nombre}' no puede estar vacía o no es una cadena.\033[0m")
            return
        
        stripped_cols_def = columnas_definicion.strip()
        if not (stripped_cols_def.startswith("(") and stripped_cols_def.endswith(")")):
            print(f"\033[1;31m❌ Error: La definición de columnas para '{hoja_nombre}' parece inválida. "
                  "Debe empezar con '(' y terminar con ')'. Ejemplo: (id INTEGER, nombre TEXT).\033[0m")
            print(f"Recibido: {columnas_definicion}")
            return

        # Si pasa las validaciones básicas, intentamos crear la tabla
        query = f"CREATE TABLE IF NOT EXISTS {hoja_nombre} {stripped_cols_def}"
        
        # execute_query ya tiene un try-except para errores de SQLite
        cursor = self.execute_query(query)
        
        if cursor is not None: # execute_query retorna None en caso de error de ejecución SQL
            # No podemos saber directamente desde el cursor si CREATE TABLE IF NOT EXISTS
            # creó una nueva tabla o si ya existía sin hacer otra consulta.
            # Simplemente confirmamos que el comando se intentó ejecutar.
            print(f"✅ Tabla '{hoja_nombre}' verificada/creación intentada.")
        else:
            # El error ya se imprimió dentro de execute_query
            print(f"ℹ️  Hubo un problema al intentar crear/verificar la tabla '{hoja_nombre}'. Revise los errores anteriores.")

    def leer_hoja(self, hoja_nombre: str) -> pd.DataFrame:
        """
        Lee todos los datos de una tabla y los devuelve como un DataFrame de Pandas.
        """
        if not hoja_nombre.isalnum() and '_' not in hoja_nombre:
             print(f"Error: Nombre de tabla '{hoja_nombre}' no es válido para leer.")
             return pd.DataFrame()

        query = f"SELECT * FROM {hoja_nombre}"
        try:
            with self._create_connection() as conn:
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e: # pd.read_sql_query puede lanzar sus propios errores
            print(f"Error al leer la tabla '{hoja_nombre}' a DataFrame: {e}")
            return pd.DataFrame() # Retorna DataFrame vacío en caso de error

    def escribir_hoja(self, *args, **kwargs):
        raise NotImplementedError("El método escribir_hoja no está implementado porque no es necesario en SQLManager.")

    def limpiar_libros_agotados(self, *args, **kwargs):
        raise NotImplementedError("El método limpiar_libros_agotados no está implementado porque no es necesario en SQLManager.")
