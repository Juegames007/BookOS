"""
Ventana principal de la aplicación.

Este módulo contiene la implementación de la ventana principal de la aplicación,
que muestra el menú con las diferentes opciones disponibles para el usuario.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSizePolicy, QSpacerItem, QMessageBox, QFrame, QApplication,
    QLineEdit, QStackedWidget, QListWidget, QAbstractScrollArea, QScrollArea
)
from PySide6.QtGui import QFont, QPixmap, QPainter, QIcon
from PySide6.QtCore import Qt, QPoint, QSize, QEasingCurve, QPropertyAnimation, QRect, QTimer, QEvent
from typing import List, Dict, Any

from app.dependencies import DependencyFactory
from gui.common.widgets import CustomButton
from gui.common.styles import BACKGROUND_IMAGE_PATH, FONTS
from gui.dialogs.add_book_dialog import AddBookDialog
from gui.dialogs.search_book_dialog import SearchBookDialog
from features.book_service import BookService

def accion_pendiente(nombre_accion, parent_window=None):
    """
    Muestra un mensaje de acción pendiente o ejecuta la acción correspondiente.
    
    Para algunas acciones específicas, lanza el diálogo correspondiente.
    Para el resto, muestra un mensaje de "acción pendiente".
    
    Args:
        nombre_accion: Nombre de la acción a ejecutar.
        parent_window: Ventana padre para mostrar mensajes o diálogos.
    """
    if nombre_accion == "Agregar Libro":
        # Obtener dependencias necesarias para el diálogo
        data_manager = DependencyFactory.get_data_manager()
        book_info_service = DependencyFactory.get_book_info_service()
        
        # Crear servicio de libros
        book_service = BookService(data_manager, book_info_service)
        
        # Crear y mostrar el diálogo inyectando el servicio
        dialog = AddBookDialog(book_service, parent_window)
        dialog.exec()
    elif nombre_accion == "Buscar Libro":
        # Obtener dependencias necesarias para el diálogo
        data_manager = DependencyFactory.get_data_manager()
        book_info_service = DependencyFactory.get_book_info_service()
        
        # Crear servicio de libros
        book_service = BookService(data_manager, book_info_service)
        
        # Crear y mostrar el diálogo inyectando el servicio
        dialog = SearchBookDialog(book_service, parent_window)
        dialog.exec()
    else:
        QMessageBox.information(parent_window, "Acción Pendiente",
                              f"La funcionalidad '{nombre_accion}' está pendiente de implementación.")

class VentanaGestionLibreria(QMainWindow):
    """
    Ventana principal de la aplicación de gestión de librería.
    
    Muestra un menú con tarjetas para las diferentes secciones:
    - Inventario
    - Finanzas
    - Ajustes
    
    Cada tarjeta contiene botones para las acciones específicas de esa sección.
    """
    # Constantes para la vista de resultados tipo tabla
    RESULT_TABLE_WIDTH = 600      # Ancho de una tabla de resultados completa (AUMENTADO)
    HEADER_ROW_HEIGHT = 30       # Altura de la fila de cabecera
    BOOK_ROW_HEIGHT = 40         # Altura de una fila de libro (reducida)
    MAX_BOOK_ROWS_PER_TABLE = 10 # Máximo de filas de libros por tabla (ajustable)
    CELL_SPACING = 5             # Espacio entre celdas en una fila
    ROW_SPACING = 5              # Espacio entre filas en una tabla (entre cabecera y primera fila, y entre filas de datos)
    TABLE_CELL_PADDING = 5       # Padding dentro de cada celda individual
    INACTIVITY_TIMEOUT_MS = 60000  # 1 minuto

    def __init__(self):
        """Inicializa la ventana principal."""
        super().__init__()
        self.setWindowTitle("Gestión Librería con PySide6")
        self.font_family = FONTS["family"]

        # Obtener el servicio de libros
        data_manager = DependencyFactory.get_data_manager()
        book_info_service = DependencyFactory.get_book_info_service()
        self.book_service = BookService(data_manager, book_info_service)

        # Configurar tamaño y posición inicial
        target_width = 1366  # Ancho suficiente para 3 columnas de 300px + espaciados
        target_height = 768
        try:
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                start_x = int(screen_geometry.center().x() - target_width / 2)
                start_y = int(screen_geometry.center().y() - target_height / 2)
                self.setGeometry(start_x, start_y, target_width, target_height)
            else:
                self.setGeometry(100, 100, target_width, target_height)
        except Exception:
            self.setGeometry(100, 100, target_width, target_height)

        # Configurar fondo
        self.background_pixmap = QPixmap(BACKGROUND_IMAGE_PATH)
        
        # Widget central ahora será un QStackedWidget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Crear el widget del menú principal (lo que antes era central_widget)
        self.main_menu_widget = QWidget()
        self.root_layout_main_menu = QVBoxLayout(self.main_menu_widget) # Layout para el contenido del menú
        self.root_layout_main_menu.setContentsMargins(20, 20, 20, 20)
        
        # Crear el widget de resultados de búsqueda
        self.search_results_widget = self._crear_vista_resultados_busqueda()

        # Añadir los widgets al QStackedWidget
        self.stacked_widget.addWidget(self.main_menu_widget)
        self.stacked_widget.addWidget(self.search_results_widget)

        # Verificar si se pudo cargar la imagen de fondo
        if self.background_pixmap.isNull():
            print(f"ADVERTENCIA MUY IMPORTANTE: No se pudo cargar la imagen de fondo desde: {BACKGROUND_IMAGE_PATH}")
            # Aplicar estilo de error al main_menu_widget en lugar del antiguo central_widget
            self.main_menu_widget.setStyleSheet("QWidget { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #D32F2F, stop:1 #FF5252); }")
            error_label = QLabel(f"Error: No se pudo cargar '{BACKGROUND_IMAGE_PATH}'.\\nVerifica la ruta y el archivo.", self.main_menu_widget)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("QLabel { color: white; font-size: 18px; background-color: transparent; }")
            self.root_layout_main_menu.addWidget(error_label, stretch=1)
        else:
            # El estilo de fondo transparente se aplica al main_menu_widget
            self.main_menu_widget.setStyleSheet("QWidget { background: transparent; }")
            # self.search_results_widget también debería ser transparente para ver el fondo de la ventana
            self.search_results_widget.setStyleSheet("QWidget { background: transparent; }")
            self._setup_ui_normal()

        # Timer de inactividad
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setInterval(self.INACTIVITY_TIMEOUT_MS)
        self.inactivity_timer.timeout.connect(self._mostrar_menu_principal_animado)
        self.inactivity_timer.start()
        # Instalar filtro de eventos para detectar actividad
        self.installEventFilter(self)

    def _setup_ui_normal(self):
        """Configura la interfaz de usuario normal (con fondo) en el main_menu_widget."""
        overall_content_widget = QWidget()
        layout_overall_content = QVBoxLayout(overall_content_widget)
        layout_overall_content.setContentsMargins(0, 0, 0, 0)
        layout_overall_content.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        layout_overall_content.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Título
        title_label = QLabel("Gestión Librería")
        title_font = QFont(self.font_family, FONTS["size_xlarge"], QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; }")
        layout_overall_content.addWidget(title_label)

        layout_overall_content.addSpacerItem(QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Contenedor para las tarjetas
        cards_holder_widget = QWidget()
        cards_holder_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_cards_holder = QHBoxLayout(cards_holder_widget)
        layout_cards_holder.setContentsMargins(0, 0, 0, 0)
        layout_cards_holder.setSpacing(25)  # Espacio horizontal entre columnas
        layout_cards_holder.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Configuraciones para las tarjetas
        card_width = 300
        main_card_height = 280
        extra_card_height = 160  # Para las tarjetas invisibles de relleno
        card_spacing = 15  # Espaciado vertical DENTRO de una columna

        # --- Columna para Inventario ---
        inventario_columna_widget = QWidget()
        inventario_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_inventario_columna = QVBoxLayout(inventario_columna_widget)
        layout_inventario_columna.setContentsMargins(0, 0, 0, 0)
        layout_inventario_columna.setSpacing(card_spacing)

        opciones_inventario_main = [
            {"icon": "agregar.png", "text": "  Agregar Libro", "action": "Agregar Libro"},
            {"icon": "buscar.png", "text": "  Buscar Libro", "action": "Buscar Libro"},
            {"icon": "modificar.png", "text": "  Modificar Libro", "action": "Modificar Libro"}
        ]

        inventario_card_principal = self._crear_tarjeta(
            "Inventario",
            opciones_inventario_main,
            card_width,
            main_card_height
        )
        layout_inventario_columna.addWidget(inventario_card_principal)

        # Tarjeta invisible de relleno para Inventario
        inventario_card_relleno_invisible = self._crear_tarjeta(
            None, [], card_width, extra_card_height, con_titulo=False
        )
        inventario_card_relleno_invisible.setVisible(False)
        layout_inventario_columna.addWidget(inventario_card_relleno_invisible)

        layout_inventario_columna.addStretch(1)
        layout_cards_holder.addWidget(inventario_columna_widget)

        # --- Columna para Finanzas ---
        finanzas_columna_widget = QWidget()
        finanzas_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_finanzas_columna = QVBoxLayout(finanzas_columna_widget)
        layout_finanzas_columna.setContentsMargins(0, 0, 0, 0)
        layout_finanzas_columna.setSpacing(card_spacing)

        # --- Barra de búsqueda para la columna de Finanzas ---
        search_bar_widget_finanzas = self._crear_barra_busqueda(card_width) # Usar card_width
        layout_finanzas_columna.addWidget(search_bar_widget_finanzas)
        layout_finanzas_columna.addSpacerItem(QSpacerItem(20, card_spacing, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)) # Espacio entre barra y tarjeta

        opciones_finanzas_main = [
            {"icon": "vender.png", "text": "  Vender Libro", "action": "Vender Libro"},
            {"icon": "ingreso.png", "text": "  Reportar Ingreso", "action": "Reportar Ingreso"},
            {"icon": "gasto.png", "text": "  Reportar Gasto", "action": "Reportar Gasto"},
        ]
        finanzas_card_principal = self._crear_tarjeta(
            "Finanzas",
            opciones_finanzas_main,
            card_width,
            main_card_height
        )
        layout_finanzas_columna.addWidget(finanzas_card_principal)

        opciones_finanzas_extra = [
            {"icon": "contabilidad.png", "text": "  Generar Contabilidad", "action": "Generar Contabilidad"},
            {"icon": "pedidos.png", "text": "  Generar Pedidos", "action": "Generar Pedidos"}
        ]
        finanzas_card_extra = self._crear_tarjeta(
            None,
            opciones_finanzas_extra,
            card_width,
            extra_card_height,
            con_titulo=False
        )
        layout_finanzas_columna.addWidget(finanzas_card_extra)

        layout_finanzas_columna.addStretch(1)
        layout_cards_holder.addWidget(finanzas_columna_widget)

        # --- Columna para Ajustes ---
        ajustes_columna_widget = QWidget()
        ajustes_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_ajustes_columna = QVBoxLayout(ajustes_columna_widget)
        layout_ajustes_columna.setContentsMargins(0, 0, 0, 0)
        layout_ajustes_columna.setSpacing(card_spacing)

        opciones_ajustes_main = [
            {"icon": "ajustes_finanzas.png", "text": "  Modificar Finanzas", "action": "Modificar Finanzas"},
            {"icon": "eliminar.png", "text": "  Eliminar Libro", "action": "Eliminar Libro"},
            {"icon": "salir.png", "text": "  Salir", "action": "SALIR_APP"}
        ]

        ajustes_card_principal = self._crear_tarjeta(
            "Ajustes",
            opciones_ajustes_main,
            card_width,
            main_card_height
        )
        layout_ajustes_columna.addWidget(ajustes_card_principal)

        # Tarjeta invisible de relleno para Ajustes
        ajustes_card_relleno_invisible = self._crear_tarjeta(
            None, [], card_width, extra_card_height, con_titulo=False
        )
        ajustes_card_relleno_invisible.setVisible(False)
        layout_ajustes_columna.addWidget(ajustes_card_relleno_invisible)

        layout_ajustes_columna.addStretch(1)
        layout_cards_holder.addWidget(ajustes_columna_widget)

        layout_overall_content.addWidget(cards_holder_widget)
        layout_overall_content.addStretch(1)

        self.root_layout_main_menu.addStretch(1) # Ahora se añade al layout del main_menu_widget
        self.root_layout_main_menu.addWidget(overall_content_widget, 0, Qt.AlignmentFlag.AlignHCenter)
        self.root_layout_main_menu.addStretch(1)

    def _crear_barra_busqueda(self, ancho: int):
        search_bar_container = QFrame()
        search_bar_container.setObjectName("searchBarContainer")
        search_bar_container.setFixedHeight(55)
        search_bar_container.setFixedWidth(ancho)
        search_bar_container.setStyleSheet(f"""
            QFrame#searchBarContainer {{
                background-color: rgba(255, 255, 255, 90);
                border-radius: 15px;
                border: 1px solid rgba(200, 200, 200, 100);
            }}
        """)

        layout = QHBoxLayout(search_bar_container)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(10)

        # Icono de búsqueda
        search_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "imagenes", "buscar.png")
        search_icon_label = QLabel()
        if os.path.exists(search_icon_path):
            search_pixmap = QPixmap(search_icon_path)
            search_icon_label.setPixmap(search_pixmap.scaled(QSize(24,24), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            search_icon_label.setText("?") # Placeholder si no hay icono
            print(f"Advertencia: No se pudo cargar el icono de búsqueda en: {search_icon_path}")
        search_icon_label.setStyleSheet("background-color: transparent; border: none;")


        # Campo de texto para búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search")
        self.search_input.setFixedHeight(35)
        self.search_input.setFont(QFont(self.font_family, FONTS["size_medium"]))
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: #333;
                padding-left: 5px;
            }
        """)
        self.search_input.returnPressed.connect(self._iniciar_busqueda) # Conectar returnPressed
        
        # Placeholder para el icono de menú (hamburguesa)
        # Usaremos un QLabel con texto por ahora, ya que no tenemos el icono exacto.
        # Este es el estilo de tres líneas horizontales (menú hamburguesa)
        menu_icon_label = QLabel("≡") 
        menu_icon_font = QFont(self.font_family, FONTS["size_large"], QFont.Weight.Bold)
        menu_icon_label.setFont(menu_icon_font)
        menu_icon_label.setStyleSheet("background-color: transparent; border: none; color: #555;")
        menu_icon_label.setCursor(Qt.CursorShape.PointingHandCursor)


        layout.addWidget(search_icon_label)
        layout.addWidget(self.search_input, 1) # El 1 es para que el QLineEdit ocupe el espacio disponible
        layout.addWidget(menu_icon_label)
        
        # Aplicar un ancho máximo al contenedor de la barra de búsqueda
        # para que no se extienda demasiado en pantallas grandes
        # Tomaremos un ancho un poco mayor que las tarjetas individuales
        # search_bar_container.setFixedWidth(400) # Comentado/Eliminado: el ancho se pasa como argumento


        return search_bar_container

    def _crear_tarjeta(self, titulo_str, opciones_data, ancho, alto, con_titulo=True):
        """
        Crea una tarjeta con título y botones.
        
        Args:
            titulo_str: Título de la tarjeta (None si no tiene título).
            opciones_data: Lista de diccionarios con 'icon', 'text' y 'action' para los botones.
            ancho: Ancho de la tarjeta.
            alto: Alto de la tarjeta.
            con_titulo: Si es True, muestra el título.
            
        Returns:
            Un QFrame con la tarjeta configurada.
        """
        tarjeta = QFrame()
        tarjeta.setFixedSize(ancho, alto)
        tarjeta.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 80); 
                border-radius: 25px;
                border: 1px solid rgba(220, 220, 220, 70);
            }}
        """)
        layout_tarjeta = QVBoxLayout(tarjeta)

        top_margin = 15  # Margen superior por defecto para tarjetas sin título con opciones
        if con_titulo and titulo_str:
            top_margin = 30
        elif not con_titulo and not opciones_data:  # Tarjeta de relleno invisible
            top_margin = 0  # O un valor pequeño si se prefiere, pero 0 para que sea solo espacio

        layout_tarjeta.setContentsMargins(30, top_margin, 30, 30)
        layout_tarjeta.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_tarjeta.setSpacing(10)

        if con_titulo and titulo_str:
            titulo_seccion = QLabel(titulo_str)
            font_titulo_seccion = QFont(self.font_family, FONTS["size_large"], QFont.Weight.Bold)
            titulo_seccion.setFont(font_titulo_seccion)
            titulo_seccion.setAlignment(Qt.AlignmentFlag.AlignLeft)
            titulo_seccion.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; border: none; }")
            layout_tarjeta.addWidget(titulo_seccion)

        for item_data in opciones_data:
            texto_visible_original = item_data["text"]
            nombre_archivo_icono = item_data["icon"]
            accion_definida = item_data["action"]

            # Corregir la ruta del icono para que apunte al directorio app/imagenes
            ruta_icono_completa = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "imagenes", nombre_archivo_icono)

            boton_personalizado = CustomButton(icon_path=ruta_icono_completa, text=texto_visible_original.strip())

            if accion_definida == "SALIR_APP":
                boton_personalizado.clicked.connect(self.close)
            else:
                boton_personalizado.clicked.connect(lambda accion=accion_definida: accion_pendiente(accion, self))

            layout_tarjeta.addWidget(boton_personalizado)

        layout_tarjeta.addStretch(1)
        return tarjeta

    def _crear_vista_resultados_busqueda(self):
        """Crea el widget para la vista de resultados de búsqueda con columnas dinámicas."""
        widget = QWidget()
        main_layout = QVBoxLayout(widget) 
        main_layout.setContentsMargins(30, 30, 30, 30) 
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.search_term_label = QLabel("Resultados para: ...")
        font_resultados = QFont(self.font_family, FONTS["size_large"], QFont.Weight.Bold)
        self.search_term_label.setFont(font_resultados)
        self.search_term_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.search_term_label.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 20px; }")
        main_layout.addWidget(self.search_term_label)

        self.results_scroll_area = QScrollArea()
        self.results_scroll_area.setWidgetResizable(True) 
        self.results_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.results_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) 
        self.results_scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        self.results_content_widget = QWidget()
        self.results_content_widget.setStyleSheet("QWidget { background-color: transparent; }")
        self.results_columns_layout = QHBoxLayout(self.results_content_widget) 
        self.results_columns_layout.setContentsMargins(0,0,0,0)
        self.results_columns_layout.setSpacing(15) 
        self.results_columns_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        
        self.results_scroll_area.setWidget(self.results_content_widget)
        main_layout.addWidget(self.results_scroll_area, 1)

        self.no_results_label = QLabel("No se encontraron libros que coincidan con tu búsqueda.")
        self.no_results_label.setFont(QFont(self.font_family, FONTS["size_medium"]))
        self.no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_results_label.setStyleSheet("QLabel { color: #555; background-color: transparent; }")
        self.no_results_label.setWordWrap(True)
        self.no_results_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        main_layout.addWidget(self.no_results_label)
        self.no_results_label.hide()

        self.boton_volver_menu = CustomButton(text="Volver al Menú Principal")
        layout_boton = QHBoxLayout()
        layout_boton.addStretch(1)
        layout_boton.addWidget(self.boton_volver_menu)
        layout_boton.addStretch(1)
        main_layout.addLayout(layout_boton)
        
        self.boton_volver_menu.clicked.connect(self._mostrar_menu_principal_animado)

        widget.setStyleSheet("background: transparent;")
        return widget

    def _iniciar_busqueda(self):
        """Se llama cuando se presiona Enter en la barra de búsqueda."""
        termino_busqueda = self.search_input.text().strip()
        if termino_busqueda:
            print(f"Buscando: {termino_busqueda}")
            # Llamar al servicio para buscar libros
            libros_encontrados = self.book_service.buscar_libros(termino_busqueda)
            self._actualizar_display_resultados(libros_encontrados) # Actualizar la UI de resultados
            self._mostrar_vista_busqueda_animado(termino_busqueda)
        else:
            print("Término de búsqueda vacío.")
            # Opcional: podríamos limpiar la vista de resultados si el término es vacío
            # y el usuario presiona enter, o simplemente no hacer nada.
            # Por ahora, no hacemos nada si está vacío.

    def _actualizar_display_resultados(self, libros: List[Dict[str, Any]]):
        """Actualiza la vista de resultados con un layout de tablas con celdas individuales y numeración."""
        while self.results_columns_layout.count():
            item = self.results_columns_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not libros:
            self.results_scroll_area.hide()
            self.no_results_label.show()
        else:
            self.no_results_label.hide()
            self.results_scroll_area.show()

            current_table_frame = None
            current_table_layout = None 
            book_rows_in_current_table = 0
            # Reducir el peso de la columna de numeración en proporción
            column_weights = [1, 5, 4, 4] # Antes: [1, 3, 2, 2]
            headers = ["#", "Título", "Autor", "Categoría"]

            # Estilo base para las celdas (glassmorphism)
            cell_style_sheet = f"""
                QFrame {{
                    background-color: rgba(255, 255, 255, 0.45);
                    border-radius: 6px;
                    border: 1px solid rgba(255, 255, 255, 0.6);
                }}
                QLabel {{
                    background-color: transparent;
                    border: none;
                    padding: {self.TABLE_CELL_PADDING}px;
                }}
            """
            header_cell_style_sheet = f"""
                QFrame {{
                    background-color: rgba(235, 235, 245, 0.6);
                    border-radius: 6px;
                    border: 1px solid rgba(255, 255, 255, 0.5);
                }}
                QLabel {{
                    background-color: transparent;
                    border: none;
                    padding: {self.TABLE_CELL_PADDING}px;
                    font-weight: bold;
                }}
            """

            for i, libro_data in enumerate(libros):
                if current_table_frame is None or book_rows_in_current_table >= self.MAX_BOOK_ROWS_PER_TABLE:
                    current_table_frame = QFrame()
                    current_table_frame.setFixedWidth(self.RESULT_TABLE_WIDTH)
                    current_table_frame.setStyleSheet(f"""
                        QFrame {{
                            background-color: rgba(220, 220, 235, 0.35);
                            border-radius: 10px; 
                            border: 1px solid rgba(255, 255, 255, 0.2);
                        }}
                    """)
                    current_table_layout = QVBoxLayout(current_table_frame)
                    current_table_layout.setContentsMargins(self.ROW_SPACING, self.ROW_SPACING, self.ROW_SPACING, self.ROW_SPACING)
                    current_table_layout.setSpacing(self.ROW_SPACING)
                    current_table_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
                    self.results_columns_layout.addWidget(current_table_frame)
                    book_rows_in_current_table = 0

                    # --- Fila de Cabecera con Celdas Individuales ---
                    header_row_widget = QWidget()
                    header_row_widget.setFixedHeight(self.HEADER_ROW_HEIGHT)
                    header_row_layout = QHBoxLayout(header_row_widget)
                    header_row_layout.setContentsMargins(0,0,0,0)
                    header_row_layout.setSpacing(self.CELL_SPACING)
                    for h_text, weight in zip(headers, column_weights):
                        cell_frame = QFrame()
                        cell_frame.setStyleSheet(header_cell_style_sheet)
                        cell_layout = QVBoxLayout(cell_frame)
                        cell_layout.setContentsMargins(0,0,0,0)
                        lbl = QLabel(h_text)
                        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        lbl.setFont(QFont(self.font_family, FONTS["size_small"], QFont.Weight.Bold))
                        lbl.setStyleSheet("color: #222; background-color:transparent;")
                        cell_layout.addWidget(lbl)
                        header_row_layout.addWidget(cell_frame, weight)
                    current_table_layout.addWidget(header_row_widget)

                # --- Fila de Libro con Celdas Individuales ---
                book_row_widget = QWidget() 
                book_row_widget.setFixedHeight(self.BOOK_ROW_HEIGHT)
                book_row_layout = QHBoxLayout(book_row_widget)
                book_row_layout.setContentsMargins(0,0,0,0)
                book_row_layout.setSpacing(self.CELL_SPACING)

                # Numeración
                numero = i + 1
                titulo = libro_data.get("Título", "N/A")
                autor = libro_data.get("Autor", "N/A")
                categorias_list = libro_data.get("Categorías", [])
                categorias = ", ".join(categorias_list) if categorias_list else "-"
                data_fields = [str(numero), titulo, autor, categorias]

                for field_text, weight in zip(data_fields, column_weights):
                    cell_frame = QFrame()
                    cell_frame.setStyleSheet(cell_style_sheet)
                    cell_layout = QVBoxLayout(cell_frame)
                    cell_layout.setContentsMargins(0,0,0,0)
                    lbl = QLabel(field_text)
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setFont(QFont(self.font_family, FONTS["size_small"]-1))
                    lbl.setWordWrap(True)
                    lbl.setStyleSheet("color: #333; background-color:transparent;")
                    cell_layout.addWidget(lbl)
                    book_row_layout.addWidget(cell_frame, weight)
                
                current_table_layout.addWidget(book_row_widget)
                book_rows_in_current_table += 1

            if current_table_layout:
                 current_table_layout.addStretch(1)

    def _mostrar_vista_busqueda_animado(self, termino_busqueda):
        """Muestra la vista de resultados de búsqueda con animación."""
        current_widget = self.stacked_widget.currentWidget()
        next_widget = self.search_results_widget

        if current_widget == next_widget:
            return

        self.search_term_label.setText(f"Resultados para: \"{termino_busqueda}\"")

        # 1. Posicionar next_widget fuera de la pantalla (a la derecha)
        # Asegurarse de que tenga el tamaño correcto que tendrá en el stack.
        # Usamos self.stacked_widget.rect() para obtener las dimensiones correctas.
        rect_stacked = self.stacked_widget.rect()
        next_widget.setGeometry(rect_stacked.width(), 0, rect_stacked.width(), rect_stacked.height())
        
        # 2. Hacer next_widget visible y ponerlo encima del widget actual
        next_widget.show()
        next_widget.raise_()

        # 3. Animación para current_widget (sale hacia la izquierda)
        # Usamos variables locales para las animaciones para evitar sobreescribir self.anim si se llama rápido
        anim_current_slide_out = QPropertyAnimation(current_widget, b"geometry")
        anim_current_slide_out.setDuration(500)
        anim_current_slide_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim_current_slide_out.setStartValue(current_widget.geometry()) 
        anim_current_slide_out.setEndValue(QRect(-current_widget.width(), 0, current_widget.width(), current_widget.height()))

        # 4. Animación para next_widget (entra desde la derecha)
        anim_next_slide_in = QPropertyAnimation(next_widget, b"geometry")
        anim_next_slide_in.setDuration(500)
        anim_next_slide_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim_next_slide_in.setStartValue(next_widget.geometry()) 
        anim_next_slide_in.setEndValue(rect_stacked) 

        # Guardar las animaciones como atributos de instancia si necesitamos cancelarlas o interactuar más tarde
        self.current_animation_group = [anim_current_slide_out, anim_next_slide_in]

        # 5. Cuando la animación de entrada termina:
        def transition_finished():
            self.stacked_widget.setCurrentWidget(next_widget) 
            current_widget.hide() 
            # Limpiar referencias para permitir recolección de basura si es necesario
            self.current_animation_group = [] 
            try:
                anim_next_slide_in.finished.disconnect(transition_finished)
            except RuntimeError: pass
            # No necesitamos desconectar anim_current_slide_out.finished explícitamente si no tiene slots conectados

        anim_next_slide_in.finished.connect(transition_finished)
        
        anim_current_slide_out.start()
        anim_next_slide_in.start()
        
    def _mostrar_menu_principal_animado(self):
        """Muestra el menú principal con animación."""
        current_widget = self.stacked_widget.currentWidget() 
        next_widget = self.main_menu_widget 

        if current_widget == next_widget:
            return

        # 1. Posicionar next_widget (main_menu_widget) fuera de pantalla (a la izquierda)
        rect_stacked = self.stacked_widget.rect()
        next_widget.setGeometry(-rect_stacked.width(), 0, rect_stacked.width(), rect_stacked.height())
        
        # 2. Hacer next_widget visible y ponerlo encima
        next_widget.show()
        next_widget.raise_()

        # 3. Animación para current_widget (search_results_widget) (sale hacia la derecha)
        anim_current_slide_out_reverse = QPropertyAnimation(current_widget, b"geometry")
        anim_current_slide_out_reverse.setDuration(500)
        anim_current_slide_out_reverse.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim_current_slide_out_reverse.setStartValue(current_widget.geometry())
        anim_current_slide_out_reverse.setEndValue(QRect(rect_stacked.width(), 0, current_widget.width(), current_widget.height()))

        # 4. Animación para next_widget (main_menu_widget) (entra desde la izquierda)
        anim_next_slide_in_reverse = QPropertyAnimation(next_widget, b"geometry")
        anim_next_slide_in_reverse.setDuration(500)
        anim_next_slide_in_reverse.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim_next_slide_in_reverse.setStartValue(next_widget.geometry()) 
        anim_next_slide_in_reverse.setEndValue(rect_stacked)

        self.current_animation_group = [anim_current_slide_out_reverse, anim_next_slide_in_reverse]

        # 5. Cuando la animación de entrada termina:
        def transition_reverse_finished():
            self.stacked_widget.setCurrentWidget(next_widget)
            current_widget.hide()
            self.current_animation_group = []
            try:
                anim_next_slide_in_reverse.finished.disconnect(transition_reverse_finished)
            except RuntimeError: pass

        anim_next_slide_in_reverse.finished.connect(transition_reverse_finished)

        anim_current_slide_out_reverse.start()
        anim_next_slide_in_reverse.start()

    def paintEvent(self, event):
        """Maneja el evento de pintar para dibujar el fondo."""
        if not self.background_pixmap.isNull():
            painter = QPainter(self)
            scaled_pixmap = self.background_pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            point = QPoint(0, 0)
            if scaled_pixmap.width() > self.width():
                point.setX(int((scaled_pixmap.width() - self.width()) / -2))
            if scaled_pixmap.height() > self.height():
                point.setY(int((scaled_pixmap.height() - self.height()) / -2))
            painter.drawPixmap(point, scaled_pixmap)
        super().paintEvent(event)

    def resizeEvent(self, event):
        """Maneja el evento de redimensionamiento."""
        super().resizeEvent(event) 
        # Centrado real del recuadro de resultados
        if hasattr(self, 'results_scroll_area') and hasattr(self, 'results_content_widget'):
            scroll_width = self.results_scroll_area.viewport().width()
            self.results_content_widget.setMinimumWidth(scroll_width)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._mostrar_menu_principal_animado()
        super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        # Reinicia el temporizador de inactividad en cualquier evento de mouse o teclado
        if event.type() in [
            QEvent.Type.MouseMove,
            QEvent.Type.KeyPress,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease
        ]:
            if self.inactivity_timer.isActive(): # Solo reiniciar si está activo
                self.inactivity_timer.start(self.INACTIVITY_TIMEOUT_MS) # Reinicia con el intervalo completo
        return super().eventFilter(obj, event) 