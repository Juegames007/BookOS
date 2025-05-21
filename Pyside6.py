import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtGui import (
    QPixmap, QPalette, QBrush, QFont, QColor, QIcon, QScreen, QPainter
)
from PySide6.QtCore import Qt, QSize, QRect, QPoint

# --- Configuración de Rutas ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "imagenes")
BACKGROUND_IMAGE_PATH = os.path.join(IMAGE_DIR, "fondo.png")

# --- Función para Acciones Pendientes ---
def accion_pendiente(nombre_accion, parent_window=None):
    QMessageBox.information(parent_window, "Acción Pendiente",
                            f"La funcionalidad '{nombre_accion}' está pendiente de implementación.")

# --- Clase Principal de la Ventana ---
class VentanaGestionLibreria(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión Librería con PySide6")
        self.font_family = "San Francisco" # Fuente deseada

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

        self.background_pixmap = QPixmap(BACKGROUND_IMAGE_PATH)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal para el widget central (este contendrá el overall_content_widget y lo centrará)
        self.root_layout = QVBoxLayout(self.central_widget) # Renombrado para claridad
        self.root_layout.setContentsMargins(20, 20, 20, 20) # Márgenes generales de la ventana

        if self.background_pixmap.isNull():
            print(f"ADVERTENCIA MUY IMPORTANTE: No se pudo cargar la imagen de fondo desde: {BACKGROUND_IMAGE_PATH}")
            self.central_widget.setStyleSheet("QWidget { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #D32F2F, stop:1 #FF5252); }")
            error_label = QLabel(f"Error: No se pudo cargar '{BACKGROUND_IMAGE_PATH}'.\nVerifica la ruta y el archivo.", self.central_widget)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("QLabel { color: white; font-size: 18px; background-color: transparent; }")
            self.root_layout.addWidget(error_label, stretch=1)
        else:
            self.central_widget.setStyleSheet("QWidget { background: transparent; }")
            self._setup_ui_normal()

    def _setup_ui_normal(self):
        # --- Widget Contenedor General (para título y tarjetas) ---
        # Este widget se centrará en la ventana.
        overall_content_widget = QWidget()
        # overall_content_widget.setStyleSheet("background-color: rgba(0,255,0,20);") # Para depurar su posición
        
        layout_overall_content = QVBoxLayout(overall_content_widget)
        layout_overall_content.setContentsMargins(0, 0, 0, 0) # Sin márgenes internos, controlamos con espaciadores
        layout_overall_content.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop) # Contenido alineado arriba y centrado horizontalmente

        # 1. Espaciador superior para el título (para bajarlo "un poquitito")
        # Ajusta el valor '15' si necesitas más o menos espacio.
        layout_overall_content.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # 2. Título Principal "Gestión Librería"
        title_label = QLabel("Gestión Librería")
        title_font = QFont(self.font_family, 30, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; }")
        layout_overall_content.addWidget(title_label)

        # 3. Espaciador entre el título y el contenedor de las tarjetas
        layout_overall_content.addSpacerItem(QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # 4. Contenedor para las dos tarjetas (Inventario y Finanzas)
        cards_holder_widget = QWidget()
        cards_holder_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_cards_holder = QHBoxLayout(cards_holder_widget)
        layout_cards_holder.setContentsMargins(0,0,0,0) # Sin márgenes propios
        layout_cards_holder.setSpacing(25) # Espacio entre las tarjetas (Inventario y Finanzas)
        layout_cards_holder.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centra las tarjetas si hay espacio extra horizontal

        card_width = 300
        card_height = 400

        opciones_inventario = [
            {"icon": "agregar.png", "text": "  Agregar Libro", "action": "Agregar Libro"},
            {"icon": "buscar.png", "text": "  Buscar Libro", "action": "Buscar Libro"},
            {"icon": "eliminar.png", "text": "  Eliminar Libro", "action": "Eliminar Libro"},
            {"icon": "modificar.png", "text": "  Modificar Libro", "action": "Modificar Libro"}
        ]
        inventario_card = self._crear_tarjeta("Inventario", opciones_inventario, card_width, card_height)
        layout_cards_holder.addWidget(inventario_card)

        opciones_finanzas = [
            {"icon": "ingreso.png", "text": "  Reportar Ingreso", "action": "Reportar Ingreso"},
            {"icon": "gasto.png", "text": "  Reportar Gasto", "action": "Reportar Gasto"},
            {"icon": "contabilidad.png", "text": "  Generar Contabilidad", "action": "Generar Contabilidad"},
            {"icon": "pedidos.png", "text": "  Generar Pedidos", "action": "Generar Pedidos"}
        ]
        finanzas_card = self._crear_tarjeta("Finanzas", opciones_finanzas, card_width, card_height)
        layout_cards_holder.addWidget(finanzas_card)
        
        layout_overall_content.addWidget(cards_holder_widget) # Añade el contenedor de tarjetas al layout general

        # Añadir un espaciador expandible al final del layout_overall_content
        # Esto asegura que el contenido (título y tarjetas) se mantenga agrupado en la parte superior
        # de overall_content_widget si este widget fuera más alto que su contenido.
        layout_overall_content.addStretch(1)

        # --- Añadir el overall_content_widget al root_layout (centrado) ---
        self.root_layout.addStretch(1) # Espaciador flexible arriba
        self.root_layout.addWidget(overall_content_widget, 0, Qt.AlignmentFlag.AlignHCenter) # Centrado horizontalmente
        self.root_layout.addStretch(1) # Espaciador flexible abajo
        # Estos dos QSpacerItem con stretch=1 en el root_layout centrarán verticalmente el overall_content_widget.

    def _crear_tarjeta(self, titulo_str, opciones_data, ancho, alto):
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
        layout_tarjeta.setContentsMargins(30, 30, 30, 30)
        layout_tarjeta.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_tarjeta.setSpacing(15)

        titulo_seccion = QLabel(titulo_str)
        font_titulo_seccion = QFont(self.font_family, 16, QFont.Weight.Bold)
        titulo_seccion.setFont(font_titulo_seccion)
        titulo_seccion.setAlignment(Qt.AlignmentFlag.AlignLeft)
        titulo_seccion.setStyleSheet("""
            QLabel {
                color: black;
                background-color: transparent;
                padding-bottom: 10px;
                border: none; /* Añade esta línea para asegurar que no haya borde */
            }
        """)
        layout_tarjeta.addWidget(titulo_seccion)

        font_botones = QFont(self.font_family, 11)
        button_height = 50
        icon_size = QSize(24, 24)

        for item_data in opciones_data:
            texto_visible_btn = item_data["text"]
            texto_accion = item_data["action"]
            nombre_archivo_icono = item_data["icon"]
            
            ruta_icono = os.path.join(IMAGE_DIR, nombre_archivo_icono)
            q_icon = QIcon(ruta_icono)
            
            boton = QPushButton(f"{texto_visible_btn}  >")
            if not q_icon.isNull():
                boton.setIcon(q_icon)
                boton.setIconSize(icon_size)
            else:
                print(f"Advertencia: No se pudo cargar el icono: {ruta_icono}")
            
            boton.setFont(font_botones)
            boton.setFixedHeight(button_height)
            boton.setStyleSheet("""
                QPushButton {
                    background-color: rgba(248, 249, 250, 100);
                    color: #202427;
                    border: 1px solid rgba(200, 200, 200, 80);
                    border-radius: 10px;
                    padding: 0px 10px 0px 5px; 
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: rgba(240, 245, 248, 120);
                    border: 1px solid rgba(190, 190, 190, 100);
                }
                QPushButton:pressed {
                    background-color: rgba(230, 238, 245, 140);
                }
            """)
            boton.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            boton.clicked.connect(lambda checked=False, accion=texto_accion: accion_pendiente(accion, self))
            layout_tarjeta.addWidget(boton)

        layout_tarjeta.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        return tarjeta

    def paintEvent(self, event):
        if not self.background_pixmap.isNull():
            painter = QPainter(self)
            scaled_pixmap = self.background_pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            point = QPoint(0,0)
            if scaled_pixmap.width() > self.width():
                point.setX(int((scaled_pixmap.width() - self.width()) / -2))
            if scaled_pixmap.height() > self.height():
                point.setY(int((scaled_pixmap.height() - self.height()) / -2))
            painter.drawPixmap(point, scaled_pixmap)
        super().paintEvent(event)

    def resizeEvent(self, event):
        self.update()
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaGestionLibreria()
    ventana.show()
    sys.exit(app.exec())