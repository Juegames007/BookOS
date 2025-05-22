# No es necesario 'import requests' aquí directamente si HttpClientInterface lo abstrae.
from core.interfaces import BookApiInterface, HttpClientInterface

class GoogleBooksApi(BookApiInterface):
    def __init__(self, http_client: HttpClientInterface):
        self.base_url = "https://www.googleapis.com/books/v1/volumes"
        self.http_client = http_client

    def json_data(self, isbn: str): # Cambiado el nombre del parámetro a 'isbn' para claridad
        """
        Busca datos de un libro por ISBN usando la API de Google Books.
        Retorna los datos en formato JSON (como un diccionario).
        """
        # Validar que el isbn no esté vacío podría ser una buena adición aquí
        if not isbn:
            # Podrías retornar un error, un diccionario vacío, o None
            print("Advertencia: El ISBN proporcionado está vacío.")
            return {} 

        url = f"{self.base_url}?q=isbn:{isbn}"
        try:
            response = self.http_client.get(url) # http_client.get ya debería manejar errores de request
            return response.json()
        except Exception as e:
            # Si http_client.get relanza excepciones, o si response.json() falla
            print(f"Error al obtener o procesar datos de Google Books para ISBN {isbn}: {e}")
            # Devolver un diccionario vacío o None podría ser apropiado aquí
            return {}