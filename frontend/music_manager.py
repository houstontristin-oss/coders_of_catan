"""
music_manager.py

ONE MusicManager inside ViewManager, call scene methods:
    self.music.play_start_menu()
    self.music.play_setup()
    self.music.play_main_board()
    self.music.stop_all()
    self.music.toggle_mute()
------------
Long tracks should be loaded with streaming=True.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import arcade


@dataclass
class TrackConfig:
    """Configuration for one named music/ambience track."""
    key: str
    path: str
    volume: float = 1.0
    loop: bool = True
    streaming: bool = True


class MusicManager:
    """
    Handles all music playback for the game.
    """

    def __init__(self, track_configs: dict[str, TrackConfig]):
        self._track_configs = track_configs

        # Loaded arcade.Sound objects
        self._sounds: dict[str, arcade.Sound] = {}

        # Active playback players, one per track key
        self._players: dict[str, object] = {}

        # Global state
        self.muted = False
        self.master_volume = 1.0
        self.current_scene = None

        self._load_tracks()

    # ------------------------------------------------------------------
    # Loading
    def _load_tracks(self) -> None:
        """Load all configured tracks once at startup."""
        for key, cfg in self._track_configs.items():
            if not cfg.path:
                continue
            if not os.path.exists(cfg.path):
                print(f"[MusicManager] Missing audio file for '{key}': {cfg.path}")
                continue

            try:
                self._sounds[key] = arcade.load_sound(
                    cfg.path,
                    streaming=cfg.streaming,
                )
            except Exception as exc:
                print(f"[MusicManager] Failed to load '{key}': {cfg.path} ({exc})")

    # ------------------------------------------------------------------
    # Volume helpers
    def _effective_volume(self, key: str) -> float:
        """Compute actual playback volume after mute/master volume."""
        if self.muted:
            return 0.0

        cfg = self._track_configs[key]
        return max(0.0, min(1.0, cfg.volume * self.master_volume))

    def set_master_volume(self, volume: float) -> None:
        """Set global master volume, clamped 0..1."""
        self.master_volume = max(0.0, min(1.0, volume))
        self._refresh_active_volumes()

    def set_track_volume(self, key: str, volume: float) -> None:
        """Set the base volume for one track, clamped 0..1."""
        if key not in self._track_configs:
            return
        self._track_configs[key].volume = max(0.0, min(1.0, volume))
        self._refresh_active_volumes()

    def _refresh_active_volumes(self) -> None:
        """Apply current mute/master/track volumes to all active players."""
        for key, player in self._players.items():
            if player is None:
                continue
            try:
                player.volume = self._effective_volume(key)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Playback controls
    def play_track(self, key: str, restart: bool = False) -> None:
        """
        Start one track if it is not already active.
        """
        if key not in self._sounds or key not in self._track_configs:
            return

        already_active = key in self._players and self._players[key] is not None
        if already_active and not restart:
            return

        if already_active and restart:
            self.stop_track(key)

        cfg = self._track_configs[key]
        sound = self._sounds[key]

        try:
            player = sound.play(
                volume=self._effective_volume(key),
                loop=cfg.loop,
            )
            self._players[key] = player
        except Exception as exc:
            print(f"[MusicManager] Failed to play '{key}': {exc}")

    def stop_track(self, key: str) -> None:
        """Stop one track if it is active."""
        player = self._players.get(key)
        if player is None:
            return

        try:
            player.pause()
            player.delete()
        except Exception:
            try:
                player.pause()
            except Exception:
                pass

        self._players[key] = None

    def stop_all(self) -> None:
        """Stop every active track."""
        for key in list(self._players.keys()):
            self.stop_track(key)
        self.current_scene = None

    def is_playing(self, key: str) -> bool:
        """Return True if a track currently has an active player."""
        player = self._players.get(key)
        return player is not None

    # ------------------------------------------------------------------
    # Mute
    def mute(self) -> None:
        self.muted = True
        self._refresh_active_volumes()

    def unmute(self) -> None:
        self.muted = False
        self._refresh_active_volumes()

    def toggle_mute(self) -> bool:
        """Toggle mute and return the new muted state."""
        self.muted = not self.muted
        self._refresh_active_volumes()
        return self.muted

    # ------------------------------------------------------------------
    # Scene presets
    def play_start_menu(self) -> None:
        """
        Start screen audio:
        - waves ambience
        - menu theme
        """
        if self.current_scene == "start":
            return

        self.stop_all()
        self.play_track("menu_waves")
        self.play_track("menu_theme")
        self.current_scene = "start"

    def play_setup(self) -> None:
        """
        Setup phase audio:
        - optional lighter setup theme
        """
        if self.current_scene == "setup":
            return

        self.stop_all()
        self.play_track("menu_waves")
        self.play_track("setup_theme")
        self.current_scene = "setup"

    def play_main_board(self) -> None:
        """
        Main gameplay audio:
        - tavern / folk board theme
        """
        if self.current_scene == "main_board":
            return

        self.stop_all()
        self.play_track("menu_waves")
        self.play_track("board_theme")
        self.current_scene = "main_board"

    def play_end_screen(self) -> None:
        """
        End screen audio:
        - optional victory or soft closing theme
        """
        if self.current_scene == "end":
            return

        self.stop_all()
        self.play_track("end_theme")
        self.current_scene = "end"