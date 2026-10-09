"""
Generates simple, original flat-icon SVG illustrations for each clothing
category (t-shirt, shirt, polo, jeans, pants, hoodie, jacket), tinted to
match the product's actual color. Used instead of stock photography so
product images never show a real person or animal — every image here is a
generic, hand-drawn garment silhouette rendered on a clean neutral card
background, generated locally (no external network call at all).

Returned as a `data:image/svg+xml` URI so it drops straight into the
existing `products.image` URL column with no extra static-file serving.
"""
import urllib.parse


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def _shade(hex_color: str, factor: float) -> str:
    """factor < 1 darkens, factor > 1 lightens (toward white)."""
    r, g, b = _hex_to_rgb(hex_color)
    if factor < 1:
        r, g, b = r * factor, g * factor, b * factor
    else:
        r = r + (255 - r) * (factor - 1)
        g = g + (255 - g) * (factor - 1)
        b = b + (255 - b) * (factor - 1)
    return _rgb_to_hex((r, g, b))


COLOR_HEX = {
    "Black": "#232323", "White": "#f4f2ee", "Navy": "#1b2a4a", "Red": "#a5281f",
    "Blue": "#2f5aa8", "Green": "#2f6b3c", "Grey": "#8a8a8a", "Maroon": "#6b1f2a",
    "Beige": "#cdb896", "Olive": "#5c5c34",
}
_DEFAULT_HEX = "#3a3a3a"

_CARD_BG = "#e9e6df"
_CARD_BG2 = "#dedad2"


def _wrap(inner: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500">'
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{_CARD_BG}"/>'
        f'<stop offset="1" stop-color="{_CARD_BG2}"/>'
        "</linearGradient></defs>"
        '<rect width="400" height="500" fill="url(#bg)"/>'
        '<ellipse cx="200" cy="405" rx="115" ry="15" fill="#00000014"/>'
        f"{inner}</svg>"
    )


def _tshirt(fill: str) -> str:
    dark, light = _shade(fill, 0.70), _shade(fill, 1.30)
    body = ("M176,104 Q200,132 224,104 L250,110 L305,140 L320,175 L260,195 "
            "L260,340 L140,340 L140,195 L80,175 L95,140 L150,110 Z")
    return (
        f'<path d="{body}" fill="{fill}" stroke="{dark}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M140,205 L140,330" stroke="{dark}" stroke-width="2.5" opacity="0.35"/>'
        f'<path d="M260,205 L260,330" stroke="{light}" stroke-width="2.5" opacity="0.45"/>'
        f'<path d="M150,110 L140,195" stroke="{light}" stroke-width="2" opacity="0.4"/>'
        f'<path d="M250,110 L260,195" stroke="{dark}" stroke-width="2" opacity="0.3"/>'
    )


def _shirt(fill: str) -> str:
    dark, light = _shade(fill, 0.70), _shade(fill, 1.30)
    body = ("M176,104 L200,158 L224,104 L250,110 L305,140 L320,175 L260,195 "
            "L260,360 L140,360 L140,195 L80,175 L95,140 L150,110 Z")
    buttons = "".join(
        f'<circle cx="200" cy="{y}" r="3.5" fill="{dark}" opacity="0.65"/>'
        for y in (175, 210, 245, 280, 315, 350)
    )
    return (
        f'<path d="{body}" fill="{fill}" stroke="{dark}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M200,158 L200,358" stroke="{dark}" stroke-width="2.5" opacity="0.4"/>'
        f"{buttons}"
        f'<path d="M150,110 L140,195" stroke="{light}" stroke-width="2" opacity="0.4"/>'
        f'<path d="M250,110 L260,195" stroke="{dark}" stroke-width="2" opacity="0.3"/>'
    )


def _polo(fill: str) -> str:
    dark, light = _shade(fill, 0.70), _shade(fill, 1.30)
    body = ("M182,104 L200,138 L218,104 L250,112 L302,142 L316,175 L260,195 "
            "L260,340 L140,340 L140,195 L84,175 L98,142 L150,112 Z")
    return (
        f'<path d="{body}" fill="{fill}" stroke="{dark}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M200,138 L200,178" stroke="{dark}" stroke-width="2.5" opacity="0.45"/>'
        f'<circle cx="200" cy="152" r="3" fill="{dark}" opacity="0.6"/>'
        f'<circle cx="200" cy="172" r="3" fill="{dark}" opacity="0.6"/>'
        f'<path d="M150,112 L140,195" stroke="{light}" stroke-width="2" opacity="0.4"/>'
        f'<path d="M250,112 L260,195" stroke="{dark}" stroke-width="2" opacity="0.3"/>'
    )


def _jeans(fill: str) -> str:
    dark, light = _shade(fill, 0.66), _shade(fill, 1.24)
    body = ("M142,92 L258,92 L266,175 L292,404 L234,404 L204,222 L196,222 "
            "L166,404 L108,404 L134,175 Z")
    return (
        f'<path d="{body}" fill="{fill}" stroke="{dark}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M142,92 L258,92 L260,118 L140,118 Z" fill="{dark}" opacity="0.32"/>'
        f'<path d="M200,118 L202,222" stroke="{dark}" stroke-width="3" opacity="0.5"/>'
        f'<path d="M172,150 L166,404" stroke="{light}" stroke-width="2.5" opacity="0.5"/>'
        f'<path d="M228,150 L234,404" stroke="{light}" stroke-width="2.5" opacity="0.5"/>'
        f'<rect x="160" y="100" width="18" height="14" rx="2" fill="none" stroke="{dark}" stroke-width="2" opacity="0.5"/>'
    )


def _pants(fill: str) -> str:
    dark, light = _shade(fill, 0.70), _shade(fill, 1.24)
    body = ("M146,94 L254,94 L262,175 L284,402 L230,402 L200,218 L196,218 "
            "L170,402 L116,402 L138,175 Z")
    return (
        f'<path d="{body}" fill="{fill}" stroke="{dark}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M146,94 L254,94 L256,116 L144,116 Z" fill="{dark}" opacity="0.28"/>'
        f'<path d="M200,116 L198,218" stroke="{dark}" stroke-width="2.5" opacity="0.4"/>'
        f'<path d="M176,150 L170,402" stroke="{light}" stroke-width="2" opacity="0.35"/>'
        f'<path d="M224,150 L230,402" stroke="{light}" stroke-width="2" opacity="0.35"/>'
    )


def _hoodie(fill: str) -> str:
    dark, light = _shade(fill, 0.68), _shade(fill, 1.28)
    hood = "M150,132 Q145,80 200,76 Q255,80 250,132 L226,124 Q200,148 174,124 Z"
    body = ("M176,120 Q200,146 224,120 L250,126 L305,150 L320,182 L260,202 "
            "L260,340 L140,340 L140,202 L80,182 L95,150 L150,126 Z")
    pocket = "M162,255 L238,255 L246,300 L154,300 Z"
    return (
        f'<path d="{body}" fill="{fill}" stroke="{dark}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="{hood}" fill="{fill}" stroke="{dark}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="{pocket}" fill="{dark}" opacity="0.22" stroke="{dark}" stroke-width="2.5" stroke-opacity="0.55"/>'
        f'<path d="M150,126 L140,202" stroke="{light}" stroke-width="2" opacity="0.4"/>'
        f'<path d="M250,126 L260,202" stroke="{dark}" stroke-width="2" opacity="0.3"/>'
        f'<circle cx="184" cy="145" r="2.5" fill="{dark}" opacity="0.6"/>'
        f'<circle cx="216" cy="145" r="2.5" fill="{dark}" opacity="0.6"/>'
    )


def _jacket(fill: str) -> str:
    dark, light = _shade(fill, 0.66), _shade(fill, 1.28)
    left = "M150,110 L196,150 L192,360 L138,360 L138,195 L80,178 L96,146 Z"
    right = "M250,110 L204,150 L208,360 L262,360 L262,195 L320,178 L304,146 Z"
    return (
        f'<path d="{left}" fill="{fill}" stroke="{dark}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="{right}" fill="{fill}" stroke="{dark}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M150,110 L138,195" stroke="{light}" stroke-width="2" opacity="0.4"/>'
        f'<path d="M250,110 L262,195" stroke="{dark}" stroke-width="2" opacity="0.3"/>'
        f'<rect x="150" y="255" width="32" height="20" rx="3" fill="none" stroke="{dark}" stroke-width="2.5" opacity="0.6"/>'
        f'<rect x="218" y="255" width="32" height="20" rx="3" fill="none" stroke="{dark}" stroke-width="2.5" opacity="0.6"/>'
    )


_BUILDERS = {
    "T-Shirts": _tshirt,
    "Shirts": _shirt,
    "Polo Shirts": _polo,
    "Jeans": _jeans,
    "Pants": _pants,
    "Hoodies": _hoodie,
    "Jackets": _jacket,
}


def product_image_data_uri(category: str, color_name: str | None) -> str:
    """Builds a self-contained data: URI SVG product icon for the given
    category, tinted with the product's own color. Never depends on any
    external image/network — safe, deterministic, and guaranteed to never
    show a real person, model, or animal."""
    fill = COLOR_HEX.get(color_name, _DEFAULT_HEX)
    builder = _BUILDERS.get(category, _tshirt)
    svg = _wrap(builder(fill))
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)
