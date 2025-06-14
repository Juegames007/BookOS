import os
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpacerItem, QSizePolicy, QMessageBox, QFrame, QDoubleSpinBox,
    QGridLayout, QButtonGroup
)
from PySide6.QtGui import QFont, QIcon, QMouseEvent, QPainter, QColor
from PySide6.QtCore import Qt, Signal, QPoint, QSize

from features.egreso_service import EgresoService
from gui.common.styles import FONTS, COLORS, STYLES
from gui.common.utils import get_icon_path, format_price

class EgresoDialog(QDialog):
    """
    Diálogo rediseñado para registrar un nuevo egreso con una interfaz moderna.
    """
    def __init__(self, egreso_service: EgresoService, parent: QWidget = None):
        super().__init__(parent)
        self.egreso_service = egreso_service
        self.font_family = FONTS.get("family", "Montserrat")
        self.payment_method = None
        
        self.setWindowTitle("Registrar Egreso")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._drag_pos = QPoint()

        self._setup_ui()

    def exec(self):
        return super().exec()

    def reject(self):
        super().reject()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = QPoint()
        event.accept()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setMinimumWidth(550)
        main_frame.setStyleSheet(f"""
            #mainFrame {{
                background-color: rgba(255, 255, 255, 0.5);
                border: 0.5px solid white;
                border-radius: 16px;
                padding: 20px;
            }}
            QLabel {{
                background-color: transparent;
                font-family: "{self.font_family}";
            }}
            QPushButton {{
                font-family: "{self.font_family}";
            }}
        """)
        main_layout.addWidget(main_frame)

        content_layout = QVBoxLayout(main_frame)
        content_layout.setSpacing(15)

        # --- Cabecera ---
        header_layout = QHBoxLayout()
        title_label = QLabel("Registrar Egreso")
        title_label.setFont(QFont(self.font_family, 18, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f'''
            QPushButton {{
                background: transparent;
                color: {COLORS['text_primary']};
                border: none;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {COLORS['accent_red']};
            }}
        ''')
        close_btn.clicked.connect(self.reject)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        content_layout.addLayout(header_layout)
        
        # --- Etiquetas Rápidas ---
        tags_layout = QGridLayout()
        tags_layout.setSpacing(10)

        etiquetas = [
            ("Almuerzo", "almuerzo.png"), 
            ("Adquisición Libros", "adquisicion_libros.png"),
            ("Salario", "salario.png"),
            ("Servicios", "servicios.png"),
            ("Pasabocas", "pasabocas.png")
        ]

        for i, (text, icon) in enumerate(etiquetas):
            button = QPushButton(QIcon(get_icon_path(icon)), f"  {text}")
            button.setStyleSheet(STYLES['button_tertiary_full'])
            button.setIconSize(QSize(20, 20))
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked, t=text: self.concepto_input.setText(t))
            row, col = divmod(i, 3)
            tags_layout.addWidget(button, row, col)

        content_layout.addLayout(tags_layout)

        # --- Campos de Entrada ---
        input_layout = QVBoxLayout()
        input_layout.setSpacing(5)

        concepto_label = QLabel("Concepto del Egreso:")
        concepto_label.setFont(QFont(self.font_family, 10, QFont.Weight.DemiBold))
        concepto_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.concepto_input = QLineEdit()
        self.concepto_input.setPlaceholderText("Ej: Compra de papelería...")
        self.concepto_input.setStyleSheet(STYLES['line_edit_style'])
        self.concepto_input.setFixedHeight(45)

        monto_label = QLabel("Monto del Egreso:")
        monto_label.setFont(QFont(self.font_family, 10, QFont.Weight.DemiBold))
        monto_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.monto_input = QLineEdit()
        self.monto_input.setPlaceholderText("0")
        self.monto_input.setStyleSheet(STYLES['line_edit_style'])
        self.monto_input.setFixedHeight(45)
        self.monto_input.textChanged.connect(self._format_monto_input)

        input_layout.addWidget(concepto_label)
        input_layout.addWidget(self.concepto_input)
        input_layout.addSpacing(5)
        input_layout.addWidget(monto_label)
        input_layout.addWidget(self.monto_input)
        content_layout.addLayout(input_layout)

        # --- Payment Method ---
        payment_label = QLabel("Método de Pago:")
        payment_label.setFont(QFont(self.font_family, 10, QFont.Weight.DemiBold))
        content_layout.addWidget(payment_label)
        
        payment_buttons_layout = QHBoxLayout()
        payment_buttons_layout.setSpacing(10)
        self.payment_button_group = QButtonGroup(self)
        self.payment_button_group.setExclusive(True)

        payment_methods = [
            ("Efectivo", "dinero.png"),
            ("Nequi", "nequi.png"),
            ("Daviplata", "daviplata.png"),
            ("Bold", "Bold.png")
        ]

        for text, icon_name in payment_methods:
            btn = QPushButton(QIcon(get_icon_path(icon_name)), f" {text}")
            btn.setIconSize(QSize(22, 22))
            btn.setCheckable(True)
            btn.setFixedHeight(40)
            btn.setStyleSheet(STYLES.get('button_toggle_transparent_style', ""))
            btn.clicked.connect(lambda checked, b=text: self._on_payment_method_selected(b))
            self.payment_button_group.addButton(btn)
            payment_buttons_layout.addWidget(btn)
        
        content_layout.addLayout(payment_buttons_layout)

        # --- Botón de Registro ---
        button_layout = QHBoxLayout()
        self.registrar_button = QPushButton("Registrar Egreso")
        self.registrar_button.setFixedHeight(45)
        self.registrar_button.setFont(QFont(self.font_family, 11, QFont.Weight.Bold))
        
        registrar_style = STYLES.get("button_success_full", "").replace("color: white;", "color: black;")
        self.registrar_button.setStyleSheet(registrar_style)
        
        self.registrar_button.setCursor(Qt.PointingHandCursor)
        self.registrar_button.clicked.connect(self._registrar_egreso)
        
        button_layout.addStretch()
        button_layout.addWidget(self.registrar_button)
        button_layout.addStretch()
        content_layout.addLayout(button_layout)

    def _on_payment_method_selected(self, method):
        self.payment_method = method

    def _format_monto_input(self):
        text = self.monto_input.text()
        clean_text = "".join(filter(str.isdigit, text))
        if clean_text:
            formatted_text = format_price(int(clean_text))
            if text != formatted_text:
                self.monto_input.blockSignals(True)
                self.monto_input.setText(formatted_text)
                self.monto_input.blockSignals(False)

    def _registrar_egreso(self):
        concepto = self.concepto_input.text().strip()
        monto_str = "".join(filter(str.isdigit, self.monto_input.text()))
        monto = float(monto_str) if monto_str else 0.0

        if not concepto:
            QMessageBox.warning(self, "Campo Vacío", "Por favor, ingrese un concepto para el egreso.")
            return

        if monto <= 0:
            QMessageBox.warning(self, "Monto Inválido", "Por favor, ingrese un monto mayor a cero.")
            return

        if not self.payment_method:
            QMessageBox.warning(self, "Método de Pago", "Por favor, seleccione un método de pago.")
            return

        success = self.egreso_service.registrar_egreso(
            monto=monto, 
            concepto=concepto,
            metodo_pago=self.payment_method
        )

        if success:
            QMessageBox.information(self, "Éxito", f"El egreso '{concepto}' por ${format_price(monto)} ha sido registrado.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el egreso. Revise la consola para más detalles.")
            self.reject()

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    from core.sqlmanager import SQLManager
    
    # --- Configuración para prueba ---
    # Esto es solo para poder ejecutar el diálogo de forma independiente.
    # En la aplicación real, el SQLManager y el EgresoService se inyectan desde la ventana principal.
    
    # Crear una base de datos en memoria para la prueba
    DB_PATH = ":memory:"
    SCHEMAS_PATH = os.path.join(os.path.dirname(__file__), '../../core/schemas.json')

    if not os.path.exists(SCHEMAS_PATH):
        print(f"Error: No se encontró el archivo de esquemas en {SCHEMAS_PATH}")
    else:
        app = QApplication([])
        
        # Simular el entorno de la app
        data_manager = SQLManager(db_path=DB_PATH)
        data_manager.connect()
        data_manager.create_tables_from_schema(schema_file=SCHEMAS_PATH)
        
        egreso_service_test = EgresoService(data_manager)
        
        # Crear y mostrar el diálogo
        dialog = EgresoDialog(egreso_service_test)
        dialog.exec()
        
        data_manager.close()
        app.quit() 