"""
Definiciones de estilos y constantes visuales para la aplicación.

Este módulo centraliza todos los estilos, colores, fuentes y otras constantes
visuales utilizadas en la aplicación, facilitando su reutilización y 
asegurando la consistencia visual entre diferentes componentes.
"""

import os

# --- Configuración de Rutas ---
APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "app")
IMAGE_DIR = os.path.join(APP_DIR, "imagenes")
BACKGROUND_IMAGE_PATH = os.path.join(IMAGE_DIR, "fondo.png")

# --- Colores de la aplicación ---
COLORS = {
    "text_primary": "#202427",
    "text_secondary": "#505050",
    "text_disabled": "#909090",
    
    "background_transparent": "rgba(255, 255, 255, 80)",
    "background_light": "rgba(255, 255, 255, 150)",
    "background_medium": "rgba(255, 255, 255, 130)",
    
    "accent_blue": "rgba(52, 152, 219, 180)",
    "accent_blue_hover": "rgba(41, 128, 185, 200)",
    "accent_blue_pressed": "rgba(41, 128, 185, 220)",
    
    "accent_green": "rgba(46, 204, 113, 180)",
    "accent_green_hover": "rgba(39, 174, 96, 200)",
    "accent_green_pressed": "rgba(39, 174, 96, 220)",
    
    "accent_red": "rgba(231, 76, 60, 180)",
    "accent_red_hover": "rgba(192, 57, 43, 200)",
    "accent_red_pressed": "rgba(192, 57, 43, 220)",
    
    "border_light": "rgba(220, 220, 220, 70)",
    "border_medium": "rgba(200, 200, 200, 80)",
    "border_focus": "#3498db",
    "border_black" : "#b7babd",
    
    "input_background": "rgba(255, 255, 255, 100)",

    "accent_purple": "#6D28D9",
    "accent_purple_hover": "#5B21B6",
    "accent_purple_pressed": "#4C1D95",
}

# --- Fuentes ---
FONTS = {
    "family": "Montserrat",
    "family_title": "Montserrat",
    "family_fallback": "Arial",
    "size_small": 11,
    "size_normal": 13,
    "size_medium": 14,
    "size_large": 18,
    "size_xlarge": 32,
    "size_large_title": 26
}

# --- Estilos comunes ---
STYLES = {
    "frame_rounded": f"""
        background-color: {COLORS["background_transparent"]}; 
        border-radius: 15px;
        border: 1px solid {COLORS["border_light"]};
        padding: 15px;
    """,
    
    "input_field": f"""
        border: 1px solid #bdc3c7;
        border-radius: 5px;
        padding: 5px 10px;
        background-color: white;
    """,
    
    "input_field_focus": f"""
        border: 2px solid {COLORS["border_focus"]};
    """,
    
    "input_field_disabled": f"""
        background-color: rgba(200, 200, 200, 80);
        color: {COLORS["text_disabled"]};
    """,
    
    "button_primary": f"""
        background-color: {COLORS["accent_blue"]};
        color: white;
        border-radius: 5px;
        padding: 5px 15px;
        border: none;
    """,
    "button_primary:hover": f"""
        background-color: {COLORS["accent_blue_hover"]};
    """,
    "button_primary:pressed": f"""
        background-color: {COLORS["accent_blue_pressed"]};
    """,
    
    "button_success": f"""
        background-color: {COLORS["accent_green"]};
        color: white;
        border-radius: 5px;
        padding: 5px 20px;
        border: none;
    """,
    "button_success:hover": f"""
        background-color: {COLORS["accent_green_hover"]};
        # border: 1px solid {COLORS["accent_green_pressed"]}; # Comentado para prueba
    """,
    "button_success:pressed": f"""
        background-color: {COLORS["accent_green_pressed"]};
    """,
    
    "button_danger": f"""
        background-color: {COLORS["accent_red"]};
        color: white;
        border-radius: 5px;
        padding: 5px 20px;
        border: none;
    """,
    "button_danger:hover": f"""
        background-color: {COLORS["accent_red_hover"]};
        # border: 1px solid {COLORS["accent_red_pressed"]}; # Comentado para prueba
    """,
    "button_danger:pressed": f"""
        background-color: {COLORS["accent_red_pressed"]};
    """,
    
    "button_disabled": f"""
        background-color: rgba(200, 200, 200, 180);
        color: rgba(120, 120, 120, 200);
    """,

    # --- Nuevos Estilos Completos para Botones ---
    "button_primary_full": f"""
        QPushButton {{
            background-color: {COLORS["accent_blue"]};
            color: white;
            border-radius: 5px;
            padding: 5px 15px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {COLORS["accent_blue_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["accent_blue_pressed"]};
        }}
    """,
    "button_success_full": f"""
        QPushButton {{
            background-color: {COLORS["accent_green"]};
            color: white;
            border-radius: 5px;
            padding: 5px 20px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {COLORS["accent_green_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["accent_green_pressed"]};
        }}
    """,
    "button_danger_full": f"""
        QPushButton {{
            background-color: {COLORS["accent_red"]};
            color: white;
            border-radius: 5px;
            padding: 5px 20px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {COLORS["accent_red_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["accent_red_pressed"]};
        }}
    """,

    "button_secondary_full": f"""
        QPushButton {{
            background-color: {COLORS["accent_purple"]};
            color: white;
            border-radius: 8px;
            padding: 5px 15px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {COLORS["accent_purple_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {COLORS["accent_purple_pressed"]};
        }}
    """,

    "button_tertiary_full": f"""
        QPushButton {{
            background-color: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            color: #000;
            font-size: 12px;
            font-weight: 500;
            padding: 5px 10px;
        }}
        QPushButton:hover {{
            background-color: rgba(0, 0, 0, 0.08);
        }}
        QPushButton:disabled {{
            background-color: rgba(0, 0, 0, 0.02);
            color: rgba(0, 0, 0, 0.3);
        }}
    """,

    "main_menu_card_style": f"""
        QFrame#mainMenuCard {{
        background-color: rgba(255, 255, 255, 89); /* Ajustado para opacidad 0.35 */
        border-radius: 16px; /* Ajustado */
        border: 0.5px solid white; /* Ajustado */
        }}
        QFrame#mainMenuCard QLabel {{
            background-color: transparent;
            border: none;
        }}
        /* Si CustomButton necesita ser transparente:
        QFrame#mainMenuCard CustomButton {{
            background-color: transparent;
        }}*/
    """,

    "line_edit_style": f"""
        QLineEdit {{
            background-color: {COLORS['input_background']};
            border: 1px solid {COLORS['border_medium']};
            border-radius: 8px;
            padding: 10px 15px;
            font-size: {FONTS['size_normal']}px;
            color: {COLORS['text_primary']};
        }}
        QLineEdit:focus {{
            border: 1px solid {COLORS['border_focus']};
        }}
    """,

    "line_edit_total_style": f"""
        QLineEdit {{
            color: {COLORS['text_primary']};
            background-color: white;
            border: 1px solid {COLORS['border_medium']};
            border-radius: 8px;
            padding-right: 10px;
        }}
        QLineEdit:focus {{
            border: 2px solid {COLORS['border_focus']};
        }}
    """,
} 