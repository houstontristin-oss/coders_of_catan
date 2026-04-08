"""
gamemode_view.py
Contains transition screen for choosing a game mode
Choose between Regular Catan or Settler Vs. AI
Actual AI move logic can live in computer_turn_view.py or call helper methods from there
keep player 1 as human
set players 2–4 to computer = True
optionally rename them to AI 1, AI 2, AI 3
then go to SetupView like normal
"""
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT, TEXT_GOLD
from .drawing import fill_rect, outline_rect
from .start_view import (
    _draw_sunset_gradient,
    _draw_clouds,
    _draw_sun,
    _draw_farmscape,
)

import random
import arcade

from backend.player import Player
from backend.computer_player import ComputerPlayer

#From setup view, one should add a check to see if the next player is flagged as a computer



# Reuse the same painted background helpers from StartView


_FONT = "MedievalSharp"

# ---------------------------------------------------------------------------
# Layout / animation tuning
GM_TITLE_TARGET_Y = SCREEN_HEIGHT * 0.74
GM_TITLE_START_Y = SCREEN_HEIGHT + 90
GM_TITLE_FONT_SIZE = 34

GM_SUBTITLE_Y = SCREEN_HEIGHT * 0.67
GM_SUBTITLE_SIZE = 13

GM_BTN_W = 320
GM_BTN_H = 62
GM_BTN_GAP = 24

GM_BTN_1_CENTER_Y = SCREEN_HEIGHT * 0.52
GM_BTN_2_CENTER_Y = GM_BTN_1_CENTER_Y - (GM_BTN_H + GM_BTN_GAP)

GM_BTN_REVEAL_1 = 0.60
GM_BTN_REVEAL_2 = 1.00

GM_HOVER_SCALE = 1.06

GM_BTN_FILL = (20, 20, 50, 220)
GM_BTN_FILL_HOVER = (36, 36, 78, 236)
GM_BTN_OUTLINE = TEXT_GOLD
GM_BTN_TEXT = (236, 223, 187, 255)
GM_HINT_TEXT = (184, 137, 44, 255)
GM_SHADOW = (60, 20, 0, 185)

P1_COLOR = (231, 76,  60)
P2_COLOR = (39,  174, 96)
P3_COLOR = (219, 118, 51)
P4_COLOR = (142, 68,  173)

class GamemodeView(arcade.View):
    """
    Mode selection screen between StartView and gameplay setup.

    Parameters
    ----------
    board : CatanBoard
    players : list[Player]
    """

    def __init__(self, vm, board):
        super().__init__()
        self.vm = vm
        self.board = board

        self._time = 0.0
        self._hovered_mode = None

        self._title_y = GM_TITLE_START_Y

        self._build_text_objects()

    # ------------------------------------------------------------------
    # Text setup
    def _build_text_objects(self):
        self.txt_title_shadow = arcade.Text(
            "Choose Gamemode",
            SCREEN_WIDTH / 2 + 3, self._title_y - 3,
            GM_SHADOW, GM_TITLE_FONT_SIZE,
            bold=True,
            anchor_x="center", anchor_y="center",
            font_name=_FONT,
        )
        self.txt_title = arcade.Text(
            "Choose Gamemode",
            SCREEN_WIDTH / 2, self._title_y,
            TEXT_GOLD, GM_TITLE_FONT_SIZE,
            bold=True,
            anchor_x="center", anchor_y="center",
            font_name=_FONT,
        )
        self.txt_subtitle = arcade.Text(
            "Choose how you want to settle the island",
            SCREEN_WIDTH / 2, GM_SUBTITLE_Y,
            GM_HINT_TEXT, GM_SUBTITLE_SIZE,
            anchor_x="center", anchor_y="center",
            font_name=_FONT,
        )

    # ------------------------------------------------------------------
    # Helpers
    def _button_rect(self, mode_name: str):
        if mode_name == "catan":
            cx, cy = SCREEN_WIDTH / 2, GM_BTN_1_CENTER_Y
        else:
            cx, cy = SCREEN_WIDTH / 2, GM_BTN_2_CENTER_Y

        hovered = self._hovered_mode == mode_name
        scale = GM_HOVER_SCALE if hovered else 1.0
        w = GM_BTN_W * scale
        h = GM_BTN_H * scale
        left = cx - w / 2
        bottom = cy - h / 2
        return left, bottom, w, h, cx, cy, hovered

    def _button_ready(self, mode_name: str) -> bool:
        if mode_name == "catan":
            return self._time >= GM_BTN_REVEAL_1
        return self._time >= GM_BTN_REVEAL_2

    def _point_in_button(self, x, y, mode_name: str) -> bool:
        if not self._button_ready(mode_name):
            return False
        left, bottom, w, h, *_ = self._button_rect(mode_name)
        return left <= x <= left + w and bottom <= y <= bottom + h

    def _go_to_selected_mode(self, mode_name: str):
        players = []

        players.append(Player(P1_COLOR, "Player 1"))
        if mode_name == "ai":
            ai2 = ComputerPlayer(P2_COLOR, "AI 2", self.board)
            ai3 = ComputerPlayer(P3_COLOR, "AI 3", self.board)
            ai4 = ComputerPlayer(P4_COLOR, "AI 4", self.board)

            ai2.player_index = 1
            ai3.player_index = 2
            ai4.player_index = 3

            players.append(ai2)
            players.append(ai3)
            players.append(ai4)
        else:
            players.append(Player(P2_COLOR, "Player 2"))
            players.append(Player(P3_COLOR, "Player 3"))
            players.append(Player(P4_COLOR, "Player 4"))

        start_player = random.randint(0,3)
        self.vm.go_to(
            "setup",
            board=self.board,
            players=players,
            current_player=start_player,
            start_player=start_player,
            cycle=1,
            port_manager=None,
        )

    # ------------------------------------------------------------------
    # Arcade lifecycle
    def on_update(self, delta_time: float):
        self._time += delta_time

        # Smooth slide-down for title
        settle_speed = 10.0
        self._title_y += (GM_TITLE_TARGET_Y - self._title_y) * min(1.0, delta_time * settle_speed)

        # keep title texts synced to animated y
        self.txt_title.y = self._title_y
        self.txt_title_shadow.y = self._title_y - 3

    def on_draw(self):
        self.clear()

        # Same background language as StartView
        _draw_sunset_gradient()
        _draw_clouds(self._time)
        _draw_sun(self._time)
        _draw_farmscape(self._time)

        # Header
        self.txt_title_shadow.draw()
        self.txt_title.draw()

        if self._time >= 0.28:
            self.txt_subtitle.draw()

        # Buttons appear one-by-one
        if self._button_ready("catan"):
            self._draw_mode_button("catan", "Settlers of Catan")

        if self._button_ready("ai"):
            self._draw_mode_button("ai", "Settler vs. AI")

    def _draw_mode_button(self, mode_name: str, label: str):
        left, bottom, w, h, cx, cy, hovered = self._button_rect(mode_name)

        fill = GM_BTN_FILL_HOVER if hovered else GM_BTN_FILL

        # small drop shadow
        fill_rect(left + 3, bottom - 3, w, h, (0, 0, 0, 90))
        fill_rect(left, bottom, w, h, fill)
        outline_rect(left, bottom, w, h, GM_BTN_OUTLINE, 2)

        # subtle inner glow on hover
        if hovered:
            outline_rect(left + 4, bottom + 4, w - 8, h - 8, (255, 230, 150, 80), 1)

        arcade.Text(
            label,
            cx, cy,
            GM_BTN_TEXT,
            22 if hovered else 19,
            bold=True,
            anchor_x="center", anchor_y="center",
            font_name=_FONT,
        ).draw()

    # ------------------------------------------------------------------
    # Mouse handling
    def on_mouse_motion(self, x, y, dx, dy):
        self._hovered_mode = None

        if self._point_in_button(x, y, "catan"):
            self._hovered_mode = "catan"
        elif self._point_in_button(x, y, "ai"):
            self._hovered_mode = "ai"

    def on_mouse_press(self, x, y, button, modifiers):
        if self._point_in_button(x, y, "catan"):
            self._go_to_selected_mode("catan")
            return

        if self._point_in_button(x, y, "ai"):
            self._go_to_selected_mode("ai")
            return
