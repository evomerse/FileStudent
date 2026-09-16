"""Module Amelioration d'image (ticket APP-10, etendu equivalent iLoveIMG).

Filtres classiques, redimensionnement, rotation, filigrane texte et
upscaling algorithmique (Lanczos). Pas de modele d'IA : voir le backlog
pour la version avancee (suppression d'arriere-plan, upscaling par IA).
"""

from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from filestudent.core.file_types import FileKind, detect_file_kind
from filestudent.core.output import sibling_path
from filestudent.core.result import Result

FILTERS = {
    "Aucun": lambda img: img,
    "Nettete": lambda img: ImageEnhance.Sharpness(img).enhance(1.8),
    "Contraste": lambda img: ImageEnhance.Contrast(img).enhance(1.3),
    "Luminosite": lambda img: ImageEnhance.Brightness(img).enhance(1.15),
    "Niveaux de gris": lambda img: img.convert("L").convert("RGB"),
    "Reduction de bruit": lambda img: img.filter(ImageFilter.MedianFilter(size=3)),
}

UPSCALE_FACTORS = {"x1": 1, "x2": 2, "x4": 4}

RESIZE_MODES = {
    "Aucun": None,
    "50 %": 0.5,
    "75 %": 0.75,
    "150 %": 1.5,
    "200 %": 2.0,
    "Largeur 800 px": 800,
    "Largeur 1200 px": 1200,
    "Largeur 1920 px": 1920,
}

ROTATE_ANGLES = {"0": 0, "90": -90, "180": 180, "270": 90}


def _crop(img: Image.Image, percent: float) -> Image.Image:
    if percent <= 0:
        return img
    dx = int(img.width * percent / 100)
    dy = int(img.height * percent / 100)
    return img.crop((dx, dy, img.width - dx, img.height - dy))


def _parse_custom_size(spec: str) -> tuple[int, int] | None:
    spec = spec.strip().lower().replace(" ", "")
    if not spec:
        return None
    if "x" not in spec:
        raise ValueError(f"Dimensions invalides : {spec} (format attendu : 800x600)")
    w_text, _, h_text = spec.partition("x")
    try:
        width, height = int(w_text), int(h_text)
    except ValueError as exc:
        raise ValueError(f"Dimensions invalides : {spec} (format attendu : 800x600)") from exc
    if width <= 0 or height <= 0:
        raise ValueError(f"Dimensions invalides : {spec} (doivent etre positives)")
    return width, height


def _resize(img: Image.Image, mode: str) -> Image.Image:
    value = RESIZE_MODES.get(mode)
    if value is None:
        return img
    if isinstance(value, float):
        w, h = int(img.width * value), int(img.height * value)
    else:
        ratio = value / img.width
        w, h = value, int(img.height * ratio)
    return img.resize((max(1, w), max(1, h)), Image.Resampling.LANCZOS)


def _watermark(img: Image.Image, text: str) -> Image.Image:
    if not text.strip():
        return img
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    fontsize = max(16, img.width // 18)
    font = None
    candidates = ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf")
    for candidate in candidates:
        try:
            font = ImageFont.truetype(candidate, fontsize)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = (img.width - tw) / 2, (img.height - th) / 2
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 110))
    return Image.alpha_composite(img, overlay).convert("RGB")


def run(
    files: list[str],
    filter_name: str = "Aucun",
    upscale: str = "x1",
    resize: str = "Aucun",
    custom_size: str = "",
    crop_percent: int = 0,
    rotate: str = "0",
    watermark_text: str = "",
    **_options: Any,
) -> Result:
    if filter_name not in FILTERS:
        raise ValueError(f"Filtre inconnu : {filter_name}")
    if upscale not in UPSCALE_FACTORS:
        raise ValueError(f"Facteur d'agrandissement inconnu : {upscale}")
    if resize not in RESIZE_MODES:
        raise ValueError(f"Mode de redimensionnement inconnu : {resize}")
    if rotate not in ROTATE_ANGLES:
        raise ValueError(f"Angle de rotation inconnu : {rotate}")
    target_size = _parse_custom_size(custom_size)
    crop_percent = max(0, min(45, int(crop_percent)))

    factor = UPSCALE_FACTORS[upscale]
    created: list[str] = []
    notes: list[str] = []

    for path in files:
        if detect_file_kind(path) != FileKind.IMAGE:
            notes.append(f"{path} : ignore (pas une image).")
            continue

        with Image.open(path) as img:
            img = img.convert("RGB")
            img = FILTERS[filter_name](img)
            if ROTATE_ANGLES[rotate]:
                img = img.rotate(ROTATE_ANGLES[rotate], expand=True)
            img = _crop(img, crop_percent)
            img = _resize(img, resize)
            if factor != 1:
                img = img.resize(
                    (img.width * factor, img.height * factor), Image.Resampling.LANCZOS
                )
            if target_size is not None:
                img = img.resize(target_size, Image.Resampling.LANCZOS)
            img = _watermark(img, watermark_text)

            out = sibling_path(path, suffix="_ameliore")
            img.save(out)
            created.append(out)

    if not created:
        detail = "\n".join(notes) if notes else "aucune image exploitable."
        raise ValueError(f"Aucun fichier produit.\n{detail}")

    message = "\n".join(created)
    if notes:
        message += "\n\nA noter :\n" + "\n".join(notes)
    return Result(message=message, paths=created)
