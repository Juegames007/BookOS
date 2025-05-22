import requests
from .interfaces import HttpClientInterface # Importación relativa de la interfaz

class RequestsClient(HttpClientInterface):
    def get(self, url: str):
        """
        Realiza una solicitud GET a la URL especificada.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # Lanza una excepción para códigos de error HTTP (4xx o 5xx)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error al realizar la solicitud HTTP a {url}: {e}")
            raise