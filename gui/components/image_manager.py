import os
import requests
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
from PySide6.QtGui import QPixmap

class ImageDownloader(QRunnable):
    """
    Worker thread for downloading an image.
    Emits the image_id and the downloaded QPixmap upon completion.
    """
    def __init__(self, image_id: str, url: str, cache_path: str):
        super().__init__()
        self.image_id = image_id
        self.url = url
        self.cache_path = cache_path
        self.signals = self._Signals()

    class _Signals(QObject):
        finished = Signal(str, QPixmap)
        failed = Signal(str)

    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=10)
            response.raise_for_status()
            
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            
            with open(self.cache_path, 'wb') as f:
                f.write(response.content)
            
            self.signals.finished.emit(self.image_id, pixmap)
        except (requests.RequestException, IOError) as e:
            print(f"Failed to download or save image for {self.image_id}: {e}")
            self.signals.failed.emit(self.image_id)


class ImageManager(QObject):
    """
    Manages asynchronous downloading and local caching of images.
    """
    image_loaded = Signal(str, QPixmap) # image_id, pixmap

    def __init__(self, cache_dir: str = "data/cache/images", parent=None):
        super().__init__(parent)
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        self.thread_pool = QThreadPool()
        self.active_downloads = set()

    def get_image(self, image_id: str, url: str):
        """
        Retrieves an image. Checks cache first, otherwise downloads.
        """
        if not image_id or not url:
            return

        cache_path = os.path.join(self.cache_dir, f"{image_id}.jpg")

        if os.path.exists(cache_path):
            pixmap = QPixmap(cache_path)
            self.image_loaded.emit(image_id, pixmap)
            return

        if image_id in self.active_downloads:
            return # Already downloading

        self.active_downloads.add(image_id)
        downloader = ImageDownloader(image_id, url, cache_path)
        downloader.signals.finished.connect(self._on_download_finished)
        downloader.signals.failed.connect(self._on_download_failed)
        self.thread_pool.start(downloader)

    def _on_download_finished(self, image_id: str, pixmap: QPixmap):
        if image_id in self.active_downloads:
            self.active_downloads.remove(image_id)
        self.image_loaded.emit(image_id, pixmap)

    def _on_download_failed(self, image_id: str):
        if image_id in self.active_downloads:
            self.active_downloads.remove(image_id)
        # Optionally, emit a signal to show a "failed" placeholder
        # self.image_failed.emit(image_id) 