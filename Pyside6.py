import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtGui import (
    QPixmap, QPalette, QBrush, QFont, QColor, QIcon, QScreen, QPainter, QCursor
)
from PySide6.QtCore import Qt, QSize, QRect, QPoint, Signal

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
    clicked = Signal()

    def __init__(self, icon_path=None, text="", parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(50)

        self.font_family = "San Francisco"
        self.text_color = "#202427"
        self.icon_size = QSize(24, 24)

        self.style_normal = f"""
            QFrame {{
                background-color: rgba(248, 249, 250, 100);
                border: 1px solid rgba(200, 200, 200, 80);
                border-radius: 10px;
            }}
            QLabel {{
                color: {self.text_color};
                background-color: transparent;
                border: none;
                padding: 0px;
            }}
        """
        self.style_hover = f"""
            QFrame {{
                background-color: rgba(240, 245, 248, 120);
                border: 1px solid rgba(190, 190, 190, 100);
                border-radius: 10px;
            }}
            QLabel {{ color: {self.text_color}; background-color: transparent; border:none; padding: 0px; }}
        """
        self.style_pressed = f"""
            QFrame {{
                background-color: rgba(230, 238, 245, 140);
                border: 1px solid rgba(180, 180, 180, 120);
                border-radius: 10px;
            }}
            QLabel {{ color: {self.text_color}; background-color: transparent; border:none; padding: 0px; }}
        """
        self.setStyleSheet(self.style_normal)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        self.icon_label = QLabel()
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(self.icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            if icon_path:
                 print(f"Advertencia: No se pudo cargar el icono para CustomButton: {icon_path}")
            self.icon_label.setFixedSize(0,0)
            layout.setSpacing(0)

        self.text_label = QLabel(text)
        font_botones = QFont(self.font_family, 11)
        self.text_label.setFont(font_botones)

        self.arrow_label = QLabel(">")
        self.arrow_label.setFont(font_botones)
        self.arrow_label.setFixedWidth(self.arrow_label.fontMetrics().horizontalAdvance("> ") + 5)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addStretch(1)
        layout.addWidget(self.arrow_label)

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
            if self.rect().contains(event.position().toPoint()):
                self.setStyleSheet(self.style_hover)
                self.clicked.emit()
            else:
                self.setStyleSheet(self.style_normal)
        super().mouseReleaseEvent(event)

class VentanaGestionLibreria(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión Librería con PySide6")
        self.font_family = "San Francisco"

        target_width = 1366 # Ancho suficiente para 3 columnas de 300px + espaciados
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
        layout_cards_holder.setSpacing(25) # Espacio horizontal entre columnas
        layout_cards_holder.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        card_width = 300
        main_card_height = 280
        extra_card_height = 160 # Para las tarjetas invisibles de relleno
        card_spacing = 15 # Espaciado vertical DENTRO de una columna

        # --- Columna para Inventario ---
        inventario_columna_widget = QWidget()
        inventario_columna_widget.setStyleSheet("QWidget { background: transparent; }")
        layout_inventario_columna = QVBoxLayout(inventario_columna_widget)
        layout_inventario_columna.setContentsMargins(0,0,0,0)
        layout_inventario_columna.setSpacing(card_spacing)

        # "Eliminar Libro" se movió a Ajustes. Asegúrate que estas 3 son las que quieres.
        opciones_inventario_main = [
            {"icon": "agregar.png", "text": "  Agregar Libro", "action": "Agregar Libro"},
            {"icon": "buscar.png", "text": "  Buscar Libro", "action": "Buscar Libro"},
            {"icon": "modificar.png", "text": "  Modificar Libro", "action": "Modificar Libro"} # Asumiendo esta como la tercera
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
        layout_finanzas_columna.setContentsMargins(0,0,0,0)
        layout_finanzas_columna.setSpacing(card_spacing)

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
        layout_ajustes_columna.setContentsMargins(0,0,0,0)
        layout_ajustes_columna.setSpacing(card_spacing)

        opciones_ajustes_main = [
            # Reemplaza 'ajustes_finanzas.png' y 'salir.png' con los nombres de tus iconos
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

        self.root_layout.addStretch(1)
        self.root_layout.addWidget(overall_content_widget, 0, Qt.AlignmentFlag.AlignHCenter)
        self.root_layout.addStretch(1)

    def _crear_tarjeta(self, titulo_str, opciones_data, ancho, alto, con_titulo=True):
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
        
        top_margin = 15 # Margen superior por defecto para tarjetas sin título con opciones
        if con_titulo and titulo_str:
            top_margin = 30
        elif not con_titulo and not opciones_data: # Tarjeta de relleno invisible
            top_margin = 0 # O un valor pequeño si se prefiere, pero 0 para que sea solo espacio

        layout_tarjeta.setContentsMargins(30, top_margin, 30, 30) 
        layout_tarjeta.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_tarjeta.setSpacing(10)

        if con_titulo and titulo_str:
            titulo_seccion = QLabel(titulo_str)
            font_titulo_seccion = QFont(self.font_family, 16, QFont.Weight.Bold)
            titulo_seccion.setFont(font_titulo_seccion)
            titulo_seccion.setAlignment(Qt.AlignmentFlag.AlignLeft)
            titulo_seccion.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 10px; border: none; }")
            layout_tarjeta.addWidget(titulo_seccion)

        for item_data in opciones_data:
            texto_visible_original = item_data["text"]
            nombre_archivo_icono = item_data["icon"]
            accion_definida = item_data["action"]
            
            ruta_icono_completa = os.path.join(IMAGE_DIR, nombre_archivo_icono)
            
            boton_personalizado = CustomButton(icon_path=ruta_icono_completa, text=texto_visible_original.strip())
            
            if accion_definida == "SALIR_APP":
                boton_personalizado.clicked.connect(self.close) 
            else:
                boton_personalizado.clicked.connect(lambda accion=accion_definida: accion_pendiente(accion, self))
            
            layout_tarjeta.addWidget(boton_personalizado)

        layout_tarjeta.addStretch(1)
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