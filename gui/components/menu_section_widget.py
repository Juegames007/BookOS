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
        main_card_height = 280
        extra_card_height = 160 
        # Nueva altura para la tarjeta de estadísticas, puede ser similar a extra_card_height
        # o ajustarse según el número de botones. Con 2 botones, podría ser más pequeña.
        stats_card_height = 140 # Estimación para 2 botones, ajustar si es necesario

        card_spacing = 15

        # --- Columna para Inventario ---
        inventario_columna_widget = QWidget()
        inventario_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_inventario_columna = QVBoxLayout(inventario_columna_widget)
        layout_inventario_columna.setContentsMargins(0,0,0,0)
        layout_inventario_columna.setSpacing(card_spacing)

        opciones_inventario_main = [
            {"icon": "agregar.png", "text": "  Agregar Libro", "action": "Agregar Libro"},
            {"icon": "apartar.png", "text": "  Apartar / Ver", "action": "Apartar / Ver"},
            {"icon": "modificar.png", "text": "  Modificar Libro", "action": "Modificar Libro"}
        ]
        inventario_card_principal = MainMenuCard(opciones_inventario_main, card_width, main_card_height, "Inventario")
        inventario_card_principal.action_triggered.connect(self.action_triggered.emit)
        layout_inventario_columna.addWidget(inventario_card_principal)
        
        # Tarjeta de relleno para inventario para alinear alturas si otras columnas crecen
        inventario_card_relleno = MainMenuCard([], card_width, 
                                               extra_card_height + card_spacing + stats_card_height) # Ajustar altura de relleno
        inventario_card_relleno.setVisible(False) 
        layout_inventario_columna.addWidget(inventario_card_relleno)
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
            {"icon": "vender.png", "text": "  Vender Libro", "action": "Vender Libro"},
            {"icon": "ingreso.png", "text": "  Anotar Ingreso", "action": "Reportar Ingreso"},
            {"icon": "gasto.png", "text": "  Anotar Gasto", "action": "Reportar Gasto"},
        ]
        # Ajustar altura de la tarjeta principal de finanzas si es necesario
        # Por ahora, la dejamos igual. Si se ve muy apretada, se puede reducir su contenido o altura.
        finanzas_card_principal = MainMenuCard(opciones_finanzas_main, card_width, main_card_height, "Finanzas")
        finanzas_card_principal.action_triggered.connect(self.action_triggered.emit)
        layout_finanzas_columna.addWidget(finanzas_card_principal)

        # Tarjeta extra original de finanzas
        opciones_finanzas_extra = [
            {"icon": "contabilidad.png", "text": "  Ver Finanzas", "action": "Ver Finanzas"}, # Asume que tienes un icono ver_finanzas.png
            {"icon": "pedidos.png", "text": "  Ver Pedidos", "action": "Ver Pedidos"}
        ]
        # Ajustar la altura de finanzas_card_extra si es necesario
        # La altura disponible para finanzas_card_extra ahora debe considerar la nueva tarjeta de estadísticas.
        # Por ahora, la dejamos con su cálculo original, podría necesitar ajuste manual o hacerse más pequeña.
        # altura_disponible_finanzas_extra = extra_card_height 
        # (Esta línea no estaba, pero es para pensar la lógica)
        
        # Si finanzas_card_extra y stats_card van en el mismo espacio vertical que extra_card_height
        # de las otras columnas, hay que dividir esa altura.
        # O, si la columna de finanzas puede ser más alta, entonces no hay problema.
        # Asumamos que la columna de finanzas puede crecer.
        
        finanzas_card_extra = MainMenuCard(opciones_finanzas_extra, card_width, extra_card_height) # Sin título explícito, usará el espacio
        finanzas_card_extra.action_triggered.connect(self.action_triggered.emit)
        layout_finanzas_columna.addWidget(finanzas_card_extra)

        layout_finanzas_columna.addStretch(1)
        layout_cards_holder.addWidget(finanzas_columna_widget)

        # --- Columna para Ajustes ---
        ajustes_columna_widget = QWidget()
        ajustes_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_ajustes_columna = QVBoxLayout(ajustes_columna_widget)
        layout_ajustes_columna.setContentsMargins(0,0,0,0)
        layout_ajustes_columna.setSpacing(card_spacing)

        opciones_ajustes_main = [
            {"icon": "ajustes_finanzas.png", "text": "  Mod. Finanzas", "action": "Modificar Finanzas"},
            {"icon": "eliminar.png", "text": "  Eliminar Libro", "action": "Eliminar Libro"},
            {"icon": "salir.png", "text": "  Salir", "action": "SALIR_APP"}
        ]
        ajustes_card_principal = MainMenuCard(opciones_ajustes_main, card_width, main_card_height, "Ajustes")
        ajustes_card_principal.action_triggered.connect(self.action_triggered.emit)
        layout_ajustes_columna.addWidget(ajustes_card_principal)
        
        # Tarjeta de relleno para ajustes para alinear alturas
        # Debe ser igual a la altura de relleno de inventario para mantener la simetría
        ajustes_card_relleno = MainMenuCard([], card_width, 
                                            extra_card_height + card_spacing + stats_card_height) # Ajustar altura de relleno
        ajustes_card_relleno.setVisible(False)
        layout_ajustes_columna.addWidget(ajustes_card_relleno)
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