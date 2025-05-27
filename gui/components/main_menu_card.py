import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, Signal
from typing import List, Dict, Optional

from gui.common.widgets import CustomButton
from gui.common.styles import FONTS, STYLES

class MainMenuCard(QFrame):
    action_triggered = Signal(str)  # Emite el 'action' string del botón presionado

    def __init__(self, 
                 opciones_data: List[Dict[str, str]], 
                 card_width: int, 
                 card_height: int, 
                 titulo_str: Optional[str] = None, 
                 parent=None):
        super().__init__(parent)
        self.font_family = FONTS.get("family", "Arial")
        self.setObjectName("mainMenuCard") # Importante para que el estilo aplique específicamente
        self._setup_ui(titulo_str, opciones_data, card_width, card_height)
        self._apply_shadow_effect()

    def _setup_ui(self, titulo_str: Optional[str], opciones_data: List[Dict[str, str]], ancho: int, alto: int):
        self.setFixedSize(ancho, alto)
        self.setStyleSheet(STYLES.get("main_menu_card_style", ""))
        layout_tarjeta = QVBoxLayout(self)

        top_margin = 15
        if titulo_str:
            top_margin = 30
        elif not opciones_data: # Tarjeta de relleno invisible, sin título ni opciones
            top_margin = 0

        layout_tarjeta.setContentsMargins(30, top_margin, 30, 30)
        layout_tarjeta.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_tarjeta.setSpacing(10)

        if titulo_str:
            titulo_seccion = QLabel(titulo_str)
            font_titulo_seccion = QFont(self.font_family, FONTS.get("size_large", 16), QFont.Weight.Bold)
            titulo_seccion.setFont(font_titulo_seccion)
            titulo_seccion.setAlignment(Qt.AlignmentFlag.AlignLeft)
            titulo_seccion.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; border: none; }")
            layout_tarjeta.addWidget(titulo_seccion)

        for item_data in opciones_data:
            texto_visible_original = item_data.get("text", "")
            nombre_archivo_icono = item_data.get("icon", "")
            accion_definida = item_data.get("action", "")

            # Construcción robusta de la ruta del icono
            try:
                current_script_dir = os.path.dirname(os.path.abspath(__file__))
                # Asumiendo que 'gui' es un subdirectorio de la raíz del proyecto donde está 'app'
                project_root_dir = os.path.dirname(current_script_dir) # Sube un nivel a 'gui'
                app_dir = os.path.join(os.path.dirname(project_root_dir), "app") # Sube otro nivel a la raíz y luego a 'app'
                ruta_icono_completa = os.path.join(app_dir, "imagenes", nombre_archivo_icono)
            except Exception:
                ruta_icono_completa = os.path.join("app", "imagenes", nombre_archivo_icono) # Fallback
            
            if not os.path.exists(ruta_icono_completa):
                 print(f"Advertencia: Icono no encontrado en {ruta_icono_completa} para acción '{accion_definida}'")
                 # Considerar usar un icono de placeholder o no poner icono
                 ruta_icono_completa = None # No pasar ruta si no existe

            boton_personalizado = CustomButton(icon_path=ruta_icono_completa, text=texto_visible_original.strip())
            
            # Usar una función lambda que capture el valor actual de accion_definida
            boton_personalizado.clicked.connect(lambda checked=False, accion=accion_definida: self.action_triggered.emit(accion))
            layout_tarjeta.addWidget(boton_personalizado)

        layout_tarjeta.addStretch(1)

    def _apply_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(100) # Actualizado el BlurRadius a 10
        # El color de la sombra: rgba( 31, 38, 135, 0.37 )
        # Qt espera un valor alfa de 0-255, así que 0.37 * 255 ~= 94
        shadow.setColor(QColor(31, 38, 135, 94))
        # Desplazamiento: 0 8px
        shadow.setOffset(0, 8) # (dx, dy)
        self.setGraphicsEffect(shadow)

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication([])

    if 'FONTS' not in globals():
        FONTS = {"family": "Arial", "size_large": 16}

    opciones_test = [
        {"icon": "agregar.png", "text": "  Agregar Algo", "action": "ADD_SOMETHING"},
        {"icon": "buscar.png", "text": "  Buscar Algo", "action": "SEARCH_SOMETHING"},
    ]

    test_window = QMainWindow()
    main_widget = QWidget()
    test_layout = QHBoxLayout(main_widget)
    test_window.setCentralWidget(main_widget)

    card1 = MainMenuCard(titulo_str="Mi Tarjeta 1", opciones_data=opciones_test, card_width=300, card_height=280)
    card2 = MainMenuCard(opciones_data=opciones_test, card_width=300, card_height=160) # Sin título

    def handle_action(accion):
        print(f"Acción recibida desde la tarjeta: {accion}")

    card1.action_triggered.connect(handle_action)
    card2.action_triggered.connect(handle_action)

    test_layout.addWidget(card1)
    test_layout.addWidget(card2)
    
    test_window.resize(700, 400)
    test_window.setWindowTitle("Prueba de MainMenuCard")
    test_window.show()
    app.exec()
