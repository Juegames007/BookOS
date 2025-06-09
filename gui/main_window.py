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
    QLineEdit, QInputDialog
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
from gui.components.menu_section_widget import MenuSectionWidget
from features.book_service import BookService
from features.reservation_service import ReservationService
from gui.dialogs.search_results_window import SearchResultsWindow

def accion_pendiente(nombre_accion, parent_window=None):
    """
    Muestra un mensaje de acción pendiente o ejecuta la acción correspondiente.
    """
    data_manager = DependencyFactory.get_data_manager()
    book_info_fetcher = DependencyFactory.get_book_info_service()
    actual_book_service = BookService(data_manager, book_info_fetcher)
    reservation_service = ReservationService(data_manager)
    
    accion_limpia = nombre_accion.strip()


    if accion_limpia == "Agregar Libro":
        dialog = AddBookDialog(actual_book_service, parent_window)
        dialog.exec()
        
    elif accion_limpia == "Modificar Libro":
        dialog = ModifyBookDialog(actual_book_service, parent=parent_window)
        dialog.exec()
    
    # --- INICIO DE LA MODIFICACIÓN ---
    elif accion_limpia == "Apartar / Ver":
        options_dialog = ReservationOptionsDialog(parent=parent_window)
        options_dialog.create_new_requested.connect(
            lambda: open_reservation_dialog(reservation_service, parent_window)
        )
        # Aquí conectarías la señal view_existing_requested a la futura ventana
        # options_dialog.view_existing_requested.connect(...)
        options_dialog.exec()
    # --- FIN DE LA MODIFICACIÓN ---

def open_reservation_dialog(reservation_service, parent_window):
    dialog = ReservationDialog(reservation_service, parent=parent_window)
    dialog.exec()

class VentanaGestionLibreria(QMainWindow):
    """
    Ventana principal de la aplicación de gestión de librería.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BookOS - Gestión de Librería")
        self.font_family = FONTS["family"]
        data_manager = DependencyFactory.get_data_manager()
        book_info_fetcher = DependencyFactory.get_book_info_service()
        self.book_service = BookService(data_manager, book_info_fetcher)
        target_width, target_height = 1366, 768
        try:
            screen_geometry = QApplication.primaryScreen().geometry()
            self.setGeometry(int(screen_geometry.center().x() - target_width / 2), int(screen_geometry.center().y() - target_height / 2), target_width, target_height)
        except Exception:
            self.setGeometry(100, 100, target_width, target_height)
        self.background_pixmap = QPixmap(BACKGROUND_IMAGE_PATH)
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
        if self.background_pixmap.isNull():
            print(f"ADVERTENCIA: No se pudo cargar la imagen de fondo: {BACKGROUND_IMAGE_PATH}")
            self.main_menu_widget.setStyleSheet("QWidget { background-color: #D32F2F; }")
        else:
            self.main_menu_widget.setStyleSheet("QWidget { background: transparent; }")
        self.current_search_results_window = None

    def _iniciar_busqueda_desde_componente(self, termino_busqueda: str, filtros: dict):
        if not termino_busqueda: return
        libros_encontrados = self.book_service.buscar_libros(termino_busqueda)
        if hasattr(self, 'current_search_results_window') and self.current_search_results_window:
            self.current_search_results_window.close()
        self.current_search_results_window = SearchResultsWindow(libros_encontrados, termino_busqueda, self)
        self.current_search_results_window.show()

    def paintEvent(self, event):
        if not self.background_pixmap.isNull():
            painter = QPainter(self)
            scaled_pixmap = self.background_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            point = QPoint(int((scaled_pixmap.width() - self.width()) / -2), int((scaled_pixmap.height() - self.height()) / -2))
            painter.drawPixmap(point, scaled_pixmap)
        super().paintEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if hasattr(self, 'current_search_results_window') and self.current_search_results_window and self.current_search_results_window.isVisible():
                self.current_search_results_window.close()
        super().keyPressEvent(event)

    def _handle_menu_action(self, accion: str):
        accion_pendiente(accion, self)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)