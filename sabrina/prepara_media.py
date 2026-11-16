#!/usr/bin/env python3
"""
Prepara foto e video per il sito di Sabrina.

COME SI USA
1. Crea una cartella "foto_originali" accanto a questo file e mettici foto e video
   (nell'ordine in cui vuoi vederli sul filo: rinominali 01_..., 02_..., ecc.).
2. Scrivi le frasi in "frasi.txt", una per riga, nello stesso ordine.
3. Installa le librerie:   pip install pillow
   (per i video serve anche ffmpeg installato sul computer, altrimenti vengono copiati così come sono)
4. Lancia:   python prepara_media.py
5. Apri index.html: troverai "media_config.js" e la cartella "media" già pronti.

Cosa fa:
- raddrizza le foto (orientamento del telefono), le ritaglia quadrate e dà un tono caldo e vintage
- comprime i video (max 30 secondi, 720p) per far caricare il sito velocemente
- collega a ogni foto/video la sua frase e crea media_config.js
"""
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

SRC = Path("foto_originali")
OUT = Path("media")
FRASI = Path("frasi.txt")

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
VID_EXT = {".mp4", ".mov", ".m4v", ".webm"}


def tono_caldo(im: Image.Image) -> Image.Image:
    """Colori leggermente più caldi, come una polaroid."""
    im = ImageEnhance.Color(im).enhance(1.06)
    im = ImageEnhance.Contrast(im).enhance(1.04)
    r, g, b = im.split()
    r = r.point(lambda v: min(255, int(v * 1.05)))
    b = b.point(lambda v: int(v * 0.94))
    return Image.merge("RGB", (r, g, b))


def prepara_foto(src: Path, dst: Path) -> None:
    im = Image.open(src)
    im = ImageOps.exif_transpose(im).convert("RGB")
    # ritaglio 4:5, un po' spostato verso l'alto per tenere i volti
    im = ImageOps.fit(im, (900, 1125), Image.LANCZOS, centering=(0.5, 0.3))
    tono_caldo(im).save(dst, "JPEG", quality=88, optimize=True)


def prepara_video(src: Path, dst: Path) -> None:
    if shutil.which("ffmpeg"):
        cmd = [
            "ffmpeg", "-y", "-i", str(src), "-t", "30",
            "-vf", "scale='min(720,iw)':-2",
            "-c:v", "libx264", "-crf", "28", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(dst),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print(f"  (ffmpeg non trovato: copio {src.name} senza comprimerlo)")
        shutil.copy(src, dst)


def main() -> None:
    if not SRC.exists():
        SRC.mkdir()
        print(f"Ho creato la cartella '{SRC}'. Mettici dentro foto e video e rilancia lo script.")
        return

    files = sorted(p for p in SRC.iterdir() if p.suffix.lower() in IMG_EXT | VID_EXT)
    if not files:
        print(f"Nessun file in '{SRC}'.")
        return

    frasi = []
    if FRASI.exists():
        frasi = [r.strip() for r in FRASI.read_text(encoding="utf-8").splitlines() if r.strip()]

    OUT.mkdir(exist_ok=True)
    items = []
    for i, f in enumerate(files, start=1):
        is_video = f.suffix.lower() in VID_EXT
        nome = f"{'video' if is_video else 'foto'}_{i:02d}" + (".mp4" if is_video else ".jpg")
        dst = OUT / nome
        print(f"[{i}/{len(files)}] {f.name} -> {dst}")
        (prepara_video if is_video else prepara_foto)(f, dst)
        didascalia = frasi[i - 1] if i - 1 < len(frasi) else "♥"
        items.append({
            "type": "video" if is_video else "photo",
            "src": dst.as_posix(),
            "caption": didascalia,
        })

    Path("media_config.js").write_text(
        "window.MEDIA = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"\nFatto! {len(items)} ricordi pronti. Apri index.html.")


if __name__ == "__main__":
    main()
