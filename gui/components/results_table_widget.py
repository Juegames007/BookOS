import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PySide6.QtGui import QFont, QPixmap, QDesktopServices
from PySide6.QtCore import Qt, QSize, Signal, QUrl
from typing import List, Dict, Any

from gui.common.styles import FONTS # Asumiendo que FONTS está en styles
from gui.common.widgets import CustomButton # Importar CustomButton

# Rutas a los iconos para la columna de imagen
try:
    CURRENT_SCRIPT_DIR_RTW = os.path.dirname(os.path.abspath(__file__))
    ICON_BASE_PATH_RTW = os.path.join(os.path.dirname(os.path.dirname(CURRENT_SCRIPT_DIR_RTW)), "app", "imagenes")
except NameError:
    ICON_BASE_PATH_RTW = os.path.join("app", "imagenes")

VER_ICON_PATH = os.path.join(ICON_BASE_PATH_RTW, "ver.png")
NO_VER_ICON_PATH = os.path.join(ICON_BASE_PATH_RTW, "no_ver.png")

class ResultsTableWidget(QFrame):
    image_view_requested = Signal(str) # Definir la señal aquí

    def __init__(self, headers: List[str], column_weights: List[int], parent=None):
        super().__init__(parent)
        self.headers = headers
        self.column_weights = column_weights
        self.font_family = FONTS.get("family", "Arial")
        
        # Constantes de estilo (podrían pasarse o tomarse de un common.styles más específico)
        self.HEADER_ROW_HEIGHT = 30
        self.BOOK_ROW_HEIGHT = 50
        self.CELL_SPACING = 5
        self.ROW_SPACING = 5
        self.TABLE_CELL_PADDING = 5

        self.cell_style_sheet = f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.45);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.6);
            }}
            QLabel {{
                background-color: transparent;
                border: none;
                padding: {self.TABLE_CELL_PADDING}px;
            }}
        """
        self.header_cell_style_sheet = f"""
            QFrame {{
                background-color: rgba(235, 235, 245, 0.6);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.5);
            }}
            QLabel {{
                background-color: transparent;
                border: none;
                padding: {self.TABLE_CELL_PADDING}px;
                font-weight: bold;
            }}
        """
        
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self) # Layout principal para esta tabla
        self.main_layout.setContentsMargins(self.ROW_SPACING, self.ROW_SPACING, self.ROW_SPACING, self.ROW_SPACING)
        self.main_layout.setSpacing(self.ROW_SPACING)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # El ancho se manejará externamente por PaginatedResultsWidget o el layout que lo contenga

    def set_data(self, data_rows: List[List[str]]): # data_rows es lista de listas de strings para las celdas
        # Limpiar contenido anterior
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # --- Fila de Cabecera ---
        header_row_widget = QWidget()
        header_row_widget.setFixedHeight(self.HEADER_ROW_HEIGHT)
        header_row_layout = QHBoxLayout(header_row_widget)
        header_row_layout.setContentsMargins(0,0,0,0)
        header_row_layout.setSpacing(self.CELL_SPACING)
        for h_text, weight in zip(self.headers, self.column_weights):
            cell_frame = QFrame()
            cell_frame.setStyleSheet(self.header_cell_style_sheet)
            cell_layout = QVBoxLayout(cell_frame) # Usar QVBoxLayout para centrar verticalmente el QLabel
            cell_layout.setContentsMargins(0,0,0,0)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centrar QLabel en la celda
            lbl = QLabel(h_text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter) # Alinear texto del label
            lbl.setFont(QFont(self.font_family, FONTS.get("size_small", 10), QFont.Weight.Bold))
            lbl.setStyleSheet("color: #222; background-color:transparent;")
            cell_layout.addWidget(lbl)
            header_row_layout.addWidget(cell_frame, weight)
        self.main_layout.addWidget(header_row_widget)

        # --- Filas de Datos ---
        for row_values in data_rows:
            book_row_widget = QWidget() 
            book_row_widget.setFixedHeight(self.BOOK_ROW_HEIGHT)
            book_row_layout = QHBoxLayout(book_row_widget)
            book_row_layout.setContentsMargins(0,0,0,0)
            book_row_layout.setSpacing(self.CELL_SPACING)

            for col_idx, (field_text, weight) in enumerate(zip(row_values, self.column_weights)):
                cell_frame = QFrame()
                cell_layout = QVBoxLayout(cell_frame) 
                cell_layout.setContentsMargins(0,0,0,0)
                cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                header_name = self.headers[col_idx] # Obtener el nombre de la cabecera para esta columna

                if header_name == "Imagen":
                    cell_frame.setStyleSheet(self.cell_style_sheet) 
                    image_url = str(field_text) 
                    icon_to_use = VER_ICON_PATH if image_url and os.path.exists(VER_ICON_PATH) else NO_VER_ICON_PATH
                    
                    btn_ver_imagen = CustomButton(icon_path=icon_to_use, text="")
                    # Hacer el botón más grande para ver si el ícono se muestra completo
                    button_size = self.BOOK_ROW_HEIGHT - 10 # Antes 16 (para diagnóstico), originalmente self.BOOK_ROW_HEIGHT - 18 o -22
                    btn_ver_imagen.setFixedSize(button_size, button_size)
                    btn_ver_imagen.setCursor(Qt.CursorShape.PointingHandCursor if image_url else Qt.CursorShape.ArrowCursor)
                    # Try a more direct stylesheet to make the button itself transparent and borderless
                    btn_ver_imagen.setStyleSheet("""
                        background: transparent;
                        border: none;
                        padding: 0px;
                        margin: 0px;
                    """)

                    if image_url:
                        btn_ver_imagen.clicked.connect(lambda checked=False, url=image_url: self.image_view_requested.emit(url))
                    else:
                        btn_ver_imagen.setEnabled(False)
                    
                    cell_layout.addWidget(btn_ver_imagen, 0, Qt.AlignmentFlag.AlignCenter)

                else: # Para otras columnas, usar QLabel como antes
                    cell_frame.setStyleSheet(self.cell_style_sheet)
                    lbl = QLabel(str(field_text))
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setFont(QFont(self.font_family, FONTS.get("size_small", 10) -1))
                    lbl.setWordWrap(True)
                    lbl.setMinimumHeight(0) # Permitir que se encoja si es necesario
                    lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Permitir expansión
                    lbl.setStyleSheet("color: #333; background-color:transparent;")
                    cell_layout.addWidget(lbl)
                
                book_row_layout.addWidget(cell_frame, weight)
            
            self.main_layout.addWidget(book_row_widget)
        
        # self.main_layout.addStretch(1) # Comentado para probar si mejora la alineación

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication([])

    # Mock FONTS si es necesario para la prueba
    if 'FONTS' not in globals():
        FONTS = {"family": "Arial", "size_small": 10}


    headers_test = ["#", "Título", "Autor", "Categoría"]
    col_weights_test = [1, 5, 4, 4]
    
    table1_data = [
        ["1", "El Señor de los Anillos", "J.R.R. Tolkien", "Fantasía"],
        ["2", "Cien Años de Soledad", "Gabriel García Márquez", "Realismo Mágico"],
    ]
    
    test_window = QWidget()
    test_layout = QVBoxLayout(test_window)
    
    table_widget = ResultsTableWidget(headers=headers_test, column_weights=col_weights_test)
    table_widget.set_data(table1_data)
    table_widget.setFixedWidth(600) # Ancho similar al de la app original

    test_layout.addWidget(QLabel("Tabla de Resultados de Prueba:"))
    test_layout.addWidget(table_widget)
    test_layout.addStretch()

    test_window.resize(700, 400)
    test_window.setWindowTitle("Prueba de ResultsTableWidget")
    test_window.show()

    app.exec()
