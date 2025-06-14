# ARCHIVO MODIFICADO: juegames007/bookos/BookOS-e73bc84f0a94b0c519fddbb143bbf5041f6aa9c0/gui/main_window.py

"""
Ventana principal de la aplicación.

Este módulo contiene la implementación de la ventana principal de la aplicación,
que muestra el menú con las diferentes opciones disponibles para el usuario.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSizePolicy, QSpacerItem, QMessageBox, QFrame, QApplication,
    QLineEdit, QInputDialog, QGraphicsBlurEffect, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView
)
from PySide6.QtGui import QFont, QPixmap, QPainter, QIcon
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QEvent
from typing import List, Dict, Any

from app.dependencies import DependencyFactory
from gui.common.widgets import CustomButton
from gui.common.styles import BACKGROUND_IMAGE_PATH, FONTS
from gui.dialogs.add_book_dialog import AddBookDialog
from gui.dialogs.modify_book_dialog import ModifyBookDialog
from gui.dialogs.reservation_dialog import ReservationDialog
from gui.dialogs.reservation_options_dialog import ReservationOptionsDialog
from gui.dialogs.existing_reservations_dialog import ExistingReservationsDialog
from gui.components.menu_section_widget import MenuSectionWidget
from gui.dialogs.sell_book_dialog import SellBookDialog
from gui.dialogs.return_dialog import ReturnDialog
from features.book_service import BookService
from features.reservation_service import ReservationService
from features.sell_service import SellService
from features.return_service import ReturnService
from features.delete_service import DeleteService
from features.egreso_service import EgresoService
from features.finance_service import FinanceService
from gui.dialogs.search_results_window import SearchResultsWindow
from gui.dialogs.delete_book_dialog import DeleteBookDialog
from gui.dialogs.egreso_dialog import EgresoDialog
from core.sqlmanager import SQLManager
from gui.dialogs.modify_finances_dialog import ModifyFinancesDialog

class VentanaGestionLibreria(QMainWindow):
    """
    Ventana principal de la aplicación de gestión de librería.
    """
    def __init__(self):
        super().__init__()
        self.background_pixmap = QPixmap()
        self.current_dialog = None
        self.setWindowTitle("BookOS - Gestión de Librería")
        self.font_family = FONTS["family"]
        
        # Efecto de desenfoque reutilizable
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(15)
        self.blur_effect.setEnabled(False) # Inicialmente desactivado

        self.dependency_factory = DependencyFactory()
        
        self.main_menu_content = None
        self.current_search_results_window = None

        self._init_background()
        self._setup_main_menu()
        
        target_width, target_height = 1366, 768
        try:
            screen_geometry = QApplication.primaryScreen().geometry()
            self.setGeometry(int(screen_geometry.center().x() - target_width / 2), int(screen_geometry.center().y() - target_height / 2), target_width, target_height)
        except Exception:
            self.setGeometry(100, 100, target_width, target_height)
        if self.background_pixmap.isNull():
            print(f"ADVERTENCIA: No se pudo cargar la imagen de fondo: {BACKGROUND_IMAGE_PATH}")
            self.main_menu_widget = QWidget()
            self.setCentralWidget(self.main_menu_widget)
            self.root_layout_main_menu = QVBoxLayout(self.main_menu_widget)
            self.root_layout_main_menu.setContentsMargins(20, 70, 20, 20)
            self.root_layout_main_menu.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.title_label = QLabel("BookOS")
            self.title_label.setFont(QFont(self.font_family, FONTS.get("size_xlarge", 20), QFont.Weight.Bold))
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_label.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; }")
            self.root_layout_main_menu.addWidget(self.title_label)
            self.root_layout_main_menu.addSpacerItem(QSpacerItem(0, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
            self.main_menu_content = MenuSectionWidget()
            self.main_menu_content.action_triggered.connect(self._handle_menu_action)
            self.main_menu_content.search_requested.connect(self._iniciar_busqueda_desde_componente)
            self.root_layout_main_menu.addWidget(self.main_menu_content)
            self.root_layout_main_menu.addStretch(1)
            self.main_menu_widget.setStyleSheet("QWidget { background-color: #D32F2F; }")
            self.main_menu_widget.setGraphicsEffect(self.blur_effect)
        else:
            self.main_menu_widget = QWidget()
            self.setCentralWidget(self.main_menu_widget)
            self.root_layout_main_menu = QVBoxLayout(self.main_menu_widget)
            self.root_layout_main_menu.setContentsMargins(20, 70, 20, 20)
            self.root_layout_main_menu.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.title_label = QLabel("BookOS")
            self.title_label.setFont(QFont(self.font_family, FONTS.get("size_xlarge", 20), QFont.Weight.Bold))
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_label.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; }")
            self.root_layout_main_menu.addWidget(self.title_label)
            self.root_layout_main_menu.addSpacerItem(QSpacerItem(0, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
            self.main_menu_content = MenuSectionWidget()
            self.main_menu_content.action_triggered.connect(self._handle_menu_action)
            self.main_menu_content.search_requested.connect(self._iniciar_busqueda_desde_componente)
            self.root_layout_main_menu.addWidget(self.main_menu_content)
            self.root_layout_main_menu.addStretch(1)
            self.main_menu_widget.setStyleSheet("QWidget { background: transparent; }")
            self.main_menu_widget.setGraphicsEffect(self.blur_effect)

        self._initialize_services()
        self._center_window()

    def _initialize_services(self):
        self.book_service = self.dependency_factory.get_book_service()
        self.data_manager = self.dependency_factory.get_data_manager()
        self.book_info_service = self.dependency_factory.get_book_info_service()
        self.reservation_service = self.dependency_factory.get_reservation_service()
        self.sell_service = self.dependency_factory.get_sell_service()
        self.return_service = self.dependency_factory.get_return_service()
        self.delete_service = self.dependency_factory.get_delete_service()
        self.egreso_service = self.dependency_factory.get_egreso_service()
        self.finance_service = self.dependency_factory.get_finance_service()

        if self.current_search_results_window is None:
            self.current_search_results_window = SearchResultsWindow(
                [], "", parent=self
            )
            self.current_search_results_window.finished.connect(self.main_menu_content.show)
            self.current_search_results_window.finished.connect(self.title_label.show)
        
    def _iniciar_busqueda_desde_componente(self, termino_busqueda: str, filtros: dict):
        if not termino_busqueda: return

        libros_encontrados = self.book_service.buscar_libros_por_termino(termino_busqueda, filtros)
        
        if self.current_search_results_window is None:
            self.current_search_results_window = SearchResultsWindow(
                libros_encontrados, 
                termino_busqueda, 
                parent=self
            )
            self.current_search_results_window.finished.connect(self.main_menu_content.show)
            self.current_search_results_window.finished.connect(self.title_label.show)
        else:
            self.current_search_results_window.update_results(libros_encontrados, termino_busqueda)

        self.main_menu_content.hide()
        self.title_label.hide()
        self.current_search_results_window.show()

    def paintEvent(self, event):
        """Pinta la imagen de fondo, asegurando que cubra toda la ventana y mantenga la relación de aspecto."""
        if self.background_pixmap.isNull():
            super().paintEvent(event)
            return
            
        painter = QPainter(self)
        
        # Escalar la imagen para que cubra el widget manteniendo la relación de aspecto (similar a background-size: cover)
        scaled_pixmap = self.background_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        
        # Centrar la imagen escalada
        x = (self.width() - scaled_pixmap.width()) / 2
        y = (self.height() - scaled_pixmap.height()) / 2
        
        painter.drawPixmap(x, y, scaled_pixmap)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.current_search_results_window and self.current_search_results_window.isVisible():
                self.current_search_results_window.close()
            elif self.current_dialog and self.current_dialog.isVisible():
                self.current_dialog.close()
        super().keyPressEvent(event)

    def _open_dialog(self, dialog_class, *args):
        if self.current_dialog is not None:
            return  # Evita abrir un diálogo si ya hay uno abierto

        self.current_dialog = dialog_class(*args, parent=self)
        self.current_dialog.finished.connect(self._on_dialog_finished)
        
        self.main_menu_content.hide()
        self.title_label.hide()
        self.current_dialog.show()

    def _handle_menu_action(self, accion: str):
        accion_limpia = accion.strip()

        dialog_map = {
            "Agregar Libro": (AddBookDialog, self.book_service),
            "Modificar Libro": (ModifyBookDialog, self.book_service),
            "Eliminar Libro": (DeleteBookDialog, self.delete_service),
            "Vender Libro": (SellBookDialog, self.book_service, self.sell_service),
            "Devoluciones": (ReturnDialog, self.return_service),
            "Reportar Gasto": (EgresoDialog, self.egreso_service),
            "Apartar / Ver": (ReservationOptionsDialog,),
            "Modificar Finanzas": (ModifyFinancesDialog, self.finance_service),
        }

        if accion_limpia in dialog_map:
            dialog_class, *services = dialog_map[accion_limpia]
            
            if dialog_class == ReservationOptionsDialog:
                 self._open_reservation_options() # Usar el método especial para este caso
            else:
                self._open_dialog(dialog_class, *services)
        
    def _open_reservation_options(self):
        if self.current_dialog is not None:
            return
            
        dialog = ReservationOptionsDialog(self)
        self.current_dialog = dialog

        # Conectar señales para que este diálogo pueda abrir otros
        dialog.new_reservation_requested.connect(
            lambda: self._switch_dialog(ReservationDialog, self.reservation_service)
        )
        dialog.view_reservations_requested.connect(
            lambda: self._switch_dialog(ExistingReservationsDialog, self.reservation_service)
        )
        dialog.finished.connect(self._on_dialog_finished)

        self.main_menu_content.hide()
        self.title_label.hide()
        dialog.show()
    
    def _switch_dialog(self, next_dialog_class, *args):
        """Cierra el diálogo actual y abre uno nuevo."""
        if self.current_dialog:
            # Desconectar la señal de 'finished' para evitar doble llamada a _on_dialog_finished
            self.current_dialog.finished.disconnect(self._on_dialog_finished)
            self.current_dialog.close() # Cerrar el diálogo de opciones
            self.current_dialog = None # Limpiar referencia

        # Abrir el nuevo diálogo
        self._open_dialog(next_dialog_class, *args)

    def _on_dialog_finished(self):
        self.main_menu_content.show()
        self.title_label.show()
        if self.current_dialog:
             # Nos aseguramos de que el diálogo que se acaba de cerrar no vuelva a llamar a esto
            try:
                self.current_dialog.finished.disconnect(self._on_dialog_finished)
            except (TypeError, RuntimeError):
                pass # La señal ya podría estar desconectada
        self.current_dialog = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update() # Forzar un repintado en cada redimensión

    def show_search_bar(self):
        """Muestra la barra de búsqueda."""
        # Implementa la lógica para mostrar la barra de búsqueda
        pass

    def _init_background(self):
        """Carga y prepara la imagen de fondo."""
        image_path = os.path.join(os.path.dirname(__file__), "..", "app", "imagenes", "fondo.png")
        if os.path.exists(image_path):
            self.background_pixmap.load(image_path)
        else:
            print(f"Error: No se pudo encontrar la imagen de fondo en {image_path}")
            self.background_pixmap = QPixmap() # Crea un pixmap vacío si no se encuentra

    def _setup_main_menu(self):
        # Implementa la lógica para configurar el menú principal
        self.main_menu_widget = QWidget()
        self.setCentralWidget(self.main_menu_widget)
        
        layout_principal = QVBoxLayout(self.main_menu_widget)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        
        self.main_menu_content = MenuSectionWidget()
        self.main_menu_content.action_triggered.connect(self._handle_menu_action)
        self.main_menu_content.search_requested.connect(self._iniciar_busqueda_desde_componente)

        layout_principal.addWidget(self.main_menu_content)

    def _center_window(self):
        # Implementa la lógica para centrar la ventana en la pantalla
        pass