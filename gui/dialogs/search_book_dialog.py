"""
Diálogo para buscar libros existentes en el inventario.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtGui import QFont

from features.book_service import BookService # Necesitaremos BookService
from gui.common.styles import FONTS # Para estilos de fuente si es necesario

class SearchBookDialog(QDialog):
    """
    Diálogo para buscar libros en el inventario local.
    Permite al usuario ingresar criterios de búsqueda y ver los resultados.
    """
    def __init__(self, book_service: BookService, parent=None):
        """
        Inicializa el diálogo de búsqueda de libros.

        Args:
            book_service: Instancia del servicio de libros para acceder a la base de datos.
            parent (QWidget, opcional): Widget padre.
        """
        super().__init__(parent)
        self.setWindowTitle("Buscar Libro en Inventario")
        self.book_service = book_service # Guardar el servicio de libros
        self.font_family = FONTS.get("family", "Arial") # Usar fuente definida o fallback

        # Configuración inicial de la UI (temporal)
        self._setup_ui_placeholder()

        # Tamaño mínimo inicial (se puede ajustar después)
        self.setMinimumSize(600, 400)

    def _setup_ui_placeholder(self):
        """Configura una UI temporal para el diálogo."""
        layout = QVBoxLayout(self)
        
        title_label = QLabel("Buscar Libros")
        title_font = QFont(self.font_family, FONTS.get("size_large_title", 20), QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        info_label = QLabel("Funcionalidad de búsqueda de libros próximamente disponible aquí.")
        info_label.setFont(QFont(self.font_family, FONTS.get("size_medium", 12)))
        layout.addWidget(info_label)

        self.setLayout(layout)

if __name__ == '__main__':
    # Para pruebas directas del diálogo (requiere QApplication)
    import sys
    from PySide6.QtWidgets import QApplication
    from app.dependencies import DependencyFactory # Para obtener BookService real

    app = QApplication(sys.argv)

    # Crear dependencias necesarias para BookService
    print("Inicializando dependencias para prueba de SearchBookDialog...")
    data_manager = DependencyFactory.get_data_manager()
    book_info_service = DependencyFactory.get_book_info_service()
    book_service_instance = BookService(data_manager, book_info_service)
    print("Dependencias listas.")

    dialog = SearchBookDialog(book_service_instance)
    dialog.show()
    sys.exit(app.exec()) 