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
        except Exception as e:
            print(f"Error al centrar ventana (usando fallback): {e}")
            self.setGeometry(100, 100, target_width, target_height)

        self.background_pixmap = QPixmap(BACKGROUND_IMAGE_PATH)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_v_layout = QVBoxLayout(self.central_widget)

        # Guardar referencias a elementos que podríamos ocultar si la imagen falla
        self.title_label_ref = None
        self.cards_holder_widget_ref = None

        if self.background_pixmap.isNull():
            print(f"ADVERTENCIA MUY IMPORTANTE: No se pudo cargar la imagen de fondo desde: {BACKGROUND_IMAGE_PATH}")
            print("Verifica que la carpeta 'imagenes' exista en el mismo directorio que el script y que 'fondo.png' esté adentro y sea una imagen válida.")
            # Fondo de error MUY OBVIO para el widget central si la imagen falla
            self.central_widget.setStyleSheet("QWidget { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #D32F2F, stop:1 #FF5252); }")
            # Opcional: podrías añadir un QLabel aquí con el mensaje de error también
            error_label = QLabel(f"Error: No se pudo cargar '{BACKGROUND_IMAGE_PATH}'.\nVerifica la ruta y el archivo.", self.central_widget)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("QLabel { color: white; font-size: 18px; background-color: transparent; }")
            self.main_v_layout.addWidget(error_label, stretch=1)

        else:
            # Si la imagen carga, configurar la UI normal
            self.central_widget.setStyleSheet("QWidget { background: transparent; }") # Crucial
            self._setup_ui_normal()


    def _setup_ui_normal(self):
        """Configura la UI normal cuando la imagen de fondo se ha cargado."""
        self.main_v_layout.setContentsMargins(30, 30, 30, 30)
        self.main_v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.title_label_ref = QLabel("Gestión Librería")
        title_font = QFont("Arial", 36, QFont.Weight.Bold)
        self.title_label_ref.setFont(title_font)
        self.title_label_ref.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label_ref.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.95);
                background-color: transparent;
                padding-bottom: 10px;
            }
        """)
        self.main_v_layout.addWidget(self.title_label_ref)
        self.main_v_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.cards_holder_widget_ref = QWidget()
        self.cards_holder_widget_ref.setStyleSheet("QWidget { background: transparent; }") # Crucial
        cards_holder_layout = QHBoxLayout(self.cards_holder_widget_ref)
        cards_holder_layout.setSpacing(30)
        cards_holder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_width = 380
        card_height = 480

        opciones_inventario = [
            ("➕ Agregar Libro", "Agregar Libro"), ("🔍 Buscar Libro", "Buscar Libro"),
            ("🗑️ Eliminar Libro", "Eliminar Libro"), ("✏️ Modificar Libro", "Modificar Libro")
        ]
        inventario_card = self._crear_tarjeta("Inventario", opciones_inventario, card_width, card_height)
        cards_holder_layout.addWidget(inventario_card)

        opciones_finanzas = [
            ("📈 Reportar Ingreso", "Reportar Ingreso"), ("📉 Reportar Gasto", "Reportar Gasto"),
            ("🧾 Generar Contabilidad", "Generar Contabilidad"), ("📦 Generar Pedidos", "Generar Pedidos")
        ]
        finanzas_card = self._crear_tarjeta("Finanzas", opciones_finanzas, card_width, card_height)
        cards_holder_layout.addWidget(finanzas_card)

        self.main_v_layout.addWidget(self.cards_holder_widget_ref, stretch=1)


    def _crear_tarjeta(self, titulo_str, opciones_btns, ancho, alto):
        tarjeta = QFrame()
        tarjeta.setFixedSize(ancho, alto)
        # --- AUMENTAMOS LA TRANSPARENCIA DE LAS TARJETAS ---
        # Alfa reducido de 120 a 80 para mayor transparencia. (0 es invisible, 255 es opaco)
        tarjeta.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 80); /* Blanco MUY semi-transparente (alfa 80) */
                border-radius: 25px;
                border: 1px solid rgba(220, 220, 220, 70); /* Borde aún más sutil */
            }}
        """)
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(30, 30, 30, 30)
        layout_tarjeta.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_tarjeta.setSpacing(15)

        titulo_seccion = QLabel(titulo_str)
        font_titulo_seccion = QFont("Arial", 22, QFont.Weight.Bold)
        titulo_seccion.setFont(font_titulo_seccion)
        titulo_seccion.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # El color del texto del título de sección debe contrastar con el fondo que se verá a través de la tarjeta
        titulo_seccion.setStyleSheet("QLabel { color: #E0E0E0; background-color: transparent; padding-bottom: 10px; }") # Texto más claro
        layout_tarjeta.addWidget(titulo_seccion)

        font_botones = QFont("Arial", 14)
        button_height = 50

        for texto_btn_completo, texto_accion in opciones_btns:
            boton = QPushButton(f"{texto_btn_completo}  >")
            boton.setFont(font_botones)
            boton.setFixedHeight(button_height)
            # --- MODIFICA ESTE BLOQUE DE ESTILO QSS PARA LOS BOTONES ---
            boton.setStyleSheet("""
                QPushButton {
                    background-color: rgba(248, 249, 250, 100); /* Color base muy claro, alfa 100 (MUY transparente) */
                    color: #202427; /* Texto oscuro. Verifica legibilidad con tu fondo. */
                    border: 1px solid rgba(200, 200, 200, 80); /* Borde aún más sutil y transparente */
                    border-radius: 10px;
                    padding-left: 15px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: rgba(240, 245, 248, 120); /* Un poco más opaco/diferente en hover (alfa 120) */
                    border: 1px solid rgba(190, 190, 190, 100);
                }
                QPushButton:pressed {
                    background-color: rgba(230, 238, 245, 140); /* Más opaco al presionar (alfa 140) */
                }
            """)
            boton.clicked.connect(lambda checked=False, accion=texto_accion: accion_pendiente(accion, self))
            layout_tarjeta.addWidget(boton)

        layout_tarjeta.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        return tarjeta

    def paintEvent(self, event):
        if not self.background_pixmap.isNull():
            painter = QPainter(self)
            scaled_pixmap = self.background_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
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