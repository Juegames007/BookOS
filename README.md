# BookOS - Sistema de Gestión de Librería

Este es un sistema de gestión para pequeñas librerías, diseñado para manejar inventario, ventas, reservas y finanzas de manera eficiente.

## Reglas de Negocio Clave

### Devoluciones

Para que una devolución sea aceptada, deben cumplirse las siguientes condiciones estrictas:

1.  **Plazo de Devolución:** La devolución solo puede procesarse si la venta original del artículo se realizó dentro de los **últimos 30 días**. No se aceptarán devoluciones para ventas con más de 30 días de antigüedad.

2.  **Existencia del Artículo:** El artículo a devolver (específicamente libros con ISBN) debe estar registrado en la base de datos. Esto significa que debe existir una entrada para él en la tabla `libros` y en la tabla `inventario`, incluso si su cantidad en inventario es cero.

3.  **Seguimiento de Artículos:**
    *   **Libros (con ISBN):** Se someten a un estricto seguimiento de inventario. Una devolución exitosa incrementará la cantidad del libro correspondiente en el inventario.
    *   **Discos y Promociones:** No tienen seguimiento de inventario. Se pueden devolver sin restricciones de cantidad o existencia previa, ya que se consideran artículos genéricos.

4.  **Impacto Financiero:** Toda devolución se registra como un **egreso** en las finanzas del negocio, ya que representa una salida de dinero para reembolsar al cliente. El monto del egreso será igual al precio de venta base del artículo en la tabla `libros`. 