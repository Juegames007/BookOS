import pandas as pd
from typing import List, Optional # Importamos Optional por si algún método lo necesitara
from .interfaces import DataManagerInterface
# Importamos SQLManager para el type hint en el constructor, aunque podría ser solo DataManagerInterface
from .sqlmanager import SQLManager # O cualquier otra implementación por defecto que queramos

class DataManager:
    def __init__(self, base_de_datos: DataManagerInterface):
        """
        Inicializa el DataManager con una estrategia de manejo de datos específica.

        Args:
            base_de_datos: Una instancia que implementa DataManagerInterface
                           (ej. SQLManager, ExcelManager).
        """
        if not isinstance(base_de_datos, DataManagerInterface):
            raise TypeError("La 'base_de_datos' proporcionada debe implementar DataManagerInterface.")
        self.base_de_datos: DataManagerInterface = base_de_datos

    def set_base_de_datos(self, base_de_datos: DataManagerInterface):
        """
        Permite cambiar la estrategia de manejo de datos en tiempo de ejecución.
        """
        if not isinstance(base_de_datos, DataManagerInterface):
            raise TypeError("La 'base_de_datos' proporcionada debe implementar DataManagerInterface.")
        self.base_de_datos = base_de_datos
        print(f"Estrategia de base de datos cambiada a: {type(base_de_datos).__name__}")

    # --- Métodos que delegan a la interfaz ---

    def crear_hoja_si_no_existe(self, hoja_nombre: str, definicion_columnas_sql: str):
        """
        Delega la creación de una "hoja" (tabla en SQL) a la estrategia actual.
        Para SQLManager, 'definicion_columnas_sql' será la definición SQL de las columnas.
        """
        self.base_de_datos.crear_hoja_si_no_existe(hoja_nombre, definicion_columnas_sql)

    def leer_hoja(self, hoja_nombre: str) -> pd.DataFrame:
        """
        Delega la lectura de una "hoja" (tabla) a la estrategia actual.
        Retorna un DataFrame.
        """
        return self.base_de_datos.leer_hoja(hoja_nombre)

    def escribir_hoja(self, hoja_nombre: str, df: pd.DataFrame, if_exists: str = 'replace'):
        """
        Delega la escritura de un DataFrame a una "hoja" (tabla) a la estrategia actual.
        """
        # Podríamos añadir validaciones aquí si es necesario antes de delegar
        self.base_de_datos.escribir_hoja(hoja_nombre, df, if_exists=if_exists)

    def limpiar_libros_agotados(self, hoja_nombre: str = "libros_estanteria"): # El nombre por defecto debe coincidir con la tabla SQL
        """
        Delega la limpieza de libros agotados a la estrategia actual.
        """
        self.base_de_datos.limpiar_libros_agotados(hoja_nombre)

    # --- Métodos de conveniencia específicos para SQL (si se usa SQLManager) ---
    # Estos métodos podrían añadirse si sabemos que estamos trabajando principalmente con SQL
    # y queremos evitar que el código de la aplicación construya SQL directamente.
    # Esto requeriría que DataManager sepa un poco más sobre la implementación
    # o que estos métodos se añadan a DataManagerInterface.

    def ejecutar_consulta_directa(self, query: str, params: Optional[tuple] = None):
        """
        Permite ejecutar una consulta de modificación si la base de datos subyacente es SQL.
        PRECAUCIÓN: Esto acopla DataManager a la idea de que la BD puede ejecutar SQL.
        """
        if hasattr(self.base_de_datos, 'execute_query'):
            return self.base_de_datos.execute_query(query, params)
        else:
            raise NotImplementedError(f"La estrategia {type(self.base_de_datos).__name__} no soporta 'execute_query'.")

    def obtener_datos_con_consulta(self, query: str, params: Optional[tuple] = None) -> List[dict]:
        """
        Permite obtener datos con una consulta SELECT si la base de datos subyacente es SQL.
        PRECAUCIÓN: Esto acopla DataManager a la idea de que la BD puede ejecutar SQL.
        """
        if hasattr(self.base_de_datos, 'fetch_query'):
            return self.base_de_datos.fetch_query(query, params)
        else:
            raise NotImplementedError(f"La estrategia {type(self.base_de_datos).__name__} no soporta 'fetch_query'.")

    def get_connection(self):
        """
        Devuelve el objeto de conexión si la estrategia subyacente lo soporta.
        """
        if hasattr(self.base_de_datos, 'get_connection'):
            return self.base_de_datos.get_connection()
        else:
            raise NotImplementedError(f"La estrategia {type(self.base_de_datos).__name__} no soporta 'get_connection'.")

    # --- Métodos alias para compatibilidad con código que espera nombres específicos ---

    def execute_query(self, query: str, params: Optional[tuple] = None):
        """
        Alias para ejecutar_consulta_directa, permite compatibilidad con código
        que espera un método llamado execute_query.
        """
        return self.ejecutar_consulta_directa(query, params)

    def fetch_query(self, query: str, params: Optional[tuple] = None) -> List[dict]:
        """
        Alias para obtener_datos_con_consulta, permite compatibilidad con código
        que espera un método llamado fetch_query.
        """
        return self.obtener_datos_con_consulta(query, params)
