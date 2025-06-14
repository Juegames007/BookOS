import sys
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
                             QWidget, QLabel, QSpacerItem, QSizePolicy, QApplication,
                             QTreeWidget, QTreeWidgetItem, QHeaderView, QStyledItemDelegate)
from PySide6.QtCore import Qt, QDate, QPoint, QSize
from PySide6.QtGui import QFont, QIcon, QMouseEvent, QColor, QPainter, QBrush, QPen, QFontDatabase
from datetime import datetime
import logging
import os

# Ajuste de sys.path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(APP_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from features.finance_service import FinanceService
from gui.common.styles import FONTS
from core.models import Ingreso, Egreso

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CardDelegate(QStyledItemDelegate):
    """
    Dibuja el fondo de toda la fila como una tarjeta redondeada y se encarga
    de pintar el texto de cada celda.
    """
    def paint(self, painter: QPainter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # --- 1. Dibuja el fondo de la fila ---
        # El cálculo y dibujo se hace solo una vez por fila (al pintar la columna 0)
        if index.column() == 0:
            # Obtenemos el color de fondo guardado en el item
            color_index = index.sibling(index.row(), 0)
            background_color = color_index.data(Qt.ItemDataRole.BackgroundRole)
            
            if background_color and isinstance(background_color, QColor):
                # Usamos el QTreeWidget como padre para obtener el ancho del viewport
                tree_widget = self.parent()
                
                # Rectángulo de la fila entera
                row_rect = tree_widget.visualRect(index)
                row_rect.setWidth(tree_widget.viewport().width())
                
                # Margen vertical para el efecto "flotante". El margen horizontal lo da el QTreeWidget.
                row_rect.adjust(0, 4, 0, -4)
                
                painter.setBrush(background_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(row_rect, 8, 8)

        # --- 2. Dibuja el contenido de la celda (texto) ---
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text:
            # Rectángulo de la celda actual
            text_rect = option.rect
            text_rect.adjust(8, 0, -8, 0)  # Padding horizontal para el texto

            # Color del texto (si no, usará el de la paleta por defecto)
            text_color = index.data(Qt.ItemDataRole.ForegroundRole)
            if text_color and isinstance(text_color, QBrush):
                 painter.setPen(QPen(text_color.color()))
            else:
                 painter.setPen(QPen(QColor("black")))

            # Alineación del texto
            alignment = index.data(Qt.ItemDataRole.TextAlignmentRole)
            if alignment is None:
                alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            
            # Fuente del texto
            font = index.data(Qt.ItemDataRole.FontRole)
            if font and isinstance(font, QFont):
                painter.setFont(font)

            painter.drawText(text_rect, int(alignment), text)

        painter.restore()

class ModifyFinancesDialog(QDialog):
    def __init__(self, finance_service: FinanceService, parent=None):
        super().__init__(parent)
        self.finance_service = finance_service
        self.font_family = FONTS["family"]
        self._drag_pos = QPoint()
        self.original_values = {}

        self._setup_window()
        self._init_ui()
        self._load_finances_for_today()

    def _setup_window(self):
        self.setWindowTitle("Finanzas del Día")
        self.setMinimumWidth(1200)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

    def _init_ui(self):
        # El diálogo principal es solo un contenedor transparente
        self.setStyleSheet("background:transparent;")
        self.setObjectName("ModifyFinancesDialog")

        # Este widget de fondo tendrá el estilo de "cristal"
        background_widget = QWidget(self)
        background_widget.setObjectName("main-dialog-background")
        background_widget.setStyleSheet("""
            #main-dialog-background {
                background-color: rgba(240, 240, 240, 0.93);
                border-radius: 15px;
                border: 1px solid rgba(200, 200, 200, 0.4);
            }
        """)
        
        # Un layout raíz para el diálogo, que contiene el widget de fondo
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(background_widget)

        # El layout de contenido, que ahora va dentro del widget de fondo
        main_layout = QVBoxLayout(background_widget)
        main_layout.setContentsMargins(25, 20, 25, 25)
        
        # --- Barra de Título ---
        title_bar_layout = QHBoxLayout()
        title_label = QLabel("Finance of the Day")
        title_label.setFont(QFont(self.font_family, 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333; background: transparent;")
        
        close_button = QPushButton("✕")
        close_button.setFont(QFont(self.font_family, 14))
        close_button.setFixedSize(32, 32)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setStyleSheet(
            "QPushButton { border: none; background-color: #e74c3c; color: white; border-radius: 16px; }"
            "QPushButton:hover { background-color: #c0392b; }"
        )
        close_button.clicked.connect(self.reject)
        
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        main_layout.addLayout(title_bar_layout)
        
        main_layout.addSpacerItem(QSpacerItem(0, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.tree = self._create_tree_widget()
        main_layout.addWidget(self.tree)
        
        main_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.save_button = QPushButton("Save Changes")
        self.save_button.setFont(QFont(self.font_family, 12, QFont.Weight.Bold))
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.setFixedSize(180, 45)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #4a627a; }
            QPushButton:pressed { background-color: #2c3e50; }
        """)
        self.save_button.clicked.connect(self._save_changes)
        main_layout.addWidget(self.save_button, 0, Qt.AlignmentFlag.AlignCenter)

    def _create_tree_widget(self) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setColumnCount(6)
        tree.setHeaderLabels(["ID", "Time", "Type", "Concept", "Amount", "Payment Method"])
        tree.setFont(QFont(self.font_family, 11))
        tree.header().setFont(QFont(self.font_family, 12, QFont.Weight.Bold))
        tree.setItemDelegate(CardDelegate(tree))
        
        # Desactivar el foco y la selección punteada para un look más limpio
        tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tree.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)

        tree.setStyleSheet("""
            QTreeWidget { 
                border: none;
                background-color: transparent;
                margin: 0 5px; /* Margen unificado para todo el tree view */
            }
            QHeaderView {
                background-color: white;
                border-radius: 8px;
                margin: 0; /* El margen lo controla el QTreeWidget padre */
            }
            QHeaderView::section { 
                background-color: transparent;
                color: #333;
                padding: 14px 5px;
                border: none;
                font-weight: 600;
            }
            QTreeWidget::item {
                /* El delegate se encarga de todo */
                border: none;
            }
        """)

        header = tree.header()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- Columnas con ancho fijo y no redimensionables ---
        widths = [80, 130, 120, 480, 150, 170]
        for i, width in enumerate(widths):
            tree.setColumnWidth(i, width)
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        
        tree.setUniformRowHeights(True)
        tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        return tree

    def _load_finances_for_today(self):
        self.tree.clear()
        today = QDate.currentDate().toString("yyyy-MM-dd")
        ingresos, egresos = self.finance_service.get_finances_by_date(today)
        
        all_transactions = [("ingreso", i) for i in ingresos] + [("egreso", e) for e in egresos]
        all_transactions.sort(key=lambda x: x[1].fecha, reverse=True)

        for trx_type, trx in all_transactions:
            self._add_item_to_tree(trx, trx_type)
        
        self._adjust_height()
        
    def _adjust_height(self):
        item_count = self.tree.topLevelItemCount()
        
        # Alturas base de los componentes fijos (título, botones, espaciadores)
        base_dialog_height = 180 
        header_height = self.tree.header().height() + 5 if item_count > 0 else 0
        row_height = 52 # Incluye el alto de la fila + el espaciado vertical

        content_height = header_height + (row_height * item_count)
        total_height = base_dialog_height + content_height

        self.setFixedHeight(int(total_height))

    def _add_item_to_tree(self, trx, trx_type: str):
        trx_id = trx.id_ingreso if trx_type == "ingreso" else trx.id_egreso
        
        try:
            # Formatear hora a AM/PM
            time_obj = datetime.strptime(trx.fecha, '%Y-%m-%d %H:%M:%S')
            time_str = time_obj.strftime('%I:%M %p')
        except (ValueError, TypeError):
            time_str = trx.fecha # Fallback

        item = QTreeWidgetItem(self.tree)
        # La altura se controla con setUniformRowHeights y el espaciado en el delegate
        item.setSizeHint(0, QSize(0, 44)) 
        
        # Guardamos la fuente para que el delegate la use
        font = QFont(self.font_family, 11)
        font_bold = QFont(self.font_family, 11, QFont.Weight.Bold)

        # Establecer datos para cada columna
        item.setText(0, str(trx_id))
        item.setData(0, Qt.ItemDataRole.TextAlignmentRole, Qt.AlignmentFlag.AlignCenter)
        
        item.setText(1, time_str)
        item.setData(1, Qt.ItemDataRole.TextAlignmentRole, Qt.AlignmentFlag.AlignCenter)

        item.setText(2, trx_type.capitalize())
        item.setData(2, Qt.ItemDataRole.TextAlignmentRole, Qt.AlignmentFlag.AlignCenter)
        item.setFont(2, font_bold)

        item.setText(3, trx.concepto)
        item.setData(3, Qt.ItemDataRole.TextAlignmentRole, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        item.setText(4, f"${trx.monto:,.0f}")
        item.setData(4, Qt.ItemDataRole.TextAlignmentRole, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        item.setFont(4, font_bold)

        item.setText(5, trx.metodo_pago)
        item.setData(5, Qt.ItemDataRole.TextAlignmentRole, Qt.AlignmentFlag.AlignCenter)

        # Aplicar fuente y color de fondo a todas las columnas
        for i in range(item.columnCount()):
            item.setFont(i, font) # Fuente base
            if i == 2 or i == 4:
                item.setFont(i, font_bold) # Sobrescribir con negrita donde corresponda
            
            # El color de fondo se define una vez para toda la fila
            row_color = QColor("#ffffff")
            item.setData(i, Qt.ItemDataRole.BackgroundRole, row_color)

        item.setData(0, Qt.ItemDataRole.UserRole, (trx_id, trx_type))
        # Habilitar la edición en las columnas correspondientes
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

        self.original_values[(trx_id, trx_type)] = {
            'concepto': trx.concepto, 
            'monto': trx.monto,
            'metodo_pago': trx.metodo_pago
        }

    def _on_item_double_clicked(self, item, column):
        # Permitir edición en Concepto(3), Monto(4) y Método(5)
        if column in [3, 4, 5]:
            # Reactivamos la selección temporalmente para que el editor funcione
            self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
            self.tree.setCurrentItem(item)
            self.tree.editItem(item, column)
            # Volvemos a desactivarla cuando la edición termina
            self.tree.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        else:
            self.tree.closePersistentEditor(item, column)

    def _save_changes(self):
        # Como la selección está desactivada, necesitamos una forma de saber en qué item estamos.
        # Por ahora, asumiremos que la edición se guarda al presionar Enter o perder el foco.
        # Este botón necesitará una lógica más elaborada o un cambio de UX.
        
        editor = self.tree.itemDelegate()
        if not editor or not isinstance(editor, CardDelegate):
             return

        # El botón de guardado global es complejo sin una selección clara.
        # La lógica actual actualiza el item al terminar la edición.
        # Vamos a enfocarlo a guardar el item que se está editando o el último editado.
        
        # Por ahora, mostraremos un mensaje informativo.
        QMessageBox.information(self, "Guardar Cambios", 
            "La edición de cada campo se guarda al presionar Enter o cambiar de celda. "
            "Este botón guardará todos los cambios en la base de datos en el futuro.")

        # La lógica de guardado a la BD se ha vuelto más compleja.
        # Se necesita un mecanismo para rastrear todos los items modificados.
        # Por ahora, esta función queda como placeholder.
        self.accept() # Cierra el diálogo por ahora.
        return

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

if __name__ == '__main__':
    class MockFinanceService:
        def get_finances_by_date(self, date):
            ingresos = [Ingreso(1, 12000, "Venta libro 'Cien Años de Soledad'", "Nequi", "2023-01-01 10:20:00", None, 1, None),
                        Ingreso(2, 15000, "Venta libro 'El Amor en los Tiempos del Cólera'", "Efectivo", "2023-01-01 12:30:00", None, 2, None)]
            egresos = [Egreso(1, 21000, "Pago de servicios públicos", "Tarjeta", "2023-01-01 09:00:00", None)]
            return ingresos, egresos
        def update_ingreso(self, *args): print(f"Mock update_ingreso: {args}"); return True
        def update_egreso(self, *args): print(f"Mock update_egreso: {args}"); return True

    app = QApplication(sys.argv)
    font_path = os.path.join(PROJECT_ROOT, "gui", "resources", "fonts", "Montserrat-Regular.ttf")
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)

    service = MockFinanceService()
    dialog = ModifyFinancesDialog(service)
    dialog.show()
    sys.exit(app.exec()) 