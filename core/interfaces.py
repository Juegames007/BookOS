from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple # Importamos los tipos necesarios
import pandas as pd # Necesario para el type hint en DataManagerInterface

class HttpClientInterface(ABC):
    @abstractmethod
    def get(self, url: str):
        pass

class BookApiInterface(ABC):
    @abstractmethod
    def json_data(self, query: str):
        pass

class DataManagerInterface(ABC):
    @abstractmethod
    def leer_hoja(self, hoja: str) -> pd.DataFrame: # Mantenemos pd.DataFrame por ahora
        pass

    @abstractmethod
    def escribir_hoja(self, hoja: str, df: pd.DataFrame): # Mantenemos pd.DataFrame
        pass

    @abstractmethod
    def crear_hoja_si_no_existe(self, hoja: str, columnas: list):
        pass

    @abstractmethod
    def limpiar_libros_agotados(self, hoja: str = "Estanterias"):
        pass

class MenuInterface(ABC):
    @abstractmethod
    def run(self):
        pass