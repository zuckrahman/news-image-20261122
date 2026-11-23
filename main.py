#!/usr/bin/env python3
"""Draw a 1024x1024 newspaper front page summing up the world news of
Sunday 22 November 2026, using only the Python standard library.

The picture is drawn pixel by pixel into an RGB buffer and written as a
deterministic PNG (fixed compression, no metadata chunks), so two runs
with no network write identical bytes.

Layout, top to bottom:
  masthead, date strip, lead story (COP31), two mid stories
  (Benghazi, Hormuz), three lower stories (Kyiv, West Bank, Nigeria),
  a briefs strip, and a footer line.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

# Colours.
PAPER = (247, 243, 232)
INK = (18, 22, 30)
NAVY = (16, 36, 62)
NAVY_LIGHT = (28, 58, 92)
RED = (178, 34, 28)
GOLD = (198, 148, 52)
SKY = (168, 205, 225)
SEA = (46, 110, 158)
SEA_DARK = (28, 78, 118)
SAND = (226, 205, 158)
GREEN = (74, 140, 86)
ORANGE = (224, 122, 42)
GREY = (108, 112, 118)
LIGHT_GREY = (232, 228, 218)
WHITE = (255, 255, 255)
BROWN = (122, 84, 52)
FLAME = (232, 120, 30)

# A 5x7 bitmap font. Each glyph is seven rows of five characters,
# "#" for a filled pixel and "." for an empty one. Only the characters
# used by the page are defined; text is drawn in upper case.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
}


class Canvas:
    """An RGB pixel buffer with simple flat drawing helpers."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height * 3)
        self.fill_rect(0, 0, width, height, colour)

    def set_pixel(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i] = colour[0]
            self.pixels[i + 1] = colour[1]
            self.pixels[i + 2] = colour[2]

    def fill_rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        for yy in range(y0, y1):
            base = (yy * self.width + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.pixels[i] = colour[0]
                self.pixels[i + 1] = colour[1]
                self.pixels[i + 2] = colour[2]

    def rect(self, x, y, w, h, colour, thickness=1):
        self.fill_rect(x, y, w, thickness, colour)
        self.fill_rect(x, y + h - thickness, w, thickness, colour)
        self.fill_rect(x, y, thickness, h, colour)
        self.fill_rect(x + w - thickness, y, thickness, h, colour)

    def line(self, x0, y0, x1, y1, colour, thickness=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            for a in range(thickness):
                for b in range(thickness):
                    self.set_pixel(x + a, y + b, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def filled_circle(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                    self.set_pixel(xx, yy, colour)

    def filled_polygon(self, points, colour):
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            nodes = []
            count = len(points)
            for i in range(count):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % count]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    nodes.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            nodes.sort()
            for k in range(0, len(nodes) - 1, 2):
                for x in range(int(nodes[k]), int(nodes[k + 1]) + 1):
                    self.set_pixel(x, y, colour)

    def text_width(self, text, scale):
        return len(text) * 6 * scale - scale

    def draw_text(self, x, y, text, scale, colour):
        cx = x
        for ch in text.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == "1":
                        self.fill_rect(
                            cx + col * scale, y + row * scale,
                            scale, scale, colour)
            cx += 6 * scale
        return cx

    def draw_text_centred(self, cx, y, text, scale, colour):
        self.draw_text(cx - self.text_width(text, scale) // 2,
                       y, text, scale, colour)

    def wrap(self, text, max_width, scale):
        words = text.upper().split()
        lines = []
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if self.text_width(trial, scale) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def draw_block(self, x, y, text, max_width, scale, colour,
                   line_gap=4):
        lines = self.wrap(text, max_width, scale)
        for i, line_text in enumerate(lines):
            self.draw_text(x, y + i * (7 * scale + line_gap),
                           line_text, scale, colour)
        return y + len(lines) * (7 * scale + line_gap)


def draw_waves(canvas, x, y, w, h, colour):
    """Three stacked wave lines across a sea panel."""
    for row in range(3):
        yy = y + 8 + row * (h // 3)
        for xx in range(x, x + w, 16):
            canvas.line(xx, yy, xx + 8, yy - 5, colour, 2)
            canvas.line(xx + 8, yy - 5, xx + 16, yy, colour, 2)


def draw_ship(canvas, x, y, w, h, hull, deck):
    """A simple side view of a ship on the water."""
    canvas.filled_polygon(
        [(x, y + h // 2), (x + w, y + h // 2),
         (x + w - 18, y + h), (x + 18, y + h)], hull)
    canvas.fill_rect(x + w // 4, y + 6, w // 2, h // 2 - 6, deck)
    canvas.fill_rect(x + w // 2 - 3, y - 14, 6, 20, hull)
    canvas.fill_rect(x + w // 4 + 8, y + 12, 10, 10, WHITE)
    canvas.fill_rect(x + w // 2 + 8, y + 12, 10, 10, WHITE)


def draw_burst(canvas, cx, cy, r, colour):
    """A starburst for an explosion."""
    points = []
    for i in range(16):
        ang = i * 3.14159265 / 8.0
        rad = r if i % 2 == 0 else r // 2
        points.append((int(cx + rad * 1.0 * (1 if i % 4 == 0 else 0.7)),
                       int(cy + rad * 0.0)))
    # Draw with simple radiating triangles instead of a trig star.
    for dx, dy in ((0, -r), (r, 0), (0, r), (-r, 0),
                   (int(r * 0.7), int(-r * 0.7)),
                   (int(r * 0.7), int(r * 0.7)),
                   (int(-r * 0.7), int(r * 0.7)),
                   (int(-r * 0.7), int(-r * 0.7))):
        canvas.filled_polygon(
            [(cx, cy), (cx + dx, cy + dy),
             (cx + int(dx * 0.4) - int(dy * 0.25),
              cy + int(dy * 0.4) + int(dx * 0.25))], colour)
    canvas.filled_circle(cx, cy, r // 2, colour)


def draw_globe(canvas, cx, cy, r):
    canvas.filled_circle(cx, cy, r, SEA)
    canvas.filled_polygon(
        [(cx - r + 8, cy - 6), (cx - 6, cy - r + 10),
         (cx + 2, cy - 4), (cx - 14, cy + 2)], GREEN)
    canvas.filled_polygon(
        [(cx + 4, cy + 6), (cx + r - 10, cy - 2),
         (cx + r - 4, cy + 14), (cx + 10, cy + r - 8),
         (cx - 2, cy + 16)], GREEN)
    canvas.filled_polygon(
        [(cx - r + 12, cy + r - 16), (cx - 4, cy + 10),
         (cx - 16, cy + r - 6)], GREEN)


def draw_building(canvas, x, y, w, h, colour):
    canvas.fill_rect(x, y, w, h, colour)
    for row in range(3):
        for col in range(3):
            wx = x + 8 + col * (w // 3)
            wy = y + 10 + row * (h // 3)
            canvas.fill_rect(wx, wy, w // 6, h // 7, SKY)
    canvas.line(x, y, x + w // 2, y - 12, INK, 3)
    canvas.line(x + w // 2, y - 12, x + w, y, INK, 3)


def draw_flame(canvas, x, y, w, h):
    canvas.filled_polygon(
        [(x, y + h), (x + w // 4, y + h // 2),
         (x + w // 2, y + h // 3), (x + w // 2 + 6, y),
         (x + w - 8, y + h // 2), (x + w, y + h)], FLAME)
    canvas.filled_polygon(
        [(x + w // 4, y + h), (x + w // 2, y + h // 2),
         (x + w - w // 4, y + h)], GOLD)


def build_image():
    c = Canvas(WIDTH, HEIGHT, PAPER)
    c.rect(10, 10, WIDTH - 20, HEIGHT - 20, INK, 3)

    # Masthead.
    c.fill_rect(14, 14, WIDTH - 28, 96, NAVY)
    c.draw_text_centred(WIDTH // 2, 30, "THE WORLD IN ONE DAY", 6, WHITE)
    c.fill_rect(60, 88, WIDTH - 120, 2, GOLD)
    c.draw_text_centred(WIDTH // 2, 94, "ONE DAY  -  ONE PAGE  -  THE WORLD",
                        1, GOLD)

    # Date strip.
    c.fill_rect(14, 110, WIDTH - 28, 52, WHITE)
    c.rect(14, 110, WIDTH - 28, 52, INK, 2)
    c.draw_text_centred(WIDTH // 2, 124, "SUNDAY 22 NOVEMBER 2026", 4, RED)
    c.draw_text(28, 148, "WORLD NEWS", 1, GREY)
    c.draw_text(WIDTH - 28 - c.text_width("SUNDAY EDITION", 1), 148,
                "SUNDAY EDITION", 1, GREY)

    # Lead story: COP31 collapse.
    lx, ly, lw, lh = 24, 172, WIDTH - 48, 252
    c.fill_rect(lx, ly, lw, lh, WHITE)
    c.rect(lx, ly, lw, lh, INK, 2)
    c.draw_text(lx + 18, ly + 14, "COP31  -  ANTALYA, TURKEY", 2, RED)
    c.draw_text(lx + 18, ly + 44, "CLIMATE TALKS", 5, INK)
    c.draw_text(lx + 18, ly + 84, "COLLAPSE", 5, INK)
    c.draw_block(lx + 18, ly + 136,
                 "COP31 ends with no deal after two weeks of talks. "
                 "The final text left out fossil fuels, and the EU and "
                 "island states refused to back it.", 560, 2, INK)
    # Lead picture: globe under a hot sun, cracked dry ground.
    px, py = lx + 600, ly + 16
    c.fill_rect(px, py, 356, 220, SKY)
    c.filled_circle(px + 296, py + 40, 26, ORANGE)
    for dx, dy in ((0, -34), (24, -24), (34, 0), (24, 24), (0, 34),
                   (-24, 24), (-34, 0), (-24, -24)):
        c.line(px + 296, py + 40, px + 296 + dx, py + 40 + dy, ORANGE, 3)
    draw_globe(c, px + 130, py + 105, 62)
    c.fill_rect(px, py + 176, 356, 44, SAND)
    c.line(px + 20, py + 176, px + 90, py + 205, BROWN, 3)
    c.line(px + 90, py + 205, px + 150, py + 190, BROWN, 3)
    c.line(px + 200, py + 176, px + 260, py + 210, BROWN, 3)
    c.line(px + 260, py + 210, px + 330, py + 196, BROWN, 3)
    c.draw_text(px + 12, py + 198, "NO DEAL ON FOSSIL FUELS", 2, RED)

    # Second row: two stories.
    # Benghazi.
    bx, by, bw, bh = 24, 436, 476, 216
    c.fill_rect(bx, by, bw, bh, WHITE)
    c.rect(bx, by, bw, bh, INK, 2)
    c.draw_text(bx + 14, by + 12, "LIBYA  -  BENGHAZI", 2, RED)
    c.draw_block(bx + 14, by + 38, "RUSSIAN WARSHIP HIT IN PORT", 448, 3, INK)
    c.draw_block(bx + 14, by + 96,
                 "Suspected sea drones hit the corvette Merkury. "
                 "The ship is badly damaged.", 448, 2, INK)
    c.fill_rect(bx + 14, by + 158, 448, 44, SEA)
    draw_ship(c, bx + 30, by + 162, 220, 26, NAVY, NAVY_LIGHT)
    draw_burst(c, bx + 330, by + 176, 18, ORANGE)
    draw_waves(c, bx + 14, by + 158, 448, 44, WHITE)

    # Hormuz.
    hx, hy, hw, hh = 524, 436, 476, 216
    c.fill_rect(hx, hy, hw, hh, WHITE)
    c.rect(hx, hy, hw, hh, INK, 2)
    c.draw_text(hx + 14, hy + 12, "GULF  -  STRAIT OF HORMUZ", 2, RED)
    c.draw_block(hx + 14, hy + 38, "TANKERS HIT AS GULF STANDOFF DEEPENS",
                 448, 3, INK)
    c.draw_block(hx + 14, hy + 96,
                 "Iran says two tankers hit mines east of Hormuz. "
                 "Trump warns of new strikes.", 448, 2, INK)
    c.fill_rect(hx + 14, hy + 158, 448, 44, SEA)
    draw_ship(c, hx + 30, hy + 162, 200, 26, INK, GREY)
    for mx in (hx + 280, hx + 330, hx + 380):
        c.filled_circle(mx, hy + 182, 10, INK)
        for dx, dy in ((0, -14), (10, -10), (14, 0), (10, 10), (0, 14),
                       (-10, 10), (-14, 0), (-10, -10)):
            c.line(mx, hy + 182, mx + dx, hy + 182 + dy, INK, 2)
    draw_waves(c, hx + 14, hy + 158, 448, 44, WHITE)

    # Third row: three stories.
    # Kyiv.
    kx, ky, kw, kh = 24, 664, 309, 204
    c.fill_rect(kx, ky, kw, kh, WHITE)
    c.rect(kx, ky, kw, kh, INK, 2)
    c.draw_text(kx + 12, ky + 12, "UKRAINE", 2, RED)
    c.draw_block(kx + 12, ky + 38, "STRIKE HITS FLATS NEAR KYIV", 285, 3, INK)
    c.draw_block(kx + 12, ky + 96,
                 "A Russian strike damages flats near the capital.",
                 285, 2, INK)
    c.fill_rect(kx + 12, ky + 158, 285, 34, LIGHT_GREY)
    draw_building(c, kx + 30, ky + 164, 70, 28, NAVY_LIGHT)
    draw_building(c, kx + 130, ky + 168, 60, 24, GREY)
    c.line(kx + 220, ky + 164, kx + 250, ky + 186, INK, 2)

    # West Bank.
    wx, wy, ww, wh = 357, 664, 309, 204
    c.fill_rect(wx, wy, ww, wh, WHITE)
    c.rect(wx, wy, ww, wh, INK, 2)
    c.draw_text(wx + 12, wy + 12, "WEST BANK", 2, RED)
    c.draw_block(wx + 12, wy + 38, "SETTLER ATTACKS CONDEMNED", 285, 3, INK)
    c.draw_block(wx + 12, wy + 96,
                 "Settlers torch vehicles and homes overnight.",
                 285, 2, INK)
    c.fill_rect(wx + 12, wy + 158, 285, 34, LIGHT_GREY)
    draw_building(c, wx + 30, wy + 164, 80, 28, BROWN)
    draw_flame(c, wx + 140, wy + 162, 34, 30)
    draw_flame(c, wx + 200, wy + 168, 26, 24)

    # Nigeria.
    nx, ny, nw, nh = 690, 664, 310, 204
    c.fill_rect(nx, ny, nw, nh, WHITE)
    c.rect(nx, ny, nw, nh, INK, 2)
    c.draw_text(nx + 12, ny + 12, "NIGERIA", 2, RED)
    c.draw_block(nx + 12, ny + 38, "AT LEAST 24 DEAD AS BOAT SINKS", 286, 3, INK)
    c.draw_block(nx + 12, ny + 96,
                 "A funeral boat capsizes in Bayelsa state.",
                 286, 2, INK)
    c.fill_rect(nx + 12, ny + 158, 286, 34, SEA)
    draw_ship(c, nx + 40, ny + 162, 150, 22, NAVY, NAVY_LIGHT)
    draw_waves(c, nx + 12, ny + 158, 286, 34, WHITE)

    # Briefs strip.
    fx, fy, fw, fh = 24, 880, WIDTH - 48, 76
    c.fill_rect(fx, fy, fw, fh, NAVY)
    c.draw_text(fx + 14, fy + 10, "ALSO TODAY", 2, GOLD)
    c.draw_block(fx + 14, fy + 34,
                 "Delta outage delays 1,600+ flights  *  Nepal PM "
                 "visits India  *  China eases margin rules  *  "
                 "Thai court cuts a defamation sentence",
                 948, 2, WHITE)

    # Footer.
    c.draw_text_centred(WIDTH // 2, 972,
                        "ALL STORIES ARE EVENTS REPORTED ON 22 NOVEMBER 2026",
                        2, INK)
    c.draw_text_centred(WIDTH // 2, 996,
                        "THE WORLD IN ONE DAY", 1, GREY)
    return c


def png_bytes(canvas):
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        start = y * stride
        raw.extend(canvas.pixels[start:start + stride])
    data = zlib.compress(bytes(raw), 9)

    def chunk(kind, payload):
        out = struct.pack(">I", len(payload)) + kind + payload
        out += struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height,
                       8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", data) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as handle:
        handle.write(png_bytes(build_image()))


if __name__ == "__main__":
    main()
