from typing import Dict, Any, List
from features.utils import format_price_with_thousands_separator

class BookUI:
    """Maneja toda la salida a consola para la funcionalidad de añadir libros."""

    def mostrar_encabezado_agregar_libros(self) -> None:
        print("\n" + "=" * 50)
        print("➕ Agregar Libros")
        print("=" * 50 + "\n")

    def mostrar_datos_api(self, book_info: Dict[str, Any]) -> None:
        print("")
        print("=" * 50)
        print("\nℹ️ Datos obtenidos del libro (desde API):\n")
        api_display_info = {k: v for k, v in book_info.items() if k not in ["ISBN"]}
        for key, value in api_display_info.items():
            print(f"  {key}: {value}\n")
        print("=" * 50)
        print("")

    def mostrar_ingreso_manual_header(self) -> None:
        print("\n" + "=" * 50)
        print("⬇️ Ingresa los datos manualmente ⬇️")

    def mostrar_precio_establecido(self, precio_int: int) -> None:
        formatted_price = format_price_with_thousands_separator(precio_int)
        print(f"\n 💲 Precio del libro establecido = \033[92m$ {formatted_price}\033[0m\n")
        print("=" * 50)
        print("")

    def mostrar_libro_no_encontrado_api(self) -> None:
        print("=" * 50)
        print("\n❌ Libro no encontrado en la API.")
        print("")

    def mostrar_ingreso_precio_cancelado(self) -> None:
        print("\n❌ Ingreso de precio cancelado.")

    def mostrar_operacion_cancelada(self) -> None:
        print("\n⚠️ Operación cancelada.")

    def mostrar_volviendo_con_pausa(self) -> None:
        input("\nPress Enter para regresar...")

    def mostrar_adicion_libro_cancelada_por_posicion(self) -> None:
        input("\nPress Enter para regresar...")

    def mostrar_libro_anadido_correctamente(self) -> None:
        print("\nLibro añadido correctamente. ℹ️")

    def mostrar_proceso_finalizado(self) -> None:
        print("\n✅ Proceso de añadir libros finalizado.")

    def mostrar_error_guardar_master_book_info(self, isbn: str, error: Exception) -> None:
        print(f"\n❌ Error inesperado al intentar guardar datos maestros para ISBN {isbn} en 'libros': {error}")

    def mostrar_master_book_info_guardado(self, isbn: str) -> None:
        print(f"\n✅ Datos maestros para ISBN {isbn} guardados en la tabla 'libros'.")

    def mostrar_master_book_info_existente(self, isbn: str) -> None:
        print(f"\nℹ️ Datos maestros para ISBN {isbn} ya existen en la tabla 'libros'. No se modificaron.")

    def mostrar_error_guardar_inventario(self, isbn: str, posicion: str, error: Exception) -> None:
        print(f"\n❌ Error general al guardar/actualizar en inventario para ISBN {isbn}, Posición {posicion}: {error}")

    def mostrar_inventario_incrementado(self, isbn: str, posicion: str, nueva_cantidad: int) -> None:
        print(f"\nℹ️ Libro existente en inventario (ISBN: {isbn}, Posición: {posicion}). Cantidad incrementada a {nueva_cantidad}.")

    def mostrar_inventario_incrementado_sin_cantidad(self, isbn: str, posicion: str) -> None:
        print(f"\nℹ️ Libro existente en inventario (ISBN: {isbn}, Posición: {posicion}). Cantidad incrementada. No se pudo verificar nueva cantidad.")

    def mostrar_warning_fetch_query(self, data_manager_type_name: str) -> None:
        print(f"\n⚠️ {data_manager_type_name} no tiene el método 'fetch_query'. La cantidad fue incrementada, pero no se puede mostrar el nuevo total.")

    def mostrar_inventario_actualizado_msg_base(self, isbn: str, posicion: str) -> None:
        print(f"\n✅ Inventario actualizado para ISBN {isbn} en posición {posicion}.")

    def mostrar_nuevo_libro_inventario(self, isbn: str, posicion: str) -> None:
        print(f"\nℹ️ Nuevo libro agregado al inventario (ISBN: {isbn}, Posición: {posicion}). Cantidad: 1.")

    def mostrar_error_agregar_nuevo_inventario(self, isbn: str, posicion: str) -> None:
        print(f"\n⚠️ No se pudo agregar el nuevo libro al inventario (ISBN: {isbn}, Posición: {posicion}) o ya existía y el update previo falló en detectarlo.")
