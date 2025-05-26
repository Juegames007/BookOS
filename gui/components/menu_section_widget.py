import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal
from typing import List, Dict, Optional

from .main_menu_card import MainMenuCard
from .search_bar_widget import SearchBarWidget # Para la barra de búsqueda en la sección de finanzas
from gui.common.styles import FONTS

class MenuSectionWidget(QWidget):
    action_triggered = Signal(str)  # Se re-emite desde las MainMenuCard
    # Señal para la búsqueda, emitida por la SearchBarWidget interna
    # Esta señal será conectada por la VentanaGestionLibreria al PaginatedResultsWidget
    search_requested = Signal(str, dict) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.font_family = FONTS.get("family", "Arial")
        self._setup_ui()

    def _setup_ui(self):
        # Este widget en sí mismo será transparente, el fondo lo maneja la ventana principal
        self.setStyleSheet("QWidget { background: transparent; }")
        
        layout_overall_content = QVBoxLayout(self)
        layout_overall_content.setContentsMargins(0, 0, 0, 0)
        layout_overall_content.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        # layout_overall_content.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Título General (opcional, podría estar en main_window)
        # title_label = QLabel("Gestión Librería")
        # title_font = QFont(self.font_family, FONTS.get("size_xlarge", 24), QFont.Weight.Bold)
        # title_label.setFont(title_font)
        # title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # title_label.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; }")
        # layout_overall_content.addWidget(title_label)
        # layout_overall_content.addSpacerItem(QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        cards_holder_widget = QWidget()
        cards_holder_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_cards_holder = QHBoxLayout(cards_holder_widget)
        layout_cards_holder.setContentsMargins(0, 0, 0, 0)
        layout_cards_holder.setSpacing(15)
        layout_cards_holder.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        layout_cards_holder.addStretch(1)

        card_width = 300
        main_card_height = 280
        extra_card_height = 160
        card_spacing = 15

        # --- Columna para Inventario ---
        inventario_columna_widget = QWidget()
        inventario_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_inventario_columna = QVBoxLayout(inventario_columna_widget)
        layout_inventario_columna.setContentsMargins(0,0,0,0)
        layout_inventario_columna.setSpacing(card_spacing)

        opciones_inventario_main = [
            {"icon": "agregar.png", "text": "  Agregar Libro", "action": "Agregar Libro"},
            {"icon": "buscar.png", "text": "  Buscar Libro", "action": "Buscar Libro"},
            {"icon": "modificar.png", "text": "  Modificar Libro", "action": "Modificar Libro"}
        ]
        inventario_card_principal = MainMenuCard(opciones_inventario_main, card_width, main_card_height, "Inventario")
        inventario_card_principal.action_triggered.connect(self.action_triggered.emit)
        layout_inventario_columna.addWidget(inventario_card_principal)
        
        inventario_card_relleno = MainMenuCard([], card_width, extra_card_height) # Tarjeta vacía para relleno
        inventario_card_relleno.setVisible(False) # Debe ser invisible
        layout_inventario_columna.addWidget(inventario_card_relleno)
        layout_inventario_columna.addStretch(1)
        layout_cards_holder.addWidget(inventario_columna_widget)

        # --- Columna para Finanzas ---
        finanzas_columna_widget = QWidget()
        finanzas_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_finanzas_columna = QVBoxLayout(finanzas_columna_widget)
        layout_finanzas_columna.setContentsMargins(0,0,0,0)
        layout_finanzas_columna.setSpacing(card_spacing)

        self.search_bar = SearchBarWidget() # Instanciar la barra de búsqueda
        self.search_bar.setFixedWidth(card_width)
        self.search_bar.search_requested.connect(self.search_requested.emit) # Re-emitir la señal
        layout_finanzas_columna.addWidget(self.search_bar)

        opciones_finanzas_main = [
            {"icon": "vender.png", "text": "  Vender Libro", "action": "Vender Libro"},
            {"icon": "ingreso.png", "text": "  Reportar Ingreso", "action": "Reportar Ingreso"},
            {"icon": "gasto.png", "text": "  Reportar Gasto", "action": "Reportar Gasto"},
        ]
        finanzas_card_principal = MainMenuCard(opciones_finanzas_main, card_width, main_card_height, "Finanzas") # Ajustar altura si es necesario
        finanzas_card_principal.action_triggered.connect(self.action_triggered.emit)
        layout_finanzas_columna.addWidget(finanzas_card_principal)

        opciones_finanzas_extra = [
            {"icon": "contabilidad.png", "text": "  Generar Contabilidad", "action": "Generar Contabilidad"},
            {"icon": "pedidos.png", "text": "  Generar Pedidos", "action": "Generar Pedidos"}
        ]
        # La altura de esta tarjeta extra podría necesitar ser ajustada para que coincida con la search_bar + card_spacing
        # o podemos asumir que las tarjetas de relleno ya no son necesarias si la search bar ocupa espacio.
        # Por ahora, mantenemos una tarjeta extra para estructura similar.
        finanzas_card_extra = MainMenuCard(opciones_finanzas_extra, card_width, extra_card_height - self.search_bar.sizeHint().height() - card_spacing if extra_card_height > self.search_bar.sizeHint().height() + card_spacing else 50)
        finanzas_card_extra.action_triggered.connect(self.action_triggered.emit)
        # layout_finanzas_columna.addWidget(finanzas_card_extra) # Decidir si esta tarjeta extra es necesaria
        layout_finanzas_columna.addStretch(1)
        layout_cards_holder.addWidget(finanzas_columna_widget)

        # --- Columna para Ajustes ---
        ajustes_columna_widget = QWidget()
        ajustes_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_ajustes_columna = QVBoxLayout(ajustes_columna_widget)
        layout_ajustes_columna.setContentsMargins(0,0,0,0)
        layout_ajustes_columna.setSpacing(card_spacing)

        opciones_ajustes_main = [
            {"icon": "ajustes_finanzas.png", "text": "  Modificar Finanzas", "action": "Modificar Finanzas"},
            {"icon": "eliminar.png", "text": "  Eliminar Libro", "action": "Eliminar Libro"},
            {"icon": "salir.png", "text": "  Salir", "action": "SALIR_APP"}
        ]
        ajustes_card_principal = MainMenuCard(opciones_ajustes_main, card_width, main_card_height, "Ajustes")
        ajustes_card_principal.action_triggered.connect(self.action_triggered.emit)
        layout_ajustes_columna.addWidget(ajustes_card_principal)
        
        ajustes_card_relleno = MainMenuCard([], card_width, extra_card_height)
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