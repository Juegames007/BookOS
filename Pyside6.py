import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtGui import (
    QPixmap, QPalette, QBrush, QFont, QColor, QIcon, QScreen, QPainter, QCursor
)
from PySide6.QtCore import Qt, QSize, QRect, QPoint, Signal # Importar Signal

# --- Configuración de Rutas ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "imagenes")
BACKGROUND_IMAGE_PATH = os.path.join(IMAGE_DIR, "fondo.png")

# --- Función para Acciones Pendientes ---
def accion_pendiente(nombre_accion, parent_window=None):
    QMessageBox.information(parent_window, "Acción Pendiente",
                            f"La funcionalidad '{nombre_accion}' está pendiente de implementación.")

# --- Clase para el Botón Personalizado ---
class CustomButton(QFrame):
    clicked = Signal() # Señal que se emitirá al hacer clic

    def __init__(self, icon_path=None, text="", parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(50) # Altura fija como los QPushButton anteriores

        # --- Estilo Base y Estados ---
        self.font_family = "San Francisco" # Heredar o definir aquí
        self.text_color = "#202427"
        self.icon_size = QSize(24, 24)

        self.style_normal = f"""
            QFrame {{
                background-color: rgba(248, 249, 250, 100); /* Alfa 100 */
                border: 1px solid rgba(200, 200, 200, 80);
                border-radius: 10px;
            }}
            QLabel {{ /* Estilo para las etiquetas dentro de este QFrame */
                color: {self.text_color};
                background-color: transparent;
                border: none;
                padding: 0px;
            }}
        """
        self.style_hover = f"""
            QFrame {{
                background-color: rgba(240, 245, 248, 120); /* Alfa 120 */
                border: 1px solid rgba(190, 190, 190, 100);
                border-radius: 10px;
            }}
            QLabel {{ color: {self.text_color}; background-color: transparent; border:none; padding: 0px; }}
        """
        self.style_pressed = f"""
            QFrame {{
                background-color: rgba(230, 238, 245, 140); /* Alfa 140 */
                border: 1px solid rgba(180, 180, 180, 120);
                border-radius: 10px;
            }}
            QLabel {{ color: {self.text_color}; background-color: transparent; border:none; padding: 0px; }}
        """
        self.setStyleSheet(self.style_normal)

        # --- Layout Interno ---
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0) # Padding Izq/Der para el contenido total
        layout.setSpacing(8) # Espacio entre icono y texto

        # Icono (QLabel)
        self.icon_label = QLabel()
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(self.icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            if icon_path: # Si se proveyó ruta pero no existe
                 print(f"Advertencia: No se pudo cargar el icono para CustomButton: {icon_path}")
            self.icon_label.setFixedSize(0,0) # Ocultar si no hay icono
            layout.setSpacing(0) # Sin espaciado si no hay icono


        # Texto Principal (QLabel)
        self.text_label = QLabel(text)
        font_botones = QFont(self.font_family, 11) # Tamaño de fuente como en tu último script
        self.text_label.setFont(font_botones)

        # Flecha (QLabel)
        self.arrow_label = QLabel(">")
        self.arrow_label.setFont(font_botones) # Misma fuente que el texto
        self.arrow_label.setFixedWidth(self.arrow_label.fontMetrics().horizontalAdvance("> ") + 5) # Ancho para la flecha

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addStretch(1) # Espacio expandible que empuja la flecha a la derecha
        layout.addWidget(self.arrow_label)

    # --- Eventos para simular botón ---
    def enterEvent(self, event):
        self.setStyleSheet(self.style_hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.style_normal)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setStyleSheet(self.style_pressed)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Solo emitir click si se soltó dentro del widget
            if self.rect().contains(event.position().toPoint()):
                self.setStyleSheet(self.style_hover) # Vuelve a hover si el mouse sigue encima
                self.clicked.emit()
            else:
                self.setStyleSheet(self.style_normal) # Vuelve a normal si el mouse se fue
        super().mouseReleaseEvent(event)


# --- Clase Principal de la Ventana (QMainWindow) ---
class VentanaGestionLibreria(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión Librería con PySide6")
        self.font_family = "San Francisco"

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
        self.root_layout = QVBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(20, 20, 20, 20)

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
        overall_content_widget = QWidget()
        layout_overall_content = QVBoxLayout(overall_content_widget)
        layout_overall_content.setContentsMargins(0, 0, 0, 0)
        layout_overall_content.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        layout_overall_content.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        title_label = QLabel("Gestión Librería")
        title_font = QFont(self.font_family, 30, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; }")
        layout_overall_content.addWidget(title_label)
        layout_overall_content.addSpacerItem(QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        cards_holder_widget = QWidget()
        cards_holder_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_cards_holder = QHBoxLayout(cards_holder_widget)
        layout_cards_holder.setContentsMargins(0,0,0,0)
        layout_cards_holder.setSpacing(25)
        layout_cards_holder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_width = 300 # Ancho de tarjeta de tu script
        card_height = 400 # Alto de tarjeta de tu script

        opciones_inventario = [
            {"icon": "agregar.png", "text": "  Agregar Libro", "action": "Agregar Libro"},
            {"icon": "buscar.png", "text": "  Buscar Libro", "action": "Buscar Libro"},
            {"icon": "eliminar.png", "text": "  Eliminar Libro", "action": "Eliminar Libro"},
            {"icon": "modificar.png", "text": "  Modificar Libro", "action": "Modificar Libro"}
        ]
        inventario_card = self._crear_tarjeta("Inventario", opciones_inventario, card_width, card_height)
        layout_cards_holder.addWidget(inventario_card)

        opciones_finanzas = [
            {"icon": "vender.png", "text": "  Vender Libro", "action": "Vender Libro"},
            {"icon": "ingreso.png", "text": "  Reportar Ingreso", "action": "Reportar Ingreso"},
            {"icon": "gasto.png", "text": "  Reportar Gasto", "action": "Reportar Gasto"},
            {"icon": "contabilidad.png", "text": "  Generar Contabilidad", "action": "Generar Contabilidad"},
            {"icon": "pedidos.png", "text": "  Generar Pedidos", "action": "Generar Pedidos"}        ]
        finanzas_card = self._crear_tarjeta("Finanzas", opciones_finanzas, card_width, card_height)
        layout_cards_holder.addWidget(finanzas_card)
        
        layout_overall_content.addWidget(cards_holder_widget)
        layout_overall_content.addStretch(1)

        self.root_layout.addStretch(1)
        self.root_layout.addWidget(overall_content_widget, 0, Qt.AlignmentFlag.AlignHCenter)
        self.root_layout.addStretch(1)

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
        layout_tarjeta.setContentsMargins(30, 30, 30, 30) # Padding dentro de la tarjeta
        layout_tarjeta.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_tarjeta.setSpacing(10) # Espacio entre título y botones, y entre botones

        titulo_seccion = QLabel(titulo_str)
        font_titulo_seccion = QFont(self.font_family, 16, QFont.Weight.Bold)
        titulo_seccion.setFont(font_titulo_seccion)
        titulo_seccion.setAlignment(Qt.AlignmentFlag.AlignLeft)
        titulo_seccion.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; border: none; }")
        layout_tarjeta.addWidget(titulo_seccion)

        # No necesitamos font_botones aquí, se define en CustomButton

        for item_data in opciones_data:
            texto_visible_original = item_data["text"]
            texto_accion = item_data["action"]
            nombre_archivo_icono = item_data["icon"]
            
            ruta_icono_completa = os.path.join(IMAGE_DIR, nombre_archivo_icono)
            
            # Usamos nuestro CustomButton
            boton_personalizado = CustomButton(icon_path=ruta_icono_completa, text=texto_visible_original.strip())
            boton_personalizado.clicked.connect(lambda accion=texto_accion: accion_pendiente(accion, self))
            
            layout_tarjeta.addWidget(boton_personalizado)

        layout_tarjeta.addStretch(1) # Empuja los botones hacia arriba si hay espacio extra en la tarjeta
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