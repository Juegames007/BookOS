"""
Ventana principal de la aplicación.

Este módulo contiene la implementación de la ventana principal de la aplicación,
que muestra el menú con las diferentes opciones disponibles para el usuario.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSizePolicy, QSpacerItem, QMessageBox, QFrame, QApplication,
    QLineEdit # QStackedWidget, QListWidget, QAbstractScrollArea, QScrollArea, QCheckBox, QGraphicsOpacityEffect ya no son necesarios aquí
)
from PySide6.QtGui import QFont, QPixmap, QPainter, QIcon
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QEvent # QEasingCurve, QPropertyAnimation, QRect, QParallelAnimationGroup, Signal ya no son necesarios aquí
from typing import List, Dict, Any

from app.dependencies import DependencyFactory
from gui.common.widgets import CustomButton
from gui.common.styles import BACKGROUND_IMAGE_PATH, FONTS
from gui.dialogs.add_book_dialog import AddBookDialog
from gui.dialogs.search_book_dialog import SearchBookDialog
# from gui.components.paginated_results_widget import PaginatedResultsWidget # Ya no se usa directamente aquí
from gui.components.menu_section_widget import MenuSectionWidget
from features.book_service import BookService
from gui.dialogs.search_results_window import SearchResultsWindow # NUEVA IMPORTACIÓN

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
        book_info_fetcher = DependencyFactory.get_book_info_service()
        
        # Crear servicio de libros correctamente
        actual_book_service = BookService(data_manager, book_info_fetcher)
        
        # Crear y mostrar el diálogo inyectando el servicio
        dialog = AddBookDialog(actual_book_service, parent_window)
        dialog.exec()
    elif nombre_accion == "Buscar Libro":
        # Obtener dependencias necesarias para el diálogo
        data_manager = DependencyFactory.get_data_manager()
        book_info_fetcher = DependencyFactory.get_book_info_service()
        
        # Crear servicio de libros correctamente
        actual_book_service = BookService(data_manager, book_info_fetcher)
        
        # Crear y mostrar el diálogo inyectando el servicio
        dialog = SearchBookDialog(actual_book_service, parent_window)
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
    # Constantes de clase que ya no son necesarias aquí (movidas a los componentes)
    # RESULT_TABLE_WIDTH = 600      
    # HEADER_ROW_HEIGHT = 30       
    # BOOK_ROW_HEIGHT = 40         
    # MAX_BOOK_ROWS_PER_TABLE = 12 
    # TABLES_PER_PAGE = 2          
    # CELL_SPACING = 5             
    # ROW_SPACING = 5              
    # TABLE_CELL_PADDING = 5       
    INACTIVITY_TIMEOUT_MS = 60000  # 1 minuto

    # Atributo para almacenar la ventana de resultados si está abierta
    # self.current_search_results_window = None # Se puede manejar localmente en el método de búsqueda

    def __init__(self):
        """Inicializa la ventana principal."""
        super().__init__()
        self.setWindowTitle("BookOS - Gestión de Librería") # Título actualizado
        self.font_family = FONTS["family"]

        # Obtener el servicio de libros
        data_manager = DependencyFactory.get_data_manager()
        book_info_fetcher = DependencyFactory.get_book_info_service()
        self.book_service = BookService(data_manager, book_info_fetcher)

        # Configurar tamaño y posición inicial
        target_width = 1366
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
        
        # Widget central ahora será solo el widget del menú principal
        self.main_menu_widget = QWidget()
        self.setCentralWidget(self.main_menu_widget) # Ya no se usa QStackedWidget

        self.root_layout_main_menu = QVBoxLayout(self.main_menu_widget)
        self.root_layout_main_menu.setContentsMargins(20, 125, 20, 20)
        self.root_layout_main_menu.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.title_label = QLabel("BookOS")
        title_font = QFont(self.font_family, FONTS.get("size_xlarge", 20), QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; }")
        self.root_layout_main_menu.addWidget(self.title_label)

        self.root_layout_main_menu.addSpacerItem(QSpacerItem(0, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Crear el contenido del menú principal usando el nuevo MenuSectionWidget
        self.main_menu_content = MenuSectionWidget()
        self.main_menu_content.action_triggered.connect(self._handle_menu_action)
        self.main_menu_content.search_requested.connect(self._iniciar_busqueda_desde_componente)
        self.root_layout_main_menu.addWidget(self.main_menu_content)
        
        self.root_layout_main_menu.addStretch(1)
        
        # Eliminar creación de self.search_results_widget y QStackedWidget
        # self.search_results_widget = PaginatedResultsWidget()
        # self.search_results_widget.back_to_menu_requested.connect(self._mostrar_menu_principal_animado)
        # self.stacked_widget.addWidget(self.main_menu_widget)
        # self.stacked_widget.addWidget(self.search_results_widget)

        # Verificar si se pudo cargar la imagen de fondo
        if self.background_pixmap.isNull():
            print(f"ADVERTENCIA MUY IMPORTANTE: No se pudo cargar la imagen de fondo desde: {BACKGROUND_IMAGE_PATH}")
            self.main_menu_widget.setStyleSheet("QWidget { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #D32F2F, stop:1 #FF5252); }")
            error_label = QLabel(f"Error: No se pudo cargar '{BACKGROUND_IMAGE_PATH}'.\\nVerifica la ruta y el archivo.", self.main_menu_widget)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("QLabel { color: white; font-size: 18px; background-color: transparent; }")
            self.root_layout_main_menu.addWidget(error_label, stretch=1)
        else:
            self.main_menu_widget.setStyleSheet("QWidget { background: transparent; }")
            # self.search_results_widget.setStyleSheet("QWidget { background: transparent; }") # Ya no existe
            self._setup_ui_normal()

        # Timer de inactividad (ya no necesita cambiar de vista, podría cerrar la ventana de resultados si estuviera abierta)
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setInterval(self.INACTIVITY_TIMEOUT_MS)
        self.inactivity_timer.timeout.connect(self._handle_inactivity) # Cambiado a un nuevo manejador
        self.inactivity_timer.start()

        # Instalar filtro de eventos para detectar actividad
        self.installEventFilter(self)

        # self.animation_group = QParallelAnimationGroup(self) # Ya no es necesario para transiciones de main_window
        self.current_search_results_window = None # Para mantener una referencia si es necesario

    def _setup_ui_normal(self):
        """Configura la interfaz de usuario normal (con fondo) en el main_menu_widget.
           Este método ahora principalmente añade el MenuSectionWidget.
        """
        # La lógica de crear tarjetas, columnas, search_bar_finanzas ya no está aquí.
        # Se ha movido a MenuSectionWidget.
        pass # El contenido se crea en __init__ y se añade al root_layout_main_menu

    def _handle_inactivity(self):
        """Maneja la inactividad. Cierra la ventana de resultados si está abierta."""
        if hasattr(self, 'current_search_results_window') and self.current_search_results_window and self.current_search_results_window.isVisible():
            print("Cerrando ventana de resultados por inactividad.")
            self.current_search_results_window.close()
        # Podríamos añadir aquí lógica para volver a un estado "seguro" de la app si fuera necesario.
        # Por ahora, solo reinicia el timer si la ventana principal está activa.
        if self.isActiveWindow():
             self.inactivity_timer.start(self.INACTIVITY_TIMEOUT_MS)

    def _iniciar_busqueda_desde_componente(self, termino_busqueda: str, filtros: dict):
        """Se llama cuando SearchBarWidget emite la señal search_requested."""
        if termino_busqueda:
            print(f"Buscando (desde componente SearchBarWidget): {termino_busqueda}, Filtros: {filtros}")
            # Aquí aplicarías los filtros al self.book_service.buscar_libros si es necesario
            # Por ahora, la función buscar_libros solo toma el término.
            libros_encontrados = self.book_service.buscar_libros(termino_busqueda)
            
            # Si ya hay una ventana de resultados abierta, ciérrala o actualízala.
            if hasattr(self, 'current_search_results_window') and self.current_search_results_window:
                # self.current_search_results_window.update_content(libros_encontrados, termino_busqueda)
                # self.current_search_results_window.show()
                # self.current_search_results_window.raise_()
                # self.current_search_results_window.activateWindow()
                # O mejor, cerramos la anterior y abrimos una nueva para evitar estados complejos
                self.current_search_results_window.close()
                self.current_search_results_window = None

            self.current_search_results_window = SearchResultsWindow(libros_encontrados, termino_busqueda, self)
            self.current_search_results_window.show()
            
            # Reiniciar el temporizador de inactividad al mostrar la vista de búsqueda
            if self.inactivity_timer.isActive():
                self.inactivity_timer.start(self.INACTIVITY_TIMEOUT_MS)
        else:
            print("Término de búsqueda vacío (desde componente SearchBarWidget).")
            # Opcional: Cerrar la ventana de resultados si estaba abierta y se borra el término
            if hasattr(self, 'current_search_results_window') and self.current_search_results_window and self.current_search_results_window.isVisible():
                self.current_search_results_window.close()

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
        # El código anterior para centrar el results_content_widget ya no es necesario
        # debido al cambio a QStackedWidget y el manejo del layout de cada página.
        # if hasattr(self, 'results_pages_stack') and self.results_pages_stack.currentWidget():
        #     current_page = self.results_pages_stack.currentWidget()
        #     # Esta lógica necesitaría revisarse si quisiéramos hacer algo con el tamaño de la página actual
        #     # pero el centrado de las tablas dentro de la página lo maneja el QHBoxLayout de la página.
        pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # self._mostrar_menu_principal_animado() # Ya no se usa
            # En su lugar, podríamos cerrar la ventana de resultados si está abierta
            if hasattr(self, 'current_search_results_window') and self.current_search_results_window and self.current_search_results_window.isVisible():
                self.current_search_results_window.close()
        # La navegación por flechas ya no se maneja aquí, sino en PaginatedResultsWidget dentro de SearchResultsWindow
        # elif self.stacked_widget.currentWidget() == self.search_results_widget: ...
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

    def _handle_menu_action(self, accion: str):
        """Maneja las acciones disparadas desde los botones del menú principal (MainMenuCard)."""
        accion_pendiente(accion, self)

    # ELIMINAR MÉTODOS DE PAGINACIÓN VACÍOS
    # def _ir_a_pagina_siguiente_resultados(self):
    #     pass

    # def _ir_a_pagina_anterior_resultados(self):
    #     pass 