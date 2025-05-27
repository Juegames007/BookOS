import os # Para construir la ruta del icono/fondo
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QWidget
from PySide6.QtCore import Qt, Signal, QPoint # QPoint para paintEvent
from PySide6.QtGui import QIcon, QPainter, QPixmap # QPainter y QPixmap para paintEvent

from gui.components.paginated_results_widget import PaginatedResultsWidget
from gui.common.styles import FONTS

# Asumimos que la imagen de fondo está en app/imagenes/
# Construir la ruta de forma más robusta para el fondo
try:
    CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # Navegar dos niveles arriba desde gui/dialogs/ para llegar a la raíz del proyecto LibraryAPP
    # luego entrar a app/imagenes/
    BACKGROUND_IMAGE_SEARCH_PATH = os.path.join(os.path.dirname(os.path.dirname(CURRENT_SCRIPT_DIR)), "app", "imagenes", "fondo_buscar.png")
except NameError: # Fallback si __file__ no está definido (ej. algunos entornos interactivos)
    BACKGROUND_IMAGE_SEARCH_PATH = os.path.join("app", "imagenes", "fondo_buscar.png")

class SearchResultsWindow(QDialog):
    """
    Una ventana de diálogo para mostrar los resultados de búsqueda paginados.
    """
    def __init__(self, libros_encontrados: list, termino_busqueda: str, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle(f"Resultados de búsqueda para: '{termino_busqueda}'")
        self.setMinimumSize(800, 600) # Tamaño mínimo, ajustable según necesidad
        # Hacer el fondo del diálogo transparente para que se vea el paintEvent
        self.setStyleSheet("QDialog { background-color: transparent; }")

        self.background_pixmap = QPixmap(BACKGROUND_IMAGE_SEARCH_PATH)
        if self.background_pixmap.isNull():
            print(f"ADVERTENCIA: No se pudo cargar la imagen de fondo para SearchResultsWindow desde: {BACKGROUND_IMAGE_SEARCH_PATH}")
            # Fallback a un color sólido si la imagen no carga
            self.setStyleSheet("QDialog { background-color: #e0e0e0; }") 

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        self.results_widget = PaginatedResultsWidget()
        # Hacer el fondo del PaginatedResultsWidget transparente también
        self.results_widget.setStyleSheet("QWidget { background-color: transparent; }") 
        self.results_widget.update_results(libros_encontrados, termino_busqueda)
        
        # Conectar la señal de "volver al menú" del PaginatedResultsWidget para cerrar este diálogo
        self.results_widget.back_to_menu_requested.connect(self.accept) # o self.close

        self.layout.addWidget(self.results_widget)
        
        # Podríamos añadir un botón de cerrar explícito si se desea, 
        # aunque el de "Volver" del PaginatedResultsWidget ya cumple esa función.
        # self.close_button = QPushButton("Cerrar")
        # self.close_button.setFont(QFont(FONTS.get("family"), FONTS.get("size_normal")))
        # self.close_button.clicked.connect(self.accept)
        # self.layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignRight)

        self.setModal(False) # Para que no bloquee la ventana principal si es necesario

    def paintEvent(self, event):
        """Maneja el evento de pintar para dibujar el fondo."""
        painter = QPainter(self)
        if not self.background_pixmap.isNull():
            scaled_pixmap = self.background_pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            point = QPoint(0, 0)
            if scaled_pixmap.width() > self.width():
                point.setX(int((scaled_pixmap.width() - self.width()) / -2))
            if scaled_pixmap.height() > self.height():
                point.setY(int((scaled_pixmap.height() - self.height()) / -2))
            painter.drawPixmap(point, scaled_pixmap)
        else:
            # Si la imagen no se cargó, pinta un fondo sólido (redundante si el stylesheet ya lo hizo, pero seguro)
            painter.fillRect(self.rect(), Qt.GlobalColor.lightGray) 
        super().paintEvent(event)

    def keyPressEvent(self, event):
        """Maneja los eventos de teclado para la navegación por páginas y Esc."""
        if event.key() == Qt.Key_Escape:
            self.accept() # Cierra el diálogo
        elif event.key() == Qt.Key_Right:
            if hasattr(self.results_widget, '_ir_a_pagina_siguiente_resultados'):
                self.results_widget._ir_a_pagina_siguiente_resultados()
        elif event.key() == Qt.Key_Left:
            if hasattr(self.results_widget, '_ir_a_pagina_anterior_resultados'):
                self.results_widget._ir_a_pagina_anterior_resultados()
        else:
            super().keyPressEvent(event) # Importante para otros manejos de teclas

    def update_content(self, libros_encontrados: list, termino_busqueda: str):
        """Actualiza los resultados mostrados en la ventana."""
        self.setWindowTitle(f"Resultados de búsqueda para: '{termino_busqueda}'")
        self.results_widget.update_results(libros_encontrados, termino_busqueda)

if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    # Ejemplo de uso (requiere QApplication)
    app = QApplication(sys.argv)
    
    # Mock de datos para prueba
    mock_libros = [
        {"titulo": "Libro de Prueba 1", "autor": "Autor Uno", "isbn": "12345", "publicacion": "2023", "genero": "Ficción", "cantidad": 5, "precio": "19.99"},
        {"titulo": "Libro de Prueba 2", "autor": "Autor Dos", "isbn": "67890", "publicacion": "2022", "genero": "No Ficción", "cantidad": 3, "precio": "25.50"}
    ]
    
    if 'FONTS' not in globals(): # Mock FONTS si es necesario
        FONTS = {"family": "Arial", "size_normal": 12}


    dialog = SearchResultsWindow(mock_libros, "prueba")
    dialog.show()
    
    sys.exit(app.exec()) 