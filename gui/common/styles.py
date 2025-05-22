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
    "background_light": "rgba(248, 249, 250, 100)",
    "background_medium": "rgba(240, 240, 240, 80)",
    
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
    "border_focus": "#3498db"
}

# --- Fuentes ---
FONTS = {
    "family": "San Francisco",
    "family_title": "Roboto",
    "family_fallback": "Arial",
    "size_small": 10,
    "size_normal": 11,
    "size_medium": 12,
    "size_large": 16,
    "size_xlarge": 30,
    "size_large_title": 24
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
} 