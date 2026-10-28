#!/usr/bin/env python3
"""
Тетрис — standalone desktop Tetris game built with Pygame.
Ported from the original index.html web version.

Controls (work regardless of keyboard layout — uses scancodes):
  Arrow keys / WASD — move and rotate
  Space              — hard drop
  P / Escape         — pause
"""

import random
import sys
import math

import pygame
from pygame.locals import (
    QUIT,
    KEYDOWN,
    VIDEORESIZE,
)

# ─── Constants ────────────────────────────────────────────────────────
COLUMNS = 10
ROWS = 20
CELL = 30  # base cell size (will scale with window)

# Palette (matching the HTML version)
INK    = (23, 27, 24)
LINE   = (57, 65, 57)
MUTED  = (157, 168, 155)
PAPER  = (240, 243, 232)
LIME   = (217, 255, 99)
CORAL  = (255, 115, 92)
TEAL   = (102, 216, 197)
YELLOW = (255, 209, 102)

COLORS = [
    None,
    TEAL,      # 1 — I
    YELLOW,    # 2 — O
    (201, 139, 255),  # 3 — T (purple)
    LIME,      # 4 — S
    CORAL,     # 5 — Z
    (98, 185, 255),   # 6 — J (blue)
    (243, 155, 103),  # 7 — L (orange)
]

SHAPES = [
    [[1, 1, 1, 1]],             # I
    [[2, 2], [2, 2]],           # O
    [[0, 3, 0], [3, 3, 3]],     # T
    [[4, 4, 0], [0, 4, 4]],     # S
    [[0, 5, 5], [5, 5, 0]],     # Z
    [[6, 0, 0], [6, 6, 6]],     # J
    [[0, 0, 7], [7, 7, 7]],     # L
]

# Scoring
LINE_SCORES = [0, 100, 300, 500, 800]

# ─── SDL scancodes for layout-independent WASD ───────────────────────
# pygame.KSCAN_* constants for physical key positions
SC_W = pygame.KSCAN_W  # 26
SC_A = pygame.KSCAN_A  # 4
SC_S = pygame.KSCAN_S  # 22
SC_D = pygame.KSCAN_D  # 7
SC_P = pygame.KSCAN_P  # 19
SC_X = pygame.KSCAN_X  # 27

# ─── Helpers ──────────────────────────────────────────────────────────

def deep_copy_shape(shape):
    return [row[:] for row in shape]


class SoundManager:
    """Simple beep synthesizer using pygame.mixer."""

    def __init__(self, enabled=False):
        self.enabled = enabled
        self._cache = {}

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            self.play_tone(500, 0.06)
        return self.enabled

    def play_tone(self, frequency, duration=0.06):
        if not self.enabled:
            return
        key = (frequency, duration)
        if key not in self._cache:
            sample_rate = 22050
            n_samples = int(sample_rate * duration)
            buf = bytearray(n_samples * 2)  # 16-bit mono
            for i in range(n_samples):
                t = i / sample_rate
                # square wave
                val = 1 if math.sin(2 * math.pi * frequency * t) >= 0 else -1
                # envelope: fade out
                envelope = max(0.001, 1.0 - (i / n_samples))
                sample = int(val * envelope * 1200)  # low volume
                sample = max(-32768, min(32767, sample))
                buf[i * 2] = sample & 0xFF
                buf[i * 2 + 1] = (sample >> 8) & 0xFF
            sound = pygame.mixer.Sound(buffer=bytes(buf))
            self._cache[key] = sound
        self._cache[key].play()


class Piece:
    __slots__ = ("shape", "x", "y")

    def __init__(self, shape, x=0, y=0):
        self.shape = shape
        self.x = x
        self.y = y


class TetrisGame:
    """Core Tetris game logic — no rendering."""

    def __init__(self):
        self.board = self._empty_board()
        self.bag = []
        self.score = 0
        self.lines = 0
        self.level = 1
        self.paused = False
        self.game_over = False
        self.current = None
        self.next_shape = None
        self._refill_bag()
        self.next_shape = self._take_shape()
        self._spawn()

    # ── board helpers ──

    @staticmethod
    def _empty_board():
        return [[0] * COLUMNS for _ in range(ROWS)]

    def _refill_bag(self):
        self.bag = list(range(len(SHAPES)))
        random.shuffle(self.bag)

    def _take_shape(self):
        if not self.bag:
            self._refill_bag()
        return deep_copy_shape(SHAPES[self.bag.pop()])

    # ── collision ──

    def _collides(self, shape, x, y):
        for ry, row in enumerate(shape):
            for rx, val in enumerate(row):
                if not val:
                    continue
                bx = x + rx
                by = y + ry
                if bx < 0 or bx >= COLUMNS or by >= ROWS:
                    return True
                if by >= 0 and self.board[by][bx]:
                    return True
        return False

    # ── spawning ──

    def _spawn(self):
        shape = self.next_shape
        self.next_shape = self._take_shape()
        x = (COLUMNS - len(shape[0])) // 2
        self.current = Piece(shape, x, 0)
        if self._collides(shape, x, 0):
            self._end_game()

    # ── locking & line clear ──

    def _lock_piece(self):
        for ry, row in enumerate(self.current.shape):
            for rx, val in enumerate(row):
                if val and self.current.y + ry >= 0:
                    self.board[self.current.y + ry][self.current.x + rx] = val
        cleared = 0
        self.board = [
            row for row in self.board
            if not all(row)
        ]
        cleared = ROWS - len(self.board)
        while len(self.board) < ROWS:
            self.board.insert(0, [0] * COLUMNS)
        return cleared

    # ── public actions ──

    def move_down(self, soft=False):
        """Move piece down one row. Returns number of cleared lines (0 if none, -1 if just moved)."""
        if self.paused or self.game_over:
            return 0
        self.current.y += 1
        if self._collides(self.current.shape, self.current.x, self.current.y):
            self.current.y -= 1
            cleared = self._lock_piece()
            if cleared:
                self.score += LINE_SCORES[min(cleared, 4)] * self.level
                self.lines += cleared
                self.level = self.lines // 10 + 1
            self._spawn()
            return cleared
        else:
            if soft:
                self.score += 1
            return -1  # just moved

    def move_left(self):
        if self.paused or self.game_over:
            return False
        self.current.x -= 1
        if self._collides(self.current.shape, self.current.x, self.current.y):
            self.current.x += 1
            return False
        return True

    def move_right(self):
        if self.paused or self.game_over:
            return False
        self.current.x += 1
        if self._collides(self.current.shape, self.current.x, self.current.y):
            self.current.x -= 1
            return False
        return True

    def rotate(self):
        if self.paused or self.game_over:
            return False
        rotated = list(zip(*reversed(self.current.shape)))
        rotated = [list(row) for row in rotated]
        saved = self.current.shape
        self.current.shape = rotated
        for shift in [0, -1, 1, -2, 2]:
            self.current.x += shift
            if not self._collides(self.current.shape, self.current.x, self.current.y):
                return True
            self.current.x -= shift
        self.current.shape = saved
        return False

    def hard_drop(self):
        if self.paused or self.game_over:
            return 0
        distance = 0
        while not self._collides(self.current.shape, self.current.x, self.current.y + 1):
            self.current.y += 1
            distance += 1
        self.score += distance * 2
        cleared = self._lock_piece()
        if cleared:
            self.score += LINE_SCORES[min(cleared, 4)] * self.level
            self.lines += cleared
            self.level = self.lines // 10 + 1
        self._spawn()
        return cleared

    def toggle_pause(self):
        if self.game_over:
            return
        self.paused = not self.paused

    def _end_game(self):
        self.game_over = True
        self.paused = False

    def restart(self):
        self.board = self._empty_board()
        self.bag = []
        self.score = 0
        self.lines = 0
        self.level = 1
        self.paused = False
        self.game_over = False
        self._refill_bag()
        self.next_shape = self._take_shape()
        self._spawn()

    def ghost_y(self):
        """Y position of where the current piece would land."""
        gy = self.current.y
        while not self._collides(self.current.shape, self.current.x, gy + 1):
            gy += 1
        return gy

    @property
    def drop_interval(self):
        return max(90, 800 - (self.level - 1) * 65)


# ─── Renderer ─────────────────────────────────────────────────────────

class TetrisRenderer:
    """Draws the Tetris game onto a Pygame surface."""

    # Layout constants (at 1x scale)
    BASE_BOARD_W = COLUMNS * CELL       # 300
    BASE_BOARD_H = ROWS * CELL          # 600
    SIDE_W = 180
    GAP = 28
    PANEL_PAD = 16
    TOP_BAR_H = 58

    MIN_W = 700
    MIN_H = 500

    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        pygame.display.set_caption("Тетрис")

        # Set window icon — 32x32 tetromino
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        icon.fill((0, 0, 0, 0))
        pygame.draw.rect(icon, LIME, (0, 0, 14, 14), border_radius=2)
        pygame.draw.rect(icon, CORAL, (17, 0, 14, 14), border_radius=2)
        pygame.draw.rect(icon, TEAL, (0, 17, 14, 14), border_radius=2)
        pygame.draw.rect(icon, YELLOW, (17, 17, 14, 14), border_radius=2)
        pygame.display.set_icon(icon)

        self.win_w = self.MIN_W + 200
        self.win_h = self.MIN_H + 250
        self.screen = pygame.display.set_mode(
            (self.win_w, self.win_h), pygame.RESIZABLE
        )
        self.font_big = None
        self.font_med = None
        self.font_sm = None
        self.font_key = None
        self._load_fonts()

    def _load_fonts(self):
        # Use system fonts — try to find a good sans-serif
        name = pygame.font.match_font("dejavusans,segoeui,arial,sans")
        self.font_big = pygame.font.Font(name, 30)
        self.font_med = pygame.font.Font(name, 18)
        self.font_sm = pygame.font.Font(name, 13)
        self.font_key = pygame.font.Font(name, 11)
        self.font_title = pygame.font.Font(name, 22)
        self.font_overlay = pygame.font.Font(name, 26)

    def _compute_layout(self):
        """Compute scale factor and positions to fit the window."""
        usable_w = self.win_w - 40  # 20px margin each side
        usable_h = self.win_h - self.TOP_BAR_H - 30  # top bar + bottom margin

        # The board should take about half the width; sides take rest
        total_base_w = self.SIDE_W + self.GAP + self.BASE_BOARD_W + self.GAP + self.SIDE_W
        scale_w = usable_w / total_base_w
        scale_h = usable_h / self.BASE_BOARD_H
        self.scale = min(scale_w, scale_h, 1.5)  # cap at 1.5x
        self.scale = max(self.scale, 0.5)  # min 0.5x

        self.cell = int(CELL * self.scale)
        board_w = COLUMNS * self.cell
        board_h = ROWS * self.cell
        side_w = int(self.SIDE_W * self.scale)
        gap = int(self.GAP * self.scale)

        total_w = side_w + gap + board_w + gap + side_w
        self.board_x = (self.win_w - total_w) // 2 + side_w + gap
        self.board_y = self.TOP_BAR_H + (usable_h - board_h) // 2
        self.board_w = board_w
        self.board_h = board_h
        self.left_x = self.board_x - gap - side_w
        self.right_x = self.board_x + board_w + gap
        self.side_w = side_w

    def draw(self, game: TetrisGame, sound: SoundManager):
        self._compute_layout()
        self.screen.fill(INK)

        # Dot pattern background
        for dx in range(0, self.win_w, 22):
            for dy in range(0, self.win_h, 22):
                pygame.draw.circle(self.screen, (52, 64, 53), (dx, dy), 1)

        self._draw_top_bar(game)
        self._draw_board(game)
        self._draw_left_panel(game)
        self._draw_right_panel(game, sound)

        if game.paused:
            self._draw_overlay("ПАУЗА", "Нажми P / Esc — продолжить")
        elif game.game_over:
            self._draw_overlay("ИГРА ОКОНЧЕНА", f"Счёт: {game.score}. Нажми R — новая игра")

        pygame.display.flip()

    # ── top bar ──

    def _draw_top_bar(self, game):
        # Brand
        bx, by = 20, 12
        mark_size = int(17 * self.scale)
        mark_gap = 2
        pygame.draw.rect(self.screen, LIME, (bx, by, mark_size, mark_size), border_radius=2)
        pygame.draw.rect(self.screen, CORAL, (bx + mark_size + mark_gap, by, mark_size, mark_size), border_radius=2)
        pygame.draw.rect(self.screen, TEAL, (bx, by + mark_size + mark_gap, mark_size, mark_size), border_radius=2)
        pygame.draw.rect(self.screen, YELLOW, (bx + mark_size + mark_gap, by + mark_size + mark_gap, mark_size, mark_size), border_radius=2)

        title_surf = self.font_title.render("ТЕТРИС", True, PAPER)
        self.screen.blit(title_surf, (bx + (mark_size * 2 + mark_gap) + 12, by + 6))

        # Status
        status_text = "Игра идёт"
        dot_color = LIME
        if game.paused:
            status_text = "Пауза"
            dot_color = CORAL
        elif game.game_over:
            status_text = "Конец игры"
            dot_color = CORAL

        st_surf = self.font_sm.render(status_text.upper(), True, MUTED)
        st_x = self.win_w - 20 - st_surf.get_width()
        st_y = by + 10
        pygame.draw.circle(self.screen, dot_color, (st_x - 12, st_y + 6), 4)
        self.screen.blit(st_surf, (st_x, st_y))

        # Divider
        div_y = self.TOP_BAR_H - 2
        pygame.draw.line(self.screen, LINE, (20, div_y), (self.win_w - 20, div_y), 1)

    # ── board ──

    def _draw_board(self, game):
        board_rect = pygame.Rect(self.board_x - 2, self.board_y - 2,
                                 self.board_w + 4, self.board_h + 4)
        # Shadow
        shadow_rect = board_rect.inflate(10, 10)
        shadow = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 40))
        self.screen.blit(shadow, shadow_rect.topleft)

        # Outer border
        pygame.draw.rect(self.screen, (87, 98, 83), board_rect, 2, border_radius=3)
        # Board background
        inner = pygame.Rect(self.board_x, self.board_y, self.board_w, self.board_h)
        pygame.draw.rect(self.screen, (17, 21, 18), inner)

        # Grid lines
        for x in range(1, COLUMNS):
            px = self.board_x + x * self.cell
            pygame.draw.line(self.screen, (40, 48, 40), (px, self.board_y), (px, self.board_y + self.board_h), 1)
        for y in range(1, ROWS):
            py = self.board_y + y * self.cell
            pygame.draw.line(self.screen, (40, 48, 40), (self.board_x, py), (self.board_x + self.board_w, py), 1)

        # Locked cells
        for y, row in enumerate(game.board):
            for x, val in enumerate(row):
                if val:
                    self._draw_cell(self.board_x + x * self.cell,
                                    self.board_y + y * self.cell,
                                    val, self.cell)

        if game.current and not game.game_over:
            # Ghost
            gy = game.ghost_y()
            for ry, row in enumerate(game.current.shape):
                for rx, val in enumerate(row):
                    if val:
                        gx_px = self.board_x + (game.current.x + rx) * self.cell
                        gy_px = self.board_y + (gy + ry) * self.cell
                        self._draw_cell(gx_px, gy_px, val, self.cell, alpha=60)

            # Current piece
            for ry, row in enumerate(game.current.shape):
                for rx, val in enumerate(row):
                    if val:
                        px = self.board_x + (game.current.x + rx) * self.cell
                        py = self.board_y + (game.current.y + ry) * self.cell
                        self._draw_cell(px, py, val, self.cell)

    def _draw_cell(self, px, py, val, size, alpha=255):
        if not val or val < 1 or val >= len(COLORS):
            return
        color = COLORS[val]
        inset = max(1, round(size * 0.07))

        cell_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        # Main
        r = pygame.Rect(inset, inset, size - inset * 2, size - inset * 2)
        pygame.draw.rect(cell_surf, (*color, alpha), r)
        # Highlight top
        pygame.draw.rect(cell_surf, (255, 255, 255, min(alpha, 53)),
                         (inset, inset, size - inset * 2, max(2, inset)))
        # Shadow bottom
        pygame.draw.rect(cell_surf, (0, 0, 0, min(alpha, 34)),
                         (inset, size - inset * 2, size - inset * 2, inset))
        self.screen.blit(cell_surf, (px, py))

    # ── panels ──

    def _draw_panel(self, x, y, w, h):
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((34, 40, 34, 232))
        pygame.draw.rect(panel, (*LINE, 200), (0, 0, w, h), 1, border_radius=5)
        self.screen.blit(panel, (x, y))

    def _draw_left_panel(self, game):
        x = self.left_x
        y = self.board_y
        w = self.side_w
        pad = int(self.PANEL_PAD * self.scale)

        # ── Score panel ──
        panel_h = int(130 * self.scale)
        self._draw_panel(x, y, w, panel_h)

        # Label
        lbl = self.font_key.render("СЧЁТ", True, MUTED)
        self.screen.blit(lbl, (x + pad, y + pad))

        # Score value
        score_str = str(game.score).zfill(6)
        score_surf = self.font_big.render(score_str, True, LIME)
        self.screen.blit(score_surf, (x + pad, y + pad + 20))

        # Lines / Level
        row_y = y + pad + 60
        lbl_lines = self.font_key.render("ЛИНИИ", True, MUTED)
        self.screen.blit(lbl_lines, (x + pad, row_y))
        val_lines = self.font_med.render(str(game.lines), True, PAPER)
        self.screen.blit(val_lines, (x + pad, row_y + 14))

        lbl_level = self.font_key.render("УРОВЕНЬ", True, MUTED)
        self.screen.blit(lbl_level, (x + pad + w // 2 - pad, row_y))
        val_level = self.font_med.render(str(game.level), True, PAPER)
        self.screen.blit(val_level, (x + pad + w // 2 - pad, row_y + 14))

        # ── Next piece panel ──
        next_y = y + panel_h + int(14 * self.scale)
        next_h = int(120 * self.scale)
        self._draw_panel(x, next_y, w, next_h)

        lbl2 = self.font_key.render("СЛЕДУЮЩАЯ", True, MUTED)
        self.screen.blit(lbl2, (x + pad, next_y + pad))

        # Draw the next shape preview
        if game.next_shape:
            preview_cell = int(18 * self.scale)
            shape = game.next_shape
            sw = len(shape[0]) * preview_cell
            sh = len(shape) * preview_cell
            ox = x + (w - sw) // 2
            oy = next_y + pad + 22 + (next_h - pad - 22 - sh) // 2
            for ry, row in enumerate(shape):
                for rx, val in enumerate(row):
                    if val:
                        self._draw_cell(ox + rx * preview_cell,
                                        oy + ry * preview_cell,
                                        val, preview_cell)

    def _draw_right_panel(self, game, sound):
        x = self.right_x
        y = self.board_y
        w = self.side_w
        pad = int(self.PANEL_PAD * self.scale)

        # ── Controls panel ──
        controls_h = int(180 * self.scale)
        self._draw_panel(x, y, w, controls_h)

        lbl = self.font_key.render("КЛАВИШИ", True, MUTED)
        self.screen.blit(lbl, (x + pad, y + pad))

        keys_info = [
            ("Движение", "← → A D"),
            ("Поворот", "↑ W"),
            ("Ускорить", "↓ S"),
            ("Сбросить", "Space"),
            ("Пауза", "P  Esc"),
            ("Новая игра", "R"),
        ]
        ky = y + pad + 18
        for label, keys in keys_info:
            lbl_s = self.font_key.render(label, True, MUTED)
            key_s = self.font_key.render(keys, True, PAPER)
            self.screen.blit(lbl_s, (x + pad, ky))
            self.screen.blit(key_s, (x + w - pad - key_s.get_width(), ky))
            ky += int(22 * self.scale)

        # ── Actions panel ──
        actions_y = y + controls_h + int(14 * self.scale)
        actions_h = int(110 * self.scale)
        self._draw_panel(x, actions_y, w, actions_h)

        lbl3 = self.font_key.render("ИГРА", True, MUTED)
        self.screen.blit(lbl3, (x + pad, actions_y + pad))

        # Buttons info
        btn_y = actions_y + pad + 18
        btns = [
            ("R — Новая игра", True),
            ("P — " + ("Продолжить" if game.paused else "Пауза"), False),
            ("M — Звук: " + ("вкл." if sound.enabled else "выкл."), False),
        ]
        for text, primary in btns:
            btn_rect = pygame.Rect(x + pad, btn_y, w - pad * 2, int(22 * self.scale))
            bg = LIME if primary else (41, 49, 41)
            fg = INK if primary else PAPER
            pygame.draw.rect(self.screen, bg, btn_rect, border_radius=3)
            pygame.draw.rect(self.screen, LINE, btn_rect, 1, border_radius=3)
            btn_surf = self.font_key.render(text, True, fg)
            self.screen.blit(btn_surf, (btn_rect.x + 6, btn_rect.y + 4))
            btn_y += int(28 * self.scale)

        # Note
        note_y = actions_y + actions_h + int(10 * self.scale)
        note = self.font_key.render("Собирай линии, набирай очки!", True, MUTED)
        self.screen.blit(note, (x + pad, note_y))

    # ── overlay ──

    def _draw_overlay(self, title, message):
        overlay = pygame.Surface((self.board_w, self.board_h), pygame.SRCALPHA)
        overlay.fill((17, 21, 18, 232))
        title_surf = self.font_overlay.render(title, True, LIME)
        msg_surf = self.font_sm.render(message, True, MUTED)
        tx = (self.board_w - title_surf.get_width()) // 2
        ty = self.board_h // 2 - 20
        mx = (self.board_w - msg_surf.get_width()) // 2
        my = ty + 36
        overlay.blit(title_surf, (tx, ty))
        overlay.blit(msg_surf, (mx, my))
        self.screen.blit(overlay, (self.board_x, self.board_y))

    def handle_resize(self, w, h):
        self.win_w = max(w, self.MIN_W)
        self.win_h = max(h, self.MIN_H)
        self.screen = pygame.display.set_mode(
            (self.win_w, self.win_h), pygame.RESIZABLE
        )


# ─── Main loop ────────────────────────────────────────────────────────

def main():
    renderer = TetrisRenderer()
    game = TetrisGame()
    sound = SoundManager(enabled=False)
    clock = pygame.time.Clock()
    last_drop = pygame.time.get_ticks()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            elif event.type == VIDEORESIZE:
                renderer.handle_resize(event.w, event.h)

            elif event.type == KEYDOWN:
                sc = event.scancode  # layout-independent

                # Escape always pauses
                if event.key == pygame.K_ESCAPE:
                    game.toggle_pause()

                # P — pause (by scancode for layout independence)
                elif sc == SC_P:
                    game.toggle_pause()

                # R — restart (use scancode)
                elif sc == pygame.KSCAN_R:
                    game.restart()
                    last_drop = pygame.time.get_ticks()

                # M — toggle sound
                elif sc == pygame.KSCAN_M:
                    sound.toggle()

                # Movement & actions (arrows always work by keycode)
                elif event.key == pygame.K_LEFT or sc == SC_A:
                    if game.move_left():
                        sound.play_tone(300)

                elif event.key == pygame.K_RIGHT or sc == SC_D:
                    if game.move_right():
                        sound.play_tone(300)

                elif event.key == pygame.K_UP or sc == SC_W or sc == SC_X:
                    if game.rotate():
                        sound.play_tone(420)

                elif event.key == pygame.K_DOWN or sc == SC_S:
                    game.move_down(soft=True)

                elif event.key == pygame.K_SPACE:
                    cleared = game.hard_drop()
                    sound.play_tone(240)
                    if cleared:
                        sound.play_tone(660, 0.13)

        # Auto-drop
        now = pygame.time.get_ticks()
        if not game.paused and not game.game_over:
            if now - last_drop > game.drop_interval:
                cleared = game.move_down()
                if cleared and cleared > 0:
                    sound.play_tone(660, 0.13)
                last_drop = now

        renderer.draw(game, sound)
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

