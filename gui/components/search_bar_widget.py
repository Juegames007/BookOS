import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QFrame, QCheckBox, QGraphicsOpacityEffect, QApplication, QGridLayout
)
from PySide6.QtGui import QFont, QPixmap, QIcon
from PySide6.QtCore import Qt, QSize, QEasingCurve, QPropertyAnimation, Signal, QParallelAnimationGroup

from gui.common.styles import FONTS # Asumiendo que FONTS está en styles

class SearchBarWidget(QFrame):
    search_requested = Signal(str, dict) # Término de búsqueda, filtros seleccionados
    # Podríamos añadir una señal para cuando se expande/colapsa si es necesario

    def __init__(self, parent=None):
        super().__init__(parent)
        self.font_family = FONTS.get("family", "Arial") # Usar .get con fallback
        self.search_bar_base_height = 55
        self._filters_visible = False
        self.filter_checkboxes_effects = []
        self.animation_group = None # Se creará bajo demanda
        
        self._setup_ui()

    def __del__(self):
        # Desconectar para evitar advertencias al cerrar
        # Aunque ahora el grupo es efímero, esto no hace daño como salvaguarda
        if self.animation_group:
            try:
                self.animation_group.finished.disconnect(self._on_filter_animation_group_finished)
            except (RuntimeError, TypeError):
                pass

    def _setup_ui(self):
        self.setObjectName("searchBarContainer")
        # El ancho será determinado por el layout que lo contenga en MainWindow, o podemos fijarlo si es necesario.
        # self.setFixedWidth(ancho_deseado) 
        self.setStyleSheet(f"""
            QFrame#searchBarContainer {{
                background-color: rgba(255, 255, 255, 89);
                border-radius: 16px;
                border: 0.5px solid white;
            }}
        """)

        main_search_layout = QVBoxLayout(self)
        main_search_layout.setContentsMargins(0, 0, 0, 0)
        main_search_layout.setSpacing(0)

        top_search_widget = QWidget()
        top_search_widget.setFixedHeight(self.search_bar_base_height)
        layout_top_search = QHBoxLayout(top_search_widget)
        layout_top_search.setContentsMargins(15, 10, 15, 10)
        layout_top_search.setSpacing(10)

        # Intentar construir la ruta de forma más robusta
        try:
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_base_dir = os.path.join(os.path.dirname(os.path.dirname(current_script_dir)), "app", "imagenes")
        except Exception: # Fallback si __file__ no está definido (ej. en algunos intérpretes interactivos)
            icon_base_dir = os.path.join("app", "imagenes")


        search_icon_path = os.path.join(icon_base_dir, "buscar.png")
        search_icon_label = QLabel()
        if os.path.exists(search_icon_path):
            search_pixmap = QPixmap(search_icon_path)
            search_icon_label.setPixmap(search_pixmap.scaled(QSize(24,24), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            search_icon_label.setText("?")
            print(f"Advertencia: No se pudo cargar el icono de búsqueda en: {search_icon_path}")
        search_icon_label.setStyleSheet("background-color: transparent; border: none;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search")
        self.search_input.setFixedHeight(35)
        self.search_input.setFont(QFont(self.font_family, FONTS.get("size_medium", 12)))
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: #333;
                padding-left: 5px;
            }
        """)
        self.search_input.returnPressed.connect(self._emit_search_requested)
        
        self.menu_icon_label = QLabel("≡") # Hacerlo atributo de instancia
        menu_icon_font = QFont(self.font_family, FONTS.get("size_large", 16), QFont.Weight.Bold)
        self.menu_icon_label.setFont(menu_icon_font)
        self.menu_icon_label.setStyleSheet("background-color: transparent; border: none; color: #555;")
        self.menu_icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_icon_label.mousePressEvent = self._toggle_filter_expansion

        layout_top_search.addWidget(search_icon_label)
        layout_top_search.addWidget(self.search_input, 1)
        layout_top_search.addWidget(self.menu_icon_label)
        
        main_search_layout.addWidget(top_search_widget)

        self.filter_options_widget = QWidget(self)
        self.filter_options_widget.setObjectName("filterOptionsWidget")
        self.filter_options_widget.setStyleSheet(f"""
            QWidget#filterOptionsWidget {{
                background-color: transparent;
            }}
            QLabel {{
                 background-color: transparent;
                 color: #444;
            }}
            QCheckBox {{
                background-color: transparent; /* Transparente cuando no está chequeado */
                border: none;
                border-radius: 8px;
                padding: 5px 10px;
                color: #333; /* Color de texto para no chequeado */
                spacing: 5px;
                font-size: {FONTS.get("size_small", 10)}px;
                min-height: 18px; 
            }}
            QCheckBox:hover {{
                background-color: rgba(200, 200, 200, 70); /* Gris muy claro semitransparente para hover en no chequeado */
            }}
            QCheckBox:checked {{
                background-color: #FFA726; /* Naranja vibrante para chequeado */
                color: white; /* Texto blanco para chequeado */
                font-weight: bold;
            }}
            QCheckBox:checked:hover {{
                background-color: #FB8C00; /* Naranja más oscuro para hover en chequeado */
            }}
            QCheckBox::indicator {{
                width: 0px;
                height: 0px;
            }}
        """)
        
        outer_filter_layout = QHBoxLayout(self.filter_options_widget)
        outer_filter_layout.setContentsMargins(0, 10, 0, 15)
        outer_filter_layout.setSpacing(0)

        filter_options_grid_layout = QGridLayout()
        filter_options_grid_layout.setHorizontalSpacing(10)
        filter_options_grid_layout.setVerticalSpacing(10)

        filter_data = [
            ("Título", "filter_by_titulo_cb", "titulo.png"),
            ("Autor", "filter_by_autor_cb", "autor.png"),
            ("Categoría", "filter_by_categoria_cb", "categoria.png")
        ]
        
        checkbox_icon_size = QSize(16, 16)
        self.filter_checkboxes_effects.clear()

        row, col = 0, 0
        for text, attr_name, icon_filename in filter_data:
            checkbox = QCheckBox(text)
            checkbox.setChecked(False)
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            
            icon_path = os.path.join(icon_base_dir, icon_filename)
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                checkbox.setIcon(QIcon(pixmap))
                checkbox.setIconSize(checkbox_icon_size)
            else:
                print(f"Advertencia: No se pudo cargar el icono del filtro: {icon_path}")
            
            opacity_effect = QGraphicsOpacityEffect(checkbox)
            checkbox.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(0.0)
            
            filter_options_grid_layout.addWidget(checkbox, row, col)
            self.filter_checkboxes_effects.append({"checkbox": checkbox, "effect": opacity_effect, "name": attr_name}) # Guardar nombre para el dict de filtros
            setattr(self, attr_name, checkbox)

            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        outer_filter_layout.addStretch(1)
        outer_filter_layout.addLayout(filter_options_grid_layout)
        outer_filter_layout.addStretch(1)
        
        self.filter_options_widget.hide()
        main_search_layout.addWidget(self.filter_options_widget)
        main_search_layout.addStretch(1)

    def _emit_search_requested(self):
        term = self.search_input.text().strip()
        filters = {}
        for item_data in self.filter_checkboxes_effects:
            # Usar el nombre del atributo guardado para la clave del filtro
            # Asumimos que el nombre es algo como "filter_by_title_cb", lo simplificamos
            filter_key = item_data["name"].replace("filter_by_", "").replace("_cb", "")
            filters[filter_key] = item_data["checkbox"].isChecked()
        self.search_requested.emit(term, filters)

    def _toggle_filter_expansion(self, event=None):
        if not hasattr(self, 'filter_options_widget') or not (hasattr(self, 'filter_checkboxes_effects') and bool(self.filter_checkboxes_effects)):
            return

        if self.animation_group and self.animation_group.state() == QParallelAnimationGroup.State.Running:
            self.animation_group.stop()

        # Crear un nuevo grupo de animación para cada toggle
        self.animation_group = QParallelAnimationGroup(self)
        self.animation_group.finished.connect(self._on_filter_animation_group_finished)
        # Asegurar que el grupo se destruya a sí mismo después de terminar
        self.animation_group.finished.connect(self.animation_group.deleteLater)

        height_anim_duration = 280
        opacity_anim_duration = 150

        preferred_filter_height = self.filter_options_widget.sizeHint().height()
        if preferred_filter_height <= 0:
            QApplication.processEvents()
            preferred_filter_height = self.filter_options_widget.layout().sizeHint().height()
        
        current_height = self.filter_options_widget.height()

        if self._filters_visible:  # Ocultar filtros
            target_container_height = 0
            target_opacity = 0.0
            
            height_animation = QPropertyAnimation(self.filter_options_widget, b"maximumHeight")
            height_animation.setDuration(height_anim_duration)
            height_animation.setStartValue(current_height)
            height_animation.setEndValue(target_container_height)
            height_animation.setEasingCurve(QEasingCurve.Type.InQuad)
            self.animation_group.addAnimation(height_animation)

            for item_data in reversed(self.filter_checkboxes_effects):
                opacity_anim = QPropertyAnimation(item_data["effect"], b"opacity")
                opacity_anim.setDuration(opacity_anim_duration) 
                opacity_anim.setStartValue(item_data["effect"].opacity()) 
                opacity_anim.setEndValue(target_opacity)
                opacity_anim.setEasingCurve(QEasingCurve.Type.InSine)
                self.animation_group.addAnimation(opacity_anim)

        else:  # Mostrar filtros
            if preferred_filter_height <= 0: return
            
            target_container_height = preferred_filter_height
            target_opacity = 1.0
            self.filter_options_widget.show()
            self.filter_options_widget.setMaximumHeight(current_height)

            height_animation = QPropertyAnimation(self.filter_options_widget, b"maximumHeight")
            height_animation.setDuration(height_anim_duration)
            height_animation.setStartValue(current_height)
            height_animation.setEndValue(target_container_height)
            height_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
            self.animation_group.addAnimation(height_animation)

            for item_data in self.filter_checkboxes_effects:
                item_data["effect"].setOpacity(0.0)
                opacity_anim = QPropertyAnimation(item_data["effect"], b"opacity")
                opacity_anim.setDuration(opacity_anim_duration) 
                opacity_anim.setStartValue(0.0)
                opacity_anim.setEndValue(target_opacity)
                opacity_anim.setEasingCurve(QEasingCurve.Type.OutSine)
                self.animation_group.addAnimation(opacity_anim)
        
        self.animation_group.start()
        self._filters_visible = not self._filters_visible

    def _on_filter_animation_group_finished(self):
        # Si el emisor no es el grupo de animación actual, significa que es una
        # señal de un grupo antiguo que fue detenido. La ignoramos para no anular
        # la referencia al nuevo grupo que ya está en curso.
        if self.sender() is not self.animation_group:
            return

        # El estado de visibilidad ya ha sido cambiado en _toggle_filter_expansion.
        if not self._filters_visible:
            self.filter_options_widget.hide()

        # El grupo de animación actual ha terminado, por lo que borramos la referencia.
        self.animation_group = None
            
if __name__ == '__main__':
    # Ejemplo de uso básico (requiere que el QApplication se ejecute)
    app = QApplication([])
    
    # Mock de FONTS para prueba si no está disponible globalmente de forma sencilla
    if 'FONTS' not in globals():
        FONTS = {"family": "Arial", "size_medium": 12, "size_large": 16, "size_small": 10}

    search_bar = SearchBarWidget()
    search_bar.setFixedWidth(300) # Darle un ancho para visualización

    def handle_search(term, filters):
        print(f"Búsqueda solicitada: Término='{term}', Filtros={filters}")

    search_bar.search_requested.connect(handle_search)
    search_bar.show()
    
    # Para probar la expansión (simulando un click)
    # import PySide6.QtCore
    # PySide6.QtCore.QTimer.singleShot(1000, lambda: search_bar._toggle_filter_expansion())
    # PySide6.QtCore.QTimer.singleShot(3000, lambda: search_bar._toggle_filter_expansion())


    test_window = QWidget()
    test_layout = QVBoxLayout(test_window)
    test_layout.addWidget(QLabel("Contenido de prueba encima de la barra de búsqueda"))
    test_layout.addWidget(search_bar)
    test_layout.addStretch()
    test_window.resize(400, 300)
    test_window.setWindowTitle("Prueba de SearchBarWidget")
    test_window.show()
    
    app.exec()
