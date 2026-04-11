# ViewManager uses go_to() to handle all view transitions in one place.
# Import this anywhere you need to switch views instead of importing views directly.

from frontend.music_manager import MusicManager, TrackConfig
from frontend.constants import (
    MENU_WAVES_MUSIC, MENU_THEME_MUSIC,
    GAMEPLAY_THEME_MUSIC, END_THEME_MUSIC,
    MENU_WAVES_VOLUME, MENU_THEME_VOLUME,
    BOARD_WAVES_VOLUME, GAMEPLAY_THEME_VOLUME,
    END_THEME_VOLUME, MASTER_MUSIC_VOLUME,
)
from frontend import start_view
from frontend import setup_view
from frontend import catan_view
from frontend import gamemode_view
from frontend import computer_turn_view
from frontend import play_card_view
from frontend import robber_place_view
from frontend import robber_res_view
from frontend import trade_view_maritime
from frontend import trade_view_barter
from frontend import end_view

class ViewManager:
    """
    Owns all view construction and transition logic.
        """

    def __init__(self, window):
        self.window = window
        self._history = []  # stack of (name, kwargs) for back navigation
        self._view_registry = {
            "start": start_view.StartView,
            "setup": setup_view.SetupView,
            "catan": catan_view.CatanView,
            "gamemode": gamemode_view.GamemodeView,
            "computer_turn": computer_turn_view.ComputerTurnView,
            "play_card": play_card_view.PlayCardView,
            "robber_place": robber_place_view.RobberPlaceView,
            "robber_res": robber_res_view.RobberResView,
            "maritime_trade": trade_view_maritime.TradeViewMaritime,
            "barter_trade": trade_view_barter.TradeViewBarter,
            "end": end_view.EndView,
        }
        self.music = MusicManager({
            "menu_waves": TrackConfig("menu_waves", MENU_WAVES_MUSIC, MENU_WAVES_VOLUME),
            "menu_theme": TrackConfig("menu_theme", MENU_THEME_MUSIC, MENU_THEME_VOLUME),
            "board_waves": TrackConfig("board_waves", MENU_WAVES_MUSIC, BOARD_WAVES_VOLUME),
            "gameplay_theme": TrackConfig("gameplay_theme", GAMEPLAY_THEME_MUSIC,
                                          GAMEPLAY_THEME_VOLUME),
            "end_theme": TrackConfig("end_theme", END_THEME_MUSIC, END_THEME_VOLUME),
        })
        self.music.set_master_volume(MASTER_MUSIC_VOLUME)

    def go_to(self, name, **kwargs):
        """
        Transition to a named view, passing any kwargs to its constructor.
        """
        view = self._build_view(name, kwargs)
        if view is None:
            raise ValueError(f"ViewManager: unknown view name '{name}'")

        self._history.append((name, kwargs))

        gameplay_views = {
            "setup", "catan", "computer_turn", "play_card", 
            "maritime_trade", "barter_trade", "robber_place", "robber_res"
        }

        if name == "start":
            self.music.play_start_menu()
        elif name in gameplay_views:
            self.music.play_gameplay()
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
        """Construct and return the view object using the registry."""
        view_class = self._view_registry.get(name)
        if not view_class:
            return None
            
        # StartView is the only one not accepting **kwargs
        if name == "start":
            return view_class(self)
            
        return view_class(self, **kwargs)
