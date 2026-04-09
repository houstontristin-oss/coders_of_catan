# ViewManager uses go_to() to handle all view transitions in one place.
# Import this anywhere you need to switch views instead of importing views directly.

from frontend.music_manager import MusicManager, TrackConfig
from frontend.constants import (
    MENU_WAVES_MUSIC, MENU_THEME_MUSIC, SETUP_THEME_MUSIC,
    BOARD_THEME_MUSIC, END_THEME_MUSIC,
    MENU_WAVES_VOLUME, MENU_THEME_VOLUME, SETUP_THEME_VOLUME,
    BOARD_THEME_VOLUME, END_THEME_VOLUME, MASTER_MUSIC_VOLUME,
)

class ViewManager:
    """
    Owns all view construction and transition logic.
        """

    def __init__(self, window):
        self.window = window
        self._history = []  # stack of (name, kwargs) for back navigation
        self.music = MusicManager({
            "menu_waves": TrackConfig("menu_waves", MENU_WAVES_MUSIC, MENU_WAVES_VOLUME),
            "menu_theme": TrackConfig("menu_theme", MENU_THEME_MUSIC, MENU_THEME_VOLUME),
            "setup_theme": TrackConfig("setup_theme", SETUP_THEME_MUSIC, SETUP_THEME_VOLUME),
            "board_theme": TrackConfig("board_theme", BOARD_THEME_MUSIC, BOARD_THEME_VOLUME),
            "end_theme": TrackConfig("end_theme", END_THEME_MUSIC, END_THEME_VOLUME),
        })
        self.music.set_master_volume(MASTER_MUSIC_VOLUME)

    def go_to(self, name, **kwargs):
        """
        Transition to a named view, passing any kwargs to its constructor.
        Known views: "start", "setup", "catan", "play_card", "robber_place", "robber_res", "end"
        """
        view = self._build_view(name, kwargs)
        if view is None:
            raise ValueError(f"ViewManager: unknown view name '{name}'")
        self._history.append((name, kwargs))
        if name == "start":
            self.music.play_start_menu()
        elif name == "setup":
            self.music.play_setup()
        elif name in ("catan", "computer_turn", "play_card", "maritime_trade", "barter_trade",
                      "robber_place", "robber_res"):
            self.music.play_main_board()
        elif name == "end":
            self.music.play_end_screen()
        self.window.show_view(view)

    def go_back(self):
        """
        Pop the current view off the history stack and return to the previous one.
        Falls back to 'start' if history is empty.
        """
        if len(self._history) > 1:
            self._history.pop()  # remove current
            name, kwargs = self._history.pop()  # get previous (go_to will re-push it)
            self.go_to(name, **kwargs)
        else:
            self._history.clear()
            self.go_to("start")

    def _build_view(self, name, kwargs):
        """Construct and return the view object for the given name."""
        if name == "start":
            from frontend.start_view import StartView
            return StartView(self)
        elif name == "setup":
            from frontend.setup_view import SetupView
            return SetupView(self, **kwargs)
        elif name == "catan":
            from frontend.catan_view import CatanView
            return CatanView(self, **kwargs)
        elif name == "gamemode":
            from frontend.gamemode_view import GamemodeView
            return GamemodeView(self, **kwargs)
        elif name == "computer_turn":
            from frontend.computer_turn_view import ComputerTurnView
            return ComputerTurnView(self, **kwargs)
        elif name == "play_card":
            from frontend.play_card_view import PlayCardView
            return PlayCardView(self, **kwargs)
        elif name == "robber_place":
            from frontend.robber_place_view import RobberPlaceView
            return RobberPlaceView(self, **kwargs)
        elif name == "robber_res":
            from frontend.robber_res_view import RobberResView
            return RobberResView(self, **kwargs)
        elif name == "maritime_trade":
            from frontend.trade_view_maritime import TradeViewMaritime
            return TradeViewMaritime(self, **kwargs)
        elif name == "barter_trade":
            from frontend.trade_view_barter import TradeViewBarter
            return TradeViewBarter(self, **kwargs)
        elif name == "end":
            from frontend.end_view import EndView
            return EndView(self, **kwargs)
        return None
