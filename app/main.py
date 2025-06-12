"""
Punto de entrada principal de la aplicación.

Este módulo es el punto de entrada para ejecutar la aplicación. Se encarga de:
1. Inicializar las dependencias (base de datos, servicios, etc.)
2. Lanzar la interfaz gráfica de usuario
"""

import sys
import os

# Añadir el directorio raíz del proyecto al sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importar recursos DESPUÉS de ajustar el path
import gui.resources.resources_rc

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

from app.dependencies import DependencyFactory                                                      
from gui.main_window import VentanaGestionLibreria
from gui.common.utils import load_fonts

def main():
    """
    Función principal que inicia la aplicación.
    
    Inicializa las dependencias necesarias y lanza la interfaz gráfica.
    Maneja errores críticos que puedan ocurrir durante la inicialización.
    """
    app = QApplication(sys.argv)

    # Cargar fuentes personalizadas
    load_fonts()

    # El DependencyFactory se encargará de inicializar el DataManager (SQLManager)
    # cuando se le pida por primera vez.
    DependencyFactory.get_data_manager()
    
    # --- Inicializar Dependencias ---
    try:
        print("Inicializando dependencias (esto configurará la base de datos)...")
        sql_manager = DependencyFactory.get_sql_manager()
        book_info_service = DependencyFactory.get_book_info_service()
        print("Dependencias inicializadas.")
    except Exception as e:
        print(f"Error Crítico al inicializar dependencias: {e}")
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setText("Error Crítico al Inicializar Dependencias")
        error_dialog.setInformativeText(f"No se pudieron inicializar los servicios necesarios para la aplicación.\nError: {e}\n\nLa aplicación podría no funcionar correctamente. Verifique la consola para más detalles.")
        error_dialog.setWindowTitle("Error de Inicialización")
        error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_dialog.exec()
        # Si el error es fatal, descomentar:
        # return 1

    # Crear y mostrar la ventana principal
    ventana = VentanaGestionLibreria()
    ventana.show()
    
    # Iniciar el bucle de eventos
    return app.exec()

if __name__ == "__main__":
    main() 