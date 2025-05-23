"""
Diálogo para buscar libros existentes en el inventario.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QWidget, QFrame, QHBoxLayout, QSpacerItem
from PySide6.QtGui import QFont, QPixmap, QPainter
from PySide6.QtCore import Qt, QPoint

from features.book_service import BookService # Necesitaremos BookService
from gui.common.styles import FONTS, COLORS, STYLES # Añadido COLORS, STYLES

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

        self._setup_ui()

        self.setMinimumSize(700, 500) # Ajustar tamaño según necesidad

    def _setup_ui(self):
        """Configura la interfaz de usuario para la búsqueda de libros."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # --- Barra de Búsqueda ---
        search_bar_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por título, autor, ISBN...")
        self.search_input.setFixedHeight(35)
        # Aplicar estilo similar al de AddBookDialog para consistencia
        self.search_input.setStyleSheet(STYLES["input_field"] + 
                                    f"QLineEdit::placeholder {{ font-size: {FONTS['size_small']}px; }}") 
        self.search_input.returnPressed.connect(self._perform_search)
        search_bar_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Buscar")
        self.search_button.setFixedHeight(35)
        self.search_button.setStyleSheet(STYLES["button_primary_full"])
        self.search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_button.clicked.connect(self._perform_search)
        search_bar_layout.addWidget(self.search_button)
        
        main_layout.addLayout(search_bar_layout)
        main_layout.addSpacing(15)

        # --- Área de Resultados de Búsqueda (con Scroll) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        
        self.results_widget = QWidget() # Widget interno para el scroll area
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setContentsMargins(5,5,5,5)
        self.results_layout.setSpacing(10)
        self.results_widget.setStyleSheet("QWidget { background-color: transparent; }") # Fondo transparente para el widget interno

        self.scroll_area.setWidget(self.results_widget)
        main_layout.addWidget(self.scroll_area) # Añadir el scroll area al layout principal

        self.setLayout(main_layout)
        self.search_input.setFocus()

    def _clear_search_results(self):
        """Limpia los widgets de resultados del layout de búsqueda."""
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        #Añadir un stretch al final para asegurar que los nuevos elementos se alinean arriba
        self.results_layout.addStretch(1)

    def _perform_search(self):
        """Ejecuta la búsqueda y muestra los resultados."""
        query = self.search_input.text().strip()
        self._clear_search_results()

        if not query:
            # Opcional: mostrar un mensaje si la búsqueda está vacía, o simplemente no mostrar nada
            # info_label = QLabel("Ingrese un término para buscar.")
            # self.results_layout.insertWidget(0, info_label) # Insertar al principio
            # self.results_layout.setAlignment(info_label, Qt.AlignmentFlag.AlignCenter)
            return

        libros_encontrados = self.book_service.buscar_libros(query)

        if libros_encontrados:
            for libro_data in libros_encontrados:
                tarjeta_libro = self._crear_tarjeta_resultado(libro_data)
                self.results_layout.insertWidget(self.results_layout.count() -1, tarjeta_libro) # Insertar antes del stretch
        else:
            no_results_label = QLabel("No se encontraron libros para su búsqueda.")
            no_results_label.setFont(QFont(self.font_family, FONTS.get("size_medium", 12)))
            no_results_label.setStyleSheet("QLabel { color: black; padding: 20px; }")
            self.results_layout.insertWidget(self.results_layout.count() -1, no_results_label, 0, Qt.AlignmentFlag.AlignCenter)

        # Asegurar que el stretch esté al final
        if self.results_layout.count() == 0 or not isinstance(self.results_layout.itemAt(self.results_layout.count() - 1), QSpacerItem):
             self.results_layout.addStretch(1)


    def _crear_tarjeta_resultado(self, libro_data: dict) -> QFrame:
        """Crea un QFrame estilizado para mostrar la información de un libro."""
        tarjeta = QFrame()
        tarjeta.setObjectName("ResultCard")
        tarjeta.setMinimumHeight(120) # Altura mínima para cada tarjeta
        tarjeta.setStyleSheet(f"""
            QFrame#ResultCard {{
                background-color: {COLORS.get("background_light", "rgba(240,240,240,100)")}; /* Vidrioformismo */
                border-radius: 10px;
                padding: 12px;
                margin-bottom: 5px; /* Espacio entre tarjetas */
                border: 1px solid {COLORS.get("border_light", "rgba(200,200,200,70)")};
            }}
            QLabel {{
                background-color: transparent;
                color: {COLORS.get("text_primary", "#202427")};
                border: none;
            }}
        """)

        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setSpacing(6)

        titulo_label = QLabel(f"<b>{libro_data.get('Título', 'N/A')}</b>")
        titulo_label.setFont(QFont(self.font_family, FONTS.get("size_medium", 13)))
        titulo_label.setWordWrap(True)
        layout_tarjeta.addWidget(titulo_label)

        autor_isbn_layout = QHBoxLayout()
        autor_label = QLabel(f"<i>Autor:</i> {libro_data.get('Autor', 'N/A')}")
        autor_label.setFont(QFont(self.font_family, FONTS.get("size_normal", 11)))
        autor_isbn_layout.addWidget(autor_label)
        autor_isbn_layout.addStretch()
        isbn_label = QLabel(f"<i>ISBN:</i> {libro_data.get('ISBN', 'N/A')}")
        isbn_label.setFont(QFont(self.font_family, FONTS.get("size_normal", 11)))
        autor_isbn_layout.addWidget(isbn_label)
        layout_tarjeta.addLayout(autor_isbn_layout)

        if libro_data.get("Editorial"): 
            editorial_label = QLabel(f"<i>Editorial:</i> {libro_data.get('Editorial')}")
            editorial_label.setFont(QFont(self.font_family, FONTS.get("size_small", 10)))
            layout_tarjeta.addWidget(editorial_label)

        precio_pos_layout = QHBoxLayout()
        precio_text = f"Precio: ${libro_data.get('Precio', 0):,.0f}".replace(",",".")
        precio_label = QLabel(precio_text)
        precio_label.setFont(QFont(self.font_family, FONTS.get("size_normal", 11), QFont.Weight.Bold))
        precio_pos_layout.addWidget(precio_label)
        precio_pos_layout.addStretch()
        if libro_data.get("Posición"):
            posicion_label = QLabel(f"Pos: {libro_data.get('Posición', '-')} (Cant: {libro_data.get('Cantidad', 0)})")
            posicion_label.setFont(QFont(self.font_family, FONTS.get("size_normal", 11)))
            precio_pos_layout.addWidget(posicion_label)
        layout_tarjeta.addLayout(precio_pos_layout)

        # Aquí se podría añadir la imagen si tuviéramos la lógica para cargarla
        # if libro_data.get("Imagen"): 
        #    # Lógica para cargar QPixmap desde URL o path

        layout_tarjeta.addStretch(1)
        return tarjeta

# Eliminar el bloque if __name__ == '__main__': o actualizarlo si se quiere probar este diálogo directamente
# ... (el if __name__ block se eliminará o se comentará)

""" # Comienzo de un bloque de comentario para el if __name__
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
""" # Fin del bloque de comentario 