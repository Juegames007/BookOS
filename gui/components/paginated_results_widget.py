import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget, QSizePolicy
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect
from typing import List, Dict, Any

from gui.common.styles import FONTS
from gui.common.widgets import CustomButton # Para los botones de navegación y volver
from .results_table_widget import ResultsTableWidget # Importar el componente de tabla

class PaginatedResultsWidget(QWidget):
    back_to_menu_requested = Signal()

    # Constantes de la ventana principal que eran relevantes aquí
    RESULT_TABLE_WIDTH = 600      
    MAX_BOOK_ROWS_PER_TABLE = 12 
    TABLES_PER_PAGE = 2          

    def __init__(self, parent=None):
        super().__init__(parent)
        self.font_family = FONTS.get("family", "Arial")
        
        self.current_results_page_index = 0
        self.total_results_pages = 0
        self.current_page_animation_group = [] # Para animaciones de páginas de resultados

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self) 
        main_layout.setContentsMargins(0, 0, 0, 0) # Ajustar márgenes si es necesario, 0 para que ocupe todo el espacio asignado
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.search_term_label = QLabel("Resultados para: ...")
        font_resultados = QFont(self.font_family, FONTS.get("size_large", 18), QFont.Weight.Bold)
        self.search_term_label.setFont(font_resultados)
        self.search_term_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.search_term_label.setStyleSheet("QLabel { color: black; background-color: transparent; padding-bottom: 20px; }")
        main_layout.addWidget(self.search_term_label)

        self.results_pages_stack = QStackedWidget()
        self.results_pages_stack.setStyleSheet("background-color: transparent;")
        main_layout.addWidget(self.results_pages_stack, 1)

        self.no_results_label = QLabel("No se encontraron libros que coincidan con tu búsqueda.")
        self.no_results_label.setFont(QFont(self.font_family, FONTS.get("size_medium", 14)))
        self.no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_results_label.setStyleSheet("QLabel { color: #555; background-color: transparent; }")
        self.no_results_label.setWordWrap(True)
        self.no_results_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        main_layout.addWidget(self.no_results_label)
        self.no_results_label.hide()

        navigation_and_back_layout = QHBoxLayout()
        
        try:
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            # Asumiendo que 'gui' es un subdirectorio de la raíz del proyecto donde está 'app'
            project_root_dir = os.path.dirname(current_script_dir) # Sube un nivel a 'gui'
            app_dir = os.path.join(os.path.dirname(project_root_dir), "app") # Sube otro nivel a la raíz y luego a 'app'
            icon_base_path = os.path.join(app_dir, "imagenes")
        except Exception:
            icon_base_path = os.path.join("app", "imagenes") # Fallback

        anterior_icon_path = os.path.join(icon_base_path, "anterior.png")
        siguiente_icon_path = os.path.join(icon_base_path, "siguiente.png")

        self.boton_anterior_resultados = CustomButton(icon_path=anterior_icon_path, text="")
        self.boton_anterior_resultados.clicked.connect(self._ir_a_pagina_anterior_resultados)
        self.boton_anterior_resultados.setEnabled(False)
        navigation_and_back_layout.addWidget(self.boton_anterior_resultados)

        navigation_and_back_layout.addStretch(1)

        self.boton_volver_menu = CustomButton(text="Volver al Menú Principal")
        self.boton_volver_menu.clicked.connect(self.back_to_menu_requested.emit)
        navigation_and_back_layout.addWidget(self.boton_volver_menu)

        navigation_and_back_layout.addStretch(1)

        self.boton_siguiente_resultados = CustomButton(icon_path=siguiente_icon_path, text="")
        self.boton_siguiente_resultados.clicked.connect(self._ir_a_pagina_siguiente_resultados)
        self.boton_siguiente_resultados.setEnabled(False)
        navigation_and_back_layout.addWidget(self.boton_siguiente_resultados)
        
        main_layout.addLayout(navigation_and_back_layout)
        self.setStyleSheet("background: transparent;")

    def update_results(self, libros: List[Dict[str, Any]], search_term: str):
        self.search_term_label.setText(f"Resultados para: \"{search_term}\"")
        
        while self.results_pages_stack.count():
            widget = self.results_pages_stack.widget(0)
            self.results_pages_stack.removeWidget(widget)
            if widget:
                widget.deleteLater()

        self.current_results_page_index = 0
        self.total_results_pages = 0

        if not libros:
            self.results_pages_stack.hide()
            self.no_results_label.show()
            self.boton_anterior_resultados.hide()
            self.boton_siguiente_resultados.hide()
        else:
            self.no_results_label.hide()
            self.results_pages_stack.show()
            self.boton_anterior_resultados.show()
            self.boton_siguiente_resultados.show()

            headers = ["#", "Título", "Autor", "Categoría"]
            column_weights = [1, 5, 4, 4]

            num_libros = len(libros)
            libros_por_pagina_fisica = self.MAX_BOOK_ROWS_PER_TABLE * self.TABLES_PER_PAGE
            self.total_results_pages = (num_libros + libros_por_pagina_fisica - 1) // libros_por_pagina_fisica

            libro_idx_global = 0
            for page_num in range(self.total_results_pages):
                page_widget = QWidget() # Contenedor para las tablas de esta página
                page_layout = QHBoxLayout(page_widget)
                page_layout.setContentsMargins(0,0,0,0)
                page_layout.setSpacing(15) # Espacio entre ResultsTableWidget si hay varios
                page_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

                for table_in_page_num in range(self.TABLES_PER_PAGE):
                    if libro_idx_global >= num_libros: break
                    
                    table_component = ResultsTableWidget(headers=headers, column_weights=column_weights)
                    table_component.setFixedWidth(self.RESULT_TABLE_WIDTH)
                    
                    libros_para_esta_tabla = []
                    for _ in range(self.MAX_BOOK_ROWS_PER_TABLE):
                        if libro_idx_global < num_libros:
                            libro_data = libros[libro_idx_global]
                            # Adaptar libro_data al formato List[str] esperado por ResultsTableWidget.set_data
                            libros_para_esta_tabla.append([
                                str(libro_idx_global + 1),
                                libro_data.get("Título", "N/A"),
                                libro_data.get("Autor", "N/A"),
                                ", ".join(libro_data.get("Categorías", [])) if libro_data.get("Categorías") else "-"
                            ])
                            libro_idx_global += 1
                        else:
                            break # No hay más libros
                    
                    if libros_para_esta_tabla:
                        table_component.set_data(libros_para_esta_tabla)
                        page_layout.addWidget(table_component)
                    else:
                        # No debería necesitarse si la lógica de break es correcta
                        table_component.deleteLater() # Limpiar si no se usa
                
                if page_layout.count() > 0:
                    self.results_pages_stack.addWidget(page_widget)
                else:
                    page_widget.deleteLater() # Limpiar página vacía

            self.total_results_pages = self.results_pages_stack.count()
            if self.total_results_pages > 0:
                self.results_pages_stack.setCurrentIndex(0)
            self._actualizar_estado_botones_navegacion()

    def _actualizar_estado_botones_navegacion(self):
        if not self.results_pages_stack or self.total_results_pages == 0:
            self.boton_anterior_resultados.setEnabled(False)
            self.boton_anterior_resultados.hide()
            self.boton_siguiente_resultados.setEnabled(False)
            self.boton_siguiente_resultados.hide()
            return

        self.boton_anterior_resultados.show()
        self.boton_siguiente_resultados.show()
        self.boton_anterior_resultados.setEnabled(self.current_results_page_index > 0)
        self.boton_siguiente_resultados.setEnabled(self.current_results_page_index < self.total_results_pages - 1)

    def _ir_a_pagina_siguiente_resultados(self):
        if self.current_results_page_index < self.total_results_pages - 1:
            nuevo_indice = self.current_results_page_index + 1
            self._mostrar_pagina_resultados_animado(nuevo_indice, direccion_forward=True)

    def _ir_a_pagina_anterior_resultados(self):
        if self.current_results_page_index > 0:
            nuevo_indice = self.current_results_page_index - 1
            self._mostrar_pagina_resultados_animado(nuevo_indice, direccion_forward=False)

    def _mostrar_pagina_resultados_animado(self, nuevo_indice: int, direccion_forward: bool):
        current_page_widget = self.results_pages_stack.widget(self.current_results_page_index)
        next_page_widget = self.results_pages_stack.widget(nuevo_indice)

        if not current_page_widget or not next_page_widget or current_page_widget == next_page_widget:
            if next_page_widget: 
                 self.results_pages_stack.setCurrentWidget(next_page_widget)
                 self.current_results_page_index = nuevo_indice
                 self._actualizar_estado_botones_navegacion()
            return

        rect_stacked = self.results_pages_stack.rect() 

        if direccion_forward:
            next_page_widget.setGeometry(rect_stacked.width(), 0, rect_stacked.width(), rect_stacked.height())
        else:
            next_page_widget.setGeometry(-rect_stacked.width(), 0, rect_stacked.width(), rect_stacked.height())
        
        next_page_widget.show()
        next_page_widget.raise_()

        anim_current_page_slide_out = QPropertyAnimation(current_page_widget, b"geometry")
        anim_current_page_slide_out.setDuration(350)
        anim_current_page_slide_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim_current_page_slide_out.setStartValue(current_page_widget.geometry())
        end_x_current = -rect_stacked.width() if direccion_forward else rect_stacked.width()
        anim_current_page_slide_out.setEndValue(QRect(end_x_current, 0, current_page_widget.width(), current_page_widget.height()))

        anim_next_page_slide_in = QPropertyAnimation(next_page_widget, b"geometry")
        anim_next_page_slide_in.setDuration(350)
        anim_next_page_slide_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim_next_page_slide_in.setStartValue(next_page_widget.geometry())
        anim_next_page_slide_in.setEndValue(rect_stacked)

        for anim in self.current_page_animation_group:
            anim.stop()
        self.current_page_animation_group = [anim_current_page_slide_out, anim_next_page_slide_in]

        def transition_finished():
            current_page_widget.hide()
            self.results_pages_stack.setCurrentWidget(next_page_widget)
            self.current_results_page_index = nuevo_indice
            self._actualizar_estado_botones_navegacion()
            self.current_page_animation_group = []
            try:
                anim_next_page_slide_in.finished.disconnect(transition_finished)
            except RuntimeError: pass

        anim_next_page_slide_in.finished.connect(transition_finished)
        anim_current_page_slide_out.start()
        anim_next_page_slide_in.start()

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    if 'FONTS' not in globals(): FONTS = {"family": "Arial", "size_large":18, "size_medium":14, "size_small":10}

    mock_libros = []
    for i in range(30):
        mock_libros.append({
            "Título": f"Libro de Prueba {i+1}",
            "Autor": f"Autor { (i%5) + 1 }",
            "Categorías": [f"Categoría {(i%3)+1}", f"Otra Cat {(i%2)+1}"]
        })

    paginated_view = PaginatedResultsWidget()
    paginated_view.update_results(mock_libros, "Término de Prueba")
    
    main_win = QWidget() # Simular una ventana principal
    layout = QVBoxLayout(main_win)
    layout.addWidget(paginated_view)
    main_win.resize(800, 600)
    main_win.setWindowTitle("Prueba de PaginatedResultsWidget")
    main_win.show()

    def handle_back_to_menu():
        print("Señal back_to_menu_requested recibida!")
        # Aquí podrías, por ejemplo, cambiar la vista en un QStackedWidget principal
        # main_win.close() # O simplemente cerrar para la prueba

    paginated_view.back_to_menu_requested.connect(handle_back_to_menu)

    app.exec()
