import os # Para construir la ruta del icono/fondo
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QWidget, QGraphicsBlurEffect
from PySide6.QtCore import Qt, Signal, QPoint, QTimer, QEvent # QPoint para paintEvent, QTimer y QEvent para inactividad
from PySide6.QtGui import QIcon, QPainter, QPixmap, QMouseEvent # QPainter y QPixmap para paintEvent

from gui.components.paginated_results_widget import PaginatedResultsWidget
from gui.common.styles import FONTS

# Asumimos que la imagen de fondo está en app/imagenes/
# Construir la ruta de forma más robusta para el fondo
try:
    CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # Navegar dos niveles arriba desde gui/dialogs/ para llegar a la raíz del proyecto LibraryAPP
    # luego entrar a app/imagenes/
    BACKGROUND_IMAGE_SEARCH_PATH = os.path.join(os.path.dirname(os.path.dirname(CURRENT_SCRIPT_DIR)), "app", "imagenes", "fondo_buscar.png")
except NameError: # Fallback si __file__ no está definido (ej. algunos entornos interactivos)
    BACKGROUND_IMAGE_SEARCH_PATH = os.path.join("app", "imagenes", "fondo_buscar.png")

class SearchResultsWindow(QDialog):
    """
    Una ventana de diálogo para mostrar los resultados de búsqueda paginados.
    """
    INACTIVITY_TIMEOUT_MS_RESULTS = 120000 # 2 minutos para la ventana de resultados

    def __init__(self, libros_encontrados: list, termino_busqueda: str, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle(f"Resultados de búsqueda para: '{termino_busqueda}'")
        
        # Flags para ventana sin bordes y fondo translúcido
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Para la funcionalidad de arrastre
        self._drag_pos = QPoint()
        # Consideraremos la parte superior del PaginatedResultsWidget o un área del diálogo
        # El PaginatedResultsWidget tiene un search_term_label, tomemos una altura que lo incluya.
        self.title_bar_height = 60 # Ajustar según sea necesario (incluye el search_term_label y un poco más)

        self.setMinimumSize(800, 750) # Aumentada la altura mínima a 750px
        # El fondo del diálogo se hace transparente por WA_TranslucentBackground
        # y el paintEvent comentado. El PaginatedResultsWidget ya es transparente.
        # self.setStyleSheet("QDialog { background-color: transparent; }") # Ya no es necesario con WA_TranslucentBackground

        # self.background_pixmap = QPixmap(BACKGROUND_IMAGE_SEARCH_PATH)
        # if self.background_pixmap.isNull():
        #     print(f"ADVERTENCIA: No se pudo cargar la imagen de fondo para SearchResultsWindow desde: {BACKGROUND_IMAGE_SEARCH_PATH}")
        #     # self.setStyleSheet("QDialog { background-color: #e0e0e0; }") 

        self._blur_effect = None
        if self.parent():
            self._blur_effect = QGraphicsBlurEffect()
            self._blur_effect.setBlurRadius(15)
            self._blur_effect.setEnabled(False)
            if hasattr(self.parent(), 'centralWidget') and self.parent().centralWidget():
                 self.parent().centralWidget().setGraphicsEffect(self._blur_effect)
            elif hasattr(self.parent(), 'current_stacked_widget') and self.parent().current_stacked_widget:
                 self.parent().current_stacked_widget.setGraphicsEffect(self._blur_effect)
            else:
                print("Advertencia: SearchResultsWindow no pudo encontrar un widget central en el padre para aplicar el desenfoque.")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        self.results_widget = PaginatedResultsWidget()
        # Hacer el fondo del PaginatedResultsWidget transparente también
        self.results_widget.setStyleSheet("QWidget { background-color: transparent; }") 
        self.results_widget.update_results(libros_encontrados, termino_busqueda)
        
        # Conectar la señal de "volver al menú" del PaginatedResultsWidget para cerrar este diálogo
        self.results_widget.back_to_menu_requested.connect(self.accept) # o self.close

        self.layout.addWidget(self.results_widget)
        
        # Podríamos añadir un botón de cerrar explícito si se desea, 
        # aunque el de "Volver" del PaginatedResultsWidget ya cumple esa función.
        # self.close_button = QPushButton("Cerrar")
        # self.close_button.setFont(QFont(FONTS.get("family"), FONTS.get("size_normal")))
        # self.close_button.clicked.connect(self.accept)
        # self.layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignRight)

        self.setModal(False) # Para que no bloquee la ventana principal si es necesario

        # Temporizador de inactividad para esta ventana de resultados
        self.results_inactivity_timer = QTimer(self)
        self.results_inactivity_timer.setInterval(self.INACTIVITY_TIMEOUT_MS_RESULTS)
        self.results_inactivity_timer.timeout.connect(self._handle_results_inactivity)
        self.results_inactivity_timer.start()

        # Instalar filtro de eventos en el widget de resultados para detectar actividad
        # ya que es el componente principal con el que interactúa el usuario aquí.
        if self.results_widget:
            self.results_widget.installEventFilter(self)

    def _handle_results_inactivity(self):
        """Maneja la inactividad específica de la ventana de resultados."""
        print(f"Cerrando {self.windowTitle()} por inactividad.")
        self.accept() # O self.close(), accept() es común para diálogos

    def eventFilter(self, obj, event: QEvent):
        # Reinicia el temporizador de inactividad de esta ventana
        # si la actividad ocurre en el results_widget
        if obj == self.results_widget and event.type() in [
            QEvent.Type.MouseMove,
            QEvent.Type.KeyPress,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.Wheel # Añadir eventos de rueda del ratón
        ]:
            if self.results_inactivity_timer.isActive():
                self.results_inactivity_timer.start(self.INACTIVITY_TIMEOUT_MS_RESULTS)
        
        return super().eventFilter(obj, event)

    def _enable_blur(self, enable: bool):
        if self.parent() and self._blur_effect:
            self._blur_effect.setEnabled(enable)
            if hasattr(self.parent(), 'centralWidget') and self.parent().centralWidget():
                self.parent().centralWidget().update()
            elif hasattr(self.parent(), 'current_stacked_widget') and self.parent().current_stacked_widget:
                self.parent().current_stacked_widget.update()

    def showEvent(self, event):
        """Se llama cuando la ventana está a punto de mostrarse."""
        super().showEvent(event)
        if self.parent():
            self._enable_blur(True)

    # Si se usa exec() en lugar de show(), estos métodos son más apropiados para el blur
    def exec(self):
        if self.parent():
            self._enable_blur(True)
        result = super().exec()
        if self.parent():
            self._enable_blur(False)
        return result

    def accept(self):
        if self.parent():
            self._enable_blur(False)
        super().accept()

    def reject(self):
        if self.parent():
            self._enable_blur(False)
        super().reject()
    
    def closeEvent(self, event):
        if self.parent():
            self._enable_blur(False)
        super().closeEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < self.title_bar_height:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event) # Pasar a PaginatedResultsWidget si no es para arrastrar

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event) 

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = QPoint()
        # No llamar a event.accept() aquí necesariamente, permitir que el evento se propague si es necesario.
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """Maneja el evento de pintar para dibujar el fondo."""
        # Comentado para permitir fondo transparente
        # painter = QPainter(self)
        # if not self.background_pixmap.isNull():
        #     scaled_pixmap = self.background_pixmap.scaled(
        #         self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        #     point = QPoint(0, 0)
        #     if scaled_pixmap.width() > self.width():
        #         point.setX(int((scaled_pixmap.width() - self.width()) / -2))
        #     if scaled_pixmap.height() > self.height():
        #         point.setY(int((scaled_pixmap.height() - self.height()) / -2))
        #     painter.drawPixmap(point, scaled_pixmap)
        # else:
        #     painter.fillRect(self.rect(), Qt.GlobalColor.lightGray) 
        super().paintEvent(event)

    def keyPressEvent(self, event):
        """Maneja los eventos de teclado para la navegación por páginas y Esc."""
        if event.key() == Qt.Key_Escape:
            self.accept() # Cierra el diálogo
        elif event.key() == Qt.Key_Right:
            if hasattr(self.results_widget, '_ir_a_pagina_siguiente_resultados'):
                self.results_widget._ir_a_pagina_siguiente_resultados()
        elif event.key() == Qt.Key_Left:
            if hasattr(self.results_widget, '_ir_a_pagina_anterior_resultados'):
                self.results_widget._ir_a_pagina_anterior_resultados()
        else:
            super().keyPressEvent(event) # Importante para otros manejos de teclas

    def update_content(self, libros_encontrados: list, termino_busqueda: str):
        """Actualiza los resultados mostrados en la ventana."""
        self.setWindowTitle(f"Resultados de búsqueda para: '{termino_busqueda}'")
        self.results_widget.update_results(libros_encontrados, termino_busqueda)

if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    # Ejemplo de uso (requiere QApplication)
    app = QApplication(sys.argv)
    
    # Mock de datos para prueba
    mock_libros = [
        {"titulo": "Libro de Prueba 1", "autor": "Autor Uno", "isbn": "12345", "publicacion": "2023", "genero": "Ficción", "cantidad": 5, "precio": "19.99"},
        {"titulo": "Libro de Prueba 2", "autor": "Autor Dos", "isbn": "67890", "publicacion": "2022", "genero": "No Ficción", "cantidad": 3, "precio": "25.50"}
    ]
    
    if 'FONTS' not in globals(): # Mock FONTS si es necesario
        FONTS = {"family": "Arial", "size_normal": 12}


    dialog = SearchResultsWindow(mock_libros, "prueba")
    dialog.show()
    
    sys.exit(app.exec()) 