"""Build a silent, captioned overview from real application screenshots."""
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
FRAMES = Path('/tmp/autostock-video-frames')
FRAMES.mkdir(exist_ok=True)
OUT = ROOT / 'dist/video'
OUT.mkdir(exist_ok=True)
INK = '#172538'
MUTED = '#526070'
ACCENT = '#a43725'
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'

def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)

def paragraph(draw, text, xy, size=30, width=570, fill=INK, bold=False):
    x, y = xy
    face = font(size, bold)
    for source_line in text.split('\n'):
        words = source_line.split()
        line = ''
        for word in words:
            candidate = f'{line} {word}'.strip()
            if draw.textlength(candidate, font=face) > width and line:
                draw.text((x, y), line, font=face, fill=fill)
                y += round(size * 1.42)
                line = word
            else:
                line = candidate
        draw.text((x, y), line, font=face, fill=fill)
        y += round(size * 1.42)
    return y

scenes = [
    (7, 'LE PROJET', 'Auto Stock\nManagement',
     'Une application pour un magasin de pièces détachées.',
     'Suivre le stock, les ventes et les règlements des clients.',
     'tableau-de-bord.png'),
    (11, '01 / STOCK', 'Retrouver les pièces\net leurs quantités.',
     'Un import CSV a créé deux références et réceptionné 36 unités.',
     'Après la vente de deux filtres : 18 filtres et 16 plaquettes en stock.',
     'catalogue.png'),
    (12, '02 / VENTE ET RÈGLEMENTS', 'Un paiement partiel,\nun solde à suivre.',
     'Deux filtres à 5 000 FCFA : une vente de 10 000 FCFA.',
     '4 000 FCFA versés à la vente, puis 2 000 FCFA remboursés. Il reste 4 000 FCFA à payer.',
     'creance.png'),
    (10, '03 / TABLEAU DE BORD', 'Retrouver les mêmes\nchiffres au même endroit.',
     'Une vente, deux articles, 10 000 FCFA de chiffre d’affaires.',
     'Le tableau de bord affiche aussi les 4 000 FCFA encore dus par le client.',
     'tableau-de-bord.png'),
    (7, 'POUR ALLER PLUS LOIN', 'Le projet,\ncôté code.',
     'Java 17 · Spring Boot\nAngular · PostgreSQL',
     '474 tests backend réussis le 17 septembre 2026. Choix techniques et liens vers le code sur cette page.',
     'catalogue.png'),
]
for i, (duration, label, title, body, note, asset) in enumerate(scenes):
    canvas = Image.new('RGB', (1600, 900), '#ffffff')
    draw = ImageDraw.Draw(canvas)
    draw.text((58, 30), 'CHEIKH / AUTO STOCK MANAGEMENT', font=font(22, True), fill=INK)
    draw.line((58, 78, 1542, 78), fill='#d9dfe6', width=2)
    draw.text((58, 134), label, font=font(23, True), fill=ACCENT)
    y = paragraph(draw, title, (58, 197), size=49, bold=True)
    y = paragraph(draw, body, (58, y + 30), size=29, fill=INK)
    paragraph(draw, note, (58, y + 32), size=27, fill=MUTED)
    screenshot = Image.open(ROOT / 'dist/images' / asset).convert('RGB')
    screenshot.thumbnail((805, 700), Image.Resampling.LANCZOS)
    x, y = 727 + (805 - screenshot.width) // 2, 115
    canvas.paste(screenshot, (x, y))
    draw.rectangle((x-1, y-1, x+screenshot.width, y+screenshot.height), outline='#d9dfe6', width=2)
    draw.line((58, 832, 1542, 832), fill='#d9dfe6', width=2)
    draw.text((58, 854), 'Aperçu en captures réelles · Données fictives · Sans audio', font=font(21), fill=MUTED)
    draw.text((1474, 854), f'{i+1} / 5', font=font(21), fill=MUTED)
    canvas.save(FRAMES / f'{i}.png')

(OUT / 'poster.jpg').write_bytes(b'')
Image.open(FRAMES / '0.png').save(OUT / 'poster.jpg', quality=92)
playlist = FRAMES / 'frames.txt'
lines = []
for i, scene in enumerate(scenes):
    lines.extend([f"file '{FRAMES / f'{i}.png'}'", f'duration {scene[0]}'])
lines.append(f"file '{FRAMES / '4.png'}'")
playlist.write_text('\n'.join(lines) + '\n')
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error',
    '-y', '-f', 'concat', '-safe', '0', '-i', str(playlist), '-vf', 'fps=24',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
    '-t', '47', '-movflags', '+faststart', str(OUT / 'auto-stock-demo.mp4')], check=True)
print('Video created: 47 seconds, 1600 x 900, silent H.264 MP4')
