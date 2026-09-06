# -*- coding: utf-8 -*-
"""Genere l'icone Lamina (PNG) pour la PWA dans le dossier pwa/."""
import os
import struct
import zlib

RACINE = os.path.dirname(os.path.abspath(__file__))


def _creer_png(chemin, taille, lettre):
    w = h = taille
    nb = 7
    cellule = taille / nb
    rows = []
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            gx = int(x // cellule)
            gy = int(y // cellule)
            if gx == 0 and 0 <= gy <= 4:
                lum = 255
            elif gy == 4 and 0 <= gx <= 6:
                lum = 255
            else:
                decal = y / max(1, h - 1)
                r = 192 - int(30 * decal)
                g = 57 - int(14 * decal)
                b = 43 - int(10 * decal)
                lum = (r, g, b)
            if lum == 255:
                row.extend([255, 255, 255, 255])
            else:
                r, g, b = lum
                row.extend([r, g, b, 255])
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(chemin, "wb") as f:
        f.write(png)
    print("genere:", chemin, taille, "x", taille)


def main():
    for taille in (512, 192, 180):
        _creer_png(os.path.join(RACINE, f"icone-{taille}.png"), taille, "L")


if __name__ == "__main__":
    main()