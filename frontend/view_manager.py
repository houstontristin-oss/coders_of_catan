# ViewManager uses function go_to to send the arcade view to different views
# go_to will be implemented into views anywhere where you import and show other views

class ViewManager:
    """
    Owns all view construction and transition logic.
 
    Parameters
    ----------
    window : arcade.Window
    """
 
    def __init__(self, window):
        self.window = window
    
    def go_to(self, name, **kwargs):
        if name == "start":
            from frontend.start_view import StartView
            self.window.show_view(StartView(self))
        elif name == "setup":
            from frontend.setup_view import SetupView
            self.window.show_view(SetupView(self, **kwargs))
        elif name == "catan":
            from frontend.catan_view import CatanView
            self.window.show_view(CatanView(self, **kwargs))
        elif name == "play_card":
            from frontend.play_card_view import PlayCardView
            self.window.show_view(PlayCardView(self, **kwargs))
