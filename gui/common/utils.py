def format_price(price: float) -> str:
    """
    Formatea un número flotante como una cadena de texto de precio
    con separadores de miles y sin decimales.
    Ej: 10000.0 -> "10.000"
    """
    if price is None:
        price = 0
    try:
        return f"{int(price):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "0" 