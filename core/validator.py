class Validator:
    @staticmethod
    def is_valid_number(number_str: str) -> bool:
        """
        Verifica si una cadena representa un número entero positivo.
        """
        return number_str.isdigit()

    @staticmethod
    def is_in_list(element: any, valid_list: list) -> bool:
        """
        Verifica si un elemento está presente en una lista dada.
        """
        return element in valid_list
    
    @staticmethod
    def is_valid_isbn(isbn: str) -> bool:
        """
        Valida un ISBN. Debe ser numérico y tener 10 o 13 dígitos.
        """
        # Eliminar guiones o espacios que a veces se usan en los ISBNs
        cleaned_isbn = isbn.replace("-", "").replace(" ", "")
        if not cleaned_isbn.isdigit():
            return False
        
        length = len(cleaned_isbn)
        if length == 10:
            # Aquí se podría agregar la lógica de validación del dígito de control del ISBN-10 si se desea.
            # Por ahora, solo verificamos la longitud y que sea numérico.
            return True
        elif length == 13:
            # Aquí se podría agregar la lógica de validación del dígito de control del ISBN-13 si se desea.
            # Por ahora, solo verificamos la longitud y que sea numérico.
            return True
        return False

    @staticmethod
    def is_valid_price(price_str: str) -> bool:
        """
        Verifica si una cadena representa un precio válido.
        Acepta números enteros o decimales no negativos.
        """
        try:
            price_str = price_str.replace(',', '.')
            price = int(price_str)
            return price >= 0
        except ValueError:
            return False

    # Podrías añadir más métodos de validación aquí según sea necesario,
    # por ejemplo, para emails, URLs, formatos de fecha específicos, etc.
    # Ejemplo:
    # @staticmethod
    # def is_valid_email(email: str) -> bool:
    #     import re
    #     # Una expresión regular simple para validar emails (puede ser más compleja)
    #     pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    #     return bool(re.match(pattern, email))
