import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from typing import List, Dict, Any

from gui.common.styles import FONTS # Asumiendo que FONTS está en styles

class ResultsTableWidget(QFrame):
    def __init__(self, headers: List[str], column_weights: List[int], parent=None):
        super().__init__(parent)
        self.headers = headers
        self.column_weights = column_weights
        self.font_family = FONTS.get("family", "Arial")
        
        # Constantes de estilo (podrían pasarse o tomarse de un common.styles más específico)
        self.HEADER_ROW_HEIGHT = 30
        self.BOOK_ROW_HEIGHT = 40
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

            for field_text, weight in zip(row_values, self.column_weights):
                cell_frame = QFrame()
                cell_frame.setStyleSheet(self.cell_style_sheet)
                cell_layout = QVBoxLayout(cell_frame) # Usar QVBoxLayout
                cell_layout.setContentsMargins(0,0,0,0)
                cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centrar QLabel
                lbl = QLabel(str(field_text)) # Asegurar que sea string
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter) # Alinear texto
                lbl.setFont(QFont(self.font_family, FONTS.get("size_small", 10) -1))
                lbl.setWordWrap(True)
                lbl.setStyleSheet("color: #333; background-color:transparent;")
                cell_layout.addWidget(lbl)
                book_row_layout.addWidget(cell_frame, weight)
            
            self.main_layout.addWidget(book_row_widget)
        
        self.main_layout.addStretch(1) # Para que las filas no se expandan si hay pocas

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
