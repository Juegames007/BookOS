import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal
from typing import List, Dict, Optional

from .main_menu_card import MainMenuCard
from .search_bar_widget import SearchBarWidget
from gui.common.styles import FONTS

class MenuSectionWidget(QWidget):
    action_triggered = Signal(str)
    search_requested = Signal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.font_family = FONTS.get("family", "Arial")
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("QWidget { background: transparent; }")
        
        layout_overall_content = QVBoxLayout(self)
        layout_overall_content.setContentsMargins(0, 0, 0, 0)
        layout_overall_content.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        cards_holder_widget = QWidget()
        cards_holder_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_cards_holder = QHBoxLayout(cards_holder_widget)
        layout_cards_holder.setContentsMargins(0, 0, 0, 0)
        layout_cards_holder.setSpacing(15)
        layout_cards_holder.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        layout_cards_holder.addStretch(1)

        card_width = 275  # Manteniendo el ancho de tarjeta que establecimos
        main_card_3_btn_height = 280
        main_card_2_btn_height = 220
        extra_card_height = 150 # Altura para las tarjetas secundarias

        card_spacing = 15

        # --- Columna para Inventario ---
        inventario_columna_widget = QWidget()
        inventario_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_inventario_columna = QVBoxLayout(inventario_columna_widget)
        layout_inventario_columna.setContentsMargins(0,0,0,0)
        layout_inventario_columna.setSpacing(card_spacing)

        opciones_inventario_main = [
            {"icon": "agregar.png", "text": "  Agregar", "action": "Agregar Libro"},
            {"icon": "eliminar.png", "text": "  Eliminar Libro", "action": "Eliminar Libro"},
        ]
        inventario_card_principal = MainMenuCard(opciones_inventario_main, card_width, main_card_2_btn_height, "Inventario")
        inventario_card_principal.action_triggered.connect(self.action_triggered.emit)
        layout_inventario_columna.addWidget(inventario_card_principal)
        
        opciones_inventario_extra = [
            {"icon": "apartar.png", "text": "  Reservas", "action": "Apartar / Ver"},
            {"icon": "devoluciones.png", "text": "  Devolución", "action": "Registrar Devolucion"},
        ]
        inventario_card_extra = MainMenuCard(opciones_inventario_extra, card_width, extra_card_height)
        inventario_card_extra.action_triggered.connect(self.action_triggered.emit)
        layout_inventario_columna.addWidget(inventario_card_extra)

        layout_inventario_columna.addStretch(1)
        layout_cards_holder.addWidget(inventario_columna_widget)

        # --- Columna para Finanzas ---
        finanzas_columna_widget = QWidget()
        finanzas_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_finanzas_columna = QVBoxLayout(finanzas_columna_widget)
        layout_finanzas_columna.setContentsMargins(0,0,0,0)
        layout_finanzas_columna.setSpacing(card_spacing)

        self.search_bar = SearchBarWidget()
        self.search_bar.setFixedWidth(card_width)
        self.search_bar.search_requested.connect(self.search_requested.emit)
        layout_finanzas_columna.addWidget(self.search_bar)

        opciones_finanzas_main = [
            {"icon": "vender.png", "text": "  Vender", "action": "Vender Libro"},
            {"icon": "gasto.png", "text": "  Egreso", "action": "Reportar Gasto"},
            {"icon": "estadisticas.png", "text": "  Estadísticas", "action": "Ver Estadisticas"},
        ]
        finanzas_card_principal = MainMenuCard(opciones_finanzas_main, card_width, main_card_3_btn_height, "Finanzas")
        finanzas_card_principal.action_triggered.connect(self.action_triggered.emit)
        layout_finanzas_columna.addWidget(finanzas_card_principal)

        layout_finanzas_columna.addStretch(1)
        layout_cards_holder.addWidget(finanzas_columna_widget)

        # --- Columna para Ajustes ---
        ajustes_columna_widget = QWidget()
        ajustes_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_ajustes_columna = QVBoxLayout(ajustes_columna_widget)
        layout_ajustes_columna.setContentsMargins(0,0,0,0)
        layout_ajustes_columna.setSpacing(card_spacing)

        opciones_ajustes_main = [
            {"icon": "modificar.png", "text": "  Mod. Inventario", "action": "Modificar Libro"},
            {"icon": "ajustes_finanzas.png", "text": "  Mod. Finanzas", "action": "Modificar Finanzas"},
        ]
        ajustes_card_principal = MainMenuCard(opciones_ajustes_main, card_width, main_card_2_btn_height, "Ajustes")
        ajustes_card_principal.action_triggered.connect(self.action_triggered.emit)
        layout_ajustes_columna.addWidget(ajustes_card_principal)
        
        opciones_ajustes_extra = [
            {"icon": "configuracion.png", "text": "  Configuración", "action": "Abrir Configuracion"},
            {"icon": "salir.png", "text": "  Salir", "action": "SALIR_APP"}
        ]
        ajustes_card_extra = MainMenuCard(opciones_ajustes_extra, card_width, extra_card_height)
        ajustes_card_extra.action_triggered.connect(self.action_triggered.emit)
        layout_ajustes_columna.addWidget(ajustes_card_extra)

        layout_ajustes_columna.addStretch(1)
        layout_cards_holder.addWidget(ajustes_columna_widget)

        layout_cards_holder.addStretch(1)

        layout_overall_content.addWidget(cards_holder_widget)
        layout_overall_content.addStretch(1)

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication([])

    if 'FONTS' not in globals(): FONTS = {"family": "Arial", "size_xlarge":24, "size_large":16, "size_medium":12, "size_small":10}

    test_main_window = QMainWindow()
    menu_sections = MenuSectionWidget()

    def handle_menu_action(action_name):
        print(f"MenuSectionWidget emitió action_triggered: {action_name}")
        if action_name == "SALIR_APP":
            app.quit()

    def handle_menu_search(term, filters):
        print(f"MenuSectionWidget emitió search_requested: Término='{term}', Filtros={filters}")

    menu_sections.action_triggered.connect(handle_menu_action)
    menu_sections.search_requested.connect(handle_menu_search)
    
    # Añadir un título y espaciadores si se desea probar cómo se ve en un layout similar a main_window
    test_root_layout = QVBoxLayout()
    title_label = QLabel("Gestión Librería (Prueba MenuSectionWidget)")
    title_font = QFont(FONTS.get("family", "Arial"), FONTS.get("size_xlarge", 24), QFont.Weight.Bold)
    title_label.setFont(title_font)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; }")
    test_root_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
    test_root_layout.addWidget(title_label)
    test_root_layout.addSpacerItem(QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
    test_root_layout.addWidget(menu_sections)
    test_root_layout.addStretch(1)

    container_widget = QWidget()
    container_widget.setLayout(test_root_layout)
    test_main_window.setCentralWidget(container_widget)
    test_main_window.resize(1024, 768)
    test_main_window.show()
    
    app.exec() 