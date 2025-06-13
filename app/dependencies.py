import json
import os
import sqlite3 # Importar sqlite3 para Optional[sqlite3.Cursor] y sqlite3.Error
from typing import List, Optional, Dict, Any # Añadir Dict y Any

# Asumiendo que 'core' y 'features' están en el PYTHONPATH o son accesibles
# Esto puede requerir ajustar el sys.path si se ejecuta desde dentro de 'app/'
# o si la estructura del proyecto no se añade automáticamente al PYTHONPATH.
# Una forma común es tener un script de ejecución en la raíz del proyecto.
try:
    from core.sqlmanager import SQLManager
    from core.interfaces import DataManagerInterface, BookApiInterface, HttpClientInterface
    from core.http_client import RequestsClient
    from core.data_manager import DataManager
    from features.book_info import GetBookInfo
    from features.book_api import GoogleBooksApi
    from features.delete_service import DeleteService
except ImportError as e:
    # Si 'core' no está directamente en PYTHONPATH, intentar ajuste relativo
    # Esto es útil si 'dependencies.py' está en 'app/' y 'core' está al mismo nivel ('../core')
    import sys
    APP_DIR_FOR_IMPORT = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT_FOR_IMPORT = os.path.dirname(APP_DIR_FOR_IMPORT)
    sys.path.insert(0, PROJECT_ROOT_FOR_IMPORT)
    # print(f"Ruta del proyecto añadida a sys.path: {PROJECT_ROOT_FOR_IMPORT}")
    
    from core.sqlmanager import SQLManager
    from core.interfaces import DataManagerInterface, BookApiInterface, HttpClientInterface
    from core.http_client import RequestsClient
    from core.data_manager import DataManager
    from features.book_info import GetBookInfo
    from features.book_api import GoogleBooksApi
    from features.delete_service import DeleteService


# Determinar rutas importantes
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
CORE_DIR = os.path.join(PROJECT_ROOT, "core")
SCHEMAS_PATH = os.path.join(CORE_DIR, "schemas.json")
DATABASE_NAME = "library_app.db"
# Guardar la BD en la raíz del proyecto por defecto, o en una carpeta 'data'
# DATABASE_PATH = PROJECT_ROOT
DATABASE_PATH = os.path.join(PROJECT_ROOT, "data") # Guardar en una carpeta 'data'


class DependencyFactory:
    _data_manager_instance: Optional[DataManagerInterface] = None
    _sql_manager_instance: Optional[SQLManager] = None
    _get_book_info_instance: Optional[GetBookInfo] = None
    _http_client_instance: Optional[HttpClientInterface] = None
    _delete_service_instance: Optional[DeleteService] = None

    @classmethod
    def get_sql_manager(cls) -> SQLManager:
        """
        DEPRECATED: Utilice get_data_manager() en su lugar.
        Mantiene compatibilidad con código existente que espera SQLManager.
        """
        if cls._sql_manager_instance is None:
            # Asegurarse de que el directorio de la base de datos exista
            if not os.path.exists(DATABASE_PATH):
                os.makedirs(DATABASE_PATH)
                print(f"Directorio de base de datos creado en: {DATABASE_PATH}")

            db_full_path = os.path.join(DATABASE_PATH, DATABASE_NAME)
            print(f"Inicializando SQLManager con base de datos en: {db_full_path}")
            
            cls._sql_manager_instance = SQLManager(db_name=DATABASE_NAME, db_path=DATABASE_PATH)
            cls._initialize_database_schema(cls._sql_manager_instance)
        return cls._sql_manager_instance

    @classmethod
    def get_data_manager(cls) -> DataManagerInterface:
        """
        Retorna una instancia de DataManagerInterface.
        
        Utiliza la clase DataManager como adaptador alrededor del SQLManager.
        Esto sigue el principio de inversión de dependencias, permitiendo
        cambiar la implementación concreta sin afectar al código cliente.
        """
        if cls._data_manager_instance is None:
            # Obtener la implementación concreta de SQLManager
            sql_manager = cls.get_sql_manager()
            
            # Crear el adaptador DataManager que implementa DataManagerInterface
            cls._data_manager_instance = DataManager(sql_manager)
            print("DataManager inicializado con SQLManager.")
            
        return cls._data_manager_instance

    @classmethod
    def _initialize_database_schema(cls, sql_manager: SQLManager) -> None:
        print(f"Intentando cargar esquemas desde: {SCHEMAS_PATH}")
        if not os.path.exists(SCHEMAS_PATH):
            print(f"Error Crítico: No se encontró el archivo de esquemas en {SCHEMAS_PATH}")
            print("La aplicación no puede continuar sin el archivo de esquemas.")
            # En una aplicación real, podrías querer salir o lanzar una excepción fatal aquí.
            # Por ejemplo: raise FileNotFoundError(f"No se encontró el archivo de esquemas en {SCHEMAS_PATH}")
            # Para permitir que la GUI se abra (aunque sin BD funcional), solo imprimimos el error.
            return

        try:
            with open(SCHEMAS_PATH, 'r', encoding='utf-8') as f: # Especificar encoding
                schemas = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error Crítico: Error al decodificar el archivo JSON de esquemas {SCHEMAS_PATH}: {e}")
            return 
        except Exception as e:
            print(f"Error Crítico: Error inesperado al leer {SCHEMAS_PATH}: {e}")
            return
            
        if 'tablas' not in schemas or not isinstance(schemas['tablas'], list):
            print(f"Error Crítico: El archivo de esquemas {SCHEMAS_PATH} no tiene el formato esperado (falta la lista 'tablas').")
            return

        print("Creando/Verificando tablas de la base de datos...")
        try:
            for tabla_info in schemas['tablas']:
                nombre_tabla = tabla_info.get('nombre')
                definicion_tabla = tabla_info.get('definicion')
                
                if nombre_tabla and definicion_tabla:
                    print(f"Procesando tabla: {nombre_tabla}...")
                    sql_manager.crear_hoja_si_no_existe(nombre_tabla, definicion_tabla)
                else:
                    print(f"Advertencia: Entrada de tabla incompleta en schemas.json (faltan 'nombre' o 'definicion'): {tabla_info}")
            print("Inicialización de esquemas de base de datos completada.")
        except Exception as e:
            print(f"Error durante la inicialización del esquema de la base de datos: {e}")
            # Esto podría ser un error de SQLManager no manejado, o un problema de conexión.

    @classmethod
    def get_http_client(cls) -> HttpClientInterface:
        if cls._http_client_instance is None:
            print("Inicializando cliente HTTP...")
            cls._http_client_instance = RequestsClient()
        return cls._http_client_instance

    @classmethod
    def get_book_info_service(cls) -> GetBookInfo:
        if cls._get_book_info_instance is None:
            print("Inicializando servicio de información de libros...")
            # Obtener el cliente HTTP
            http_client = cls.get_http_client()
            
            # Crear la instancia de GoogleBooksApi
            google_books_api = GoogleBooksApi(http_client=http_client)
            
            # Crear GetBookInfo con la API de Google Books
            cls._get_book_info_instance = GetBookInfo(apis=[google_books_api])
            print("Servicio de información de libros inicializado con Google Books API.")
        return cls._get_book_info_instance

    @classmethod
    def get_delete_service(cls) -> DeleteService:
        if cls._delete_service_instance is None:
            data_manager = cls.get_data_manager()
            cls._delete_service_instance = DeleteService(data_manager)
            print("DeleteService inicializado.")
        return cls._delete_service_instance

# Para probar este módulo directamente (opcional)
if __name__ == '__main__':
    print("Probando la inicialización de dependencias...")
    
    # Necesitamos estar en el directorio raíz del proyecto para que las importaciones relativas funcionen
    # Si ejecutas `python app/dependencies.py` directamente, las importaciones de `core` fallarán.
    # La prueba es más robusta si se ejecuta desde un script en la raíz del proyecto
    # que configure sys.path apropiadamente, o si el proyecto está instalado.

    # Ejemplo de cómo se podría ejecutar la prueba (asumiendo que sys.path está configurado):
    try:
        print(f"Probando desde: {os.getcwd()}")
        print(f"Contenido de sys.path[0]: {sys.path[0] if sys.path else 'Vacío'}")

        # Usar el DataManager en lugar del SQLManager directamente
        data_manager = DependencyFactory.get_data_manager()
        if data_manager:
            print(f"DataManager instanciado: {type(data_manager)}")
            
            # Prueba simple: intentar leer de una tabla (asumiendo que 'libros' existe)
            # Esto fallará si la tabla no existe y no se puede crear.
            try:
                libros = data_manager.fetch_query("SELECT isbn FROM libros LIMIT 1")
                print(f"Resultado de prueba de lectura de 'libros': {libros if libros else 'Tabla vacía o no existe.'}")
            except Exception as e_fetch:
                print(f"Error al probar fetch_query: {e_fetch}")
        else:
            print("Fallo al instanciar DataManager.")

        # Para GetBookInfo:
        # Necesitaríamos una implementación concreta de BookApiInterface para probar
        # from core.interfaces import BookApiInterface # Ya importada
        # class MockBookApi(BookApiInterface):
        #     def json_data(self, isbn: str) -> Optional[Dict[str, Any]]:
        #         if isbn == "123":
        #             return {"items": [{"volumeInfo": {"title": "Mock Book"}}]}
        #         return None
        #
        # mock_apis = [MockBookApi()]
        # book_service = DependencyFactory.get_book_info_service(apis_implementations=mock_apis)
        # if book_service:
        #     print(f"GetBookInfo instanciado: {type(book_service)}")
        #     info = book_service.extraer_info_json("123")
        #     print(f"Info del libro mock: {info}")
        # else:
        #     print("Fallo al instanciar GetBookInfo.")

    except ImportError as e_imp:
        print(f"Error de importación durante la prueba: {e_imp}")
        print("Asegúrate de ejecutar esta prueba desde un entorno donde 'core' y 'features' sean accesibles.")
        print("Por ejemplo, desde la raíz del proyecto, o con PYTHONPATH configurado.")
    except Exception as e:
        print(f"Error general durante la prueba de inicialización: {e}")
        import traceback
        traceback.print_exc() 