import unicodedata

def format_price_with_thousands_separator(price_val: any) -> str:
    """Formatea un valor numérico (entero) con separadores de miles.
    Ejemplo: 10000 -> "10.000"
    Ejemplo: "12345" -> "12.345"
    """
    try:
        # Intentar convertir a entero si es una cadena
        if isinstance(price_val, str):
            # Eliminar puntos o comas existentes para asegurar conversión limpia a int
            # Esto es por si la cadena ya viene con algún formato no deseado
            cleaned_price_str = price_val.replace('.', '').replace(',', '')
            # Tomar solo la parte antes de un posible decimal si el usuario lo ingresó accidentalmente
            if '.' in cleaned_price_str:
                 cleaned_price_str = cleaned_price_str.split('.')[0]
            if ',' in cleaned_price_str: # Para el caso "1,000" como entrada
                 cleaned_price_str = cleaned_price_str.split(',')[0]

            # Verificar si después de limpiar, es un número válido
            if not cleaned_price_str.isdigit() and not (cleaned_price_str.startswith('-') and cleaned_price_str[1:].isdigit()):
                return str(price_val) # Devolver original si no es un número limpio
            
            num_int = int(cleaned_price_str)
        elif isinstance(price_val, (int, float)):
            num_int = int(price_val) # Truncar float a int
        else:
            return str(price_val) # Devolver como cadena si no es un tipo esperado

        # Formatear el entero con comas y luego reemplazar por puntos
        return f"{num_int:,}".replace(',', '.')
    except (ValueError, TypeError):
        # En caso de cualquier error de conversión o tipo, devolver el valor original como cadena
        return str(price_val)

def normalize_for_search(text: str) -> str:
    """
    Normaliza un texto para búsquedas: lo convierte a minúsculas y elimina tildes.
    Ej: "Arcángeles" -> "arcangeles"
    """
    if not isinstance(text, str):
        return ""
    # NFD (Normalization Form D) descompone los caracteres en su base + acentos
    nfkd_form = unicodedata.normalize('NFD', text.lower())
    # Se eliminan los caracteres que son acentos (combinados)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
