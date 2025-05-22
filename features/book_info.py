from typing import List, Dict, Any, Optional
from core.interfaces import BookApiInterface

class GetBookInfo:
    def __init__(self, apis: List[BookApiInterface]):
        self.apis = apis

    def _try_apis(self, isbn: str) -> Dict[str, Any]:
        """
        Intenta obtener datos del libro desde las APIs configuradas.
        Retorna el primer resultado exitoso.
        """
        for api_client in self.apis:
            try:
                data = api_client.json_data(isbn)
                if self._has_data(data, isbn): # Pasamos isbn a _has_data para consistencia
                    return data
            except Exception as e:
                # Podrías loggear este error si una API específica falla
                # print(f"Advertencia: La API {type(api_client).__name__} falló para el ISBN {isbn}. Error: {e}")
                continue # Intenta con la siguiente API
        return {} # Retorna un diccionario vacío si ninguna API tiene éxito o encuentra datos

    def _has_data(self, data: Dict[str, Any], query: str) -> bool:
        """
        Verifica si los datos de la API son válidos y contienen información.
        'query' podría ser el ISBN u otro identificador usado.
        """
        if not data: # Si data es None o un diccionario vacío
            return False
        # Específico para Google Books API
        if "items" in data and data["items"]: # Asegura que 'items' exista y no esté vacío
            return True
        # Podrías añadir condiciones para otras APIs aquí, por ejemplo:
        # elif "otro_identificador_clave" in data:
        #     return True
        # El chequeo original de 'f"ISBN:{query}" in data' parece muy específico
        # y podría no ser generalizable si 'data' es un JSON complejo.
        # Considera si esa condición sigue siendo necesaria o cómo adaptarla.
        return False

    def extraer_info_json(self, isbn: str) -> Optional[Dict[str, Any]]:
        """
        Extrae y formatea la información del libro desde el JSON obtenido de la API.
        Retorna un diccionario con la información del libro o None si no se encuentra.
        """
        if not isbn: # Validación básica
            # print("Error: Se requiere un ISBN para extraer información.")
            return None

        data = self._try_apis(isbn)

        if not data: # Si _try_apis retornó un diccionario vacío
            return None

        # Procesamiento específico para Google Books API
        # Esto necesitaría ser más genérico si usas múltiples APIs con formatos diferentes
        # o podrías tener métodos de parseo específicos por API.
        if "items" in data and data["items"]: # Asegurarse de que 'items' existe y tiene contenido
            try:
                volume_info = data["items"][0].get("volumeInfo", {}) # Usar .get() para seguridad
                
                # Extraer categorías, asegurando que sea una lista
                categories = volume_info.get("categories", [])
                if not isinstance(categories, list):
                    categories = [str(categories)] if categories else []


                # Construir el diccionario de información del libro
                book_details = {
                    "ISBN": isbn,
                    "Título": volume_info.get("title", "Desconocido"),
                    # Asegurar que el autor sea una cadena, tomando el primero si hay lista
                    "Autor": volume_info.get("authors", ["Desconocido"])[0] if volume_info.get("authors") else "Desconocido",
                    "Editorial": volume_info.get("publisher", "Desconocido"),
                    "Imagen": volume_info.get("imageLinks", {}).get("thumbnail", ""),
                    "Categorías": categories, # Ya es una lista
                    "Posición": "",  # Se llenará después, o se puede quitar si no es de la API
                    "Cantidad": 1    # Cantidad inicial, se puede ajustar después
                }
                return book_details
            except (IndexError, KeyError, TypeError) as e:
                # Error al parsear la respuesta esperada de Google Books
                print(f"Error al parsear la información del libro desde la API para ISBN {isbn}: {e}")
                return None
        
        # Si se llega aquí, es porque 'data' no tenía el formato esperado de Google Books
        # o _has_data falló por otra razón después de que _try_apis devolviera datos.
        return None
