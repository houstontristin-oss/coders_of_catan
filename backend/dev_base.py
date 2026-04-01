"""
dev_base.py — Development Card Hierarchy
-----------------------------------------
Base class DevCard and one child class per card type.

All visual data (labels, descriptions, tints) live in constants.py.
This file contains ONLY game logic so it can be unit-tested without arcade.
"""

from frontend.constants import (
    DEV_CARD_LABELS,
    DEV_CARD_DESCRIPTIONS,
    DEV_CARD_TINTS,
)

# ---------------------------------------------------------------------------
# Action-tag constants  (returned by DevCard.apply())
ACTION_NONE           = "none"
ACTION_BACK_TO_BOARD  = "back_to_board"
ACTION_POPUP_YOP      = "popup_year_of_plenty"
ACTION_POPUP_MONOPOLY = "popup_monopoly"


class DevCard:
    """
    Base class for all development cards.
    """

    def __init__(self, just_bought: bool = False):
        self.just_bought = just_bought

    # ------------------------------------------------------------------
    # Visual attributes  (read from constants, not hardcoded per class)
    @property
    def label(self) -> str:
        return DEV_CARD_LABELS.get(self.card_type(), "Unknown Card")

    @property
    def description(self) -> str:
        return DEV_CARD_DESCRIPTIONS.get(self.card_type(), "")

    @property
    def tint(self) -> tuple:
        if self.just_bought:
            return DEV_CARD_TINTS["just_bought"]
        return DEV_CARD_TINTS.get(self.card_type(), (60, 60, 90, 255))

    # ------------------------------------------------------------------
    # Public interface
    def can_play(self, game_state: dict) -> bool:
        """
        Return True if this card is eligible to be played right now.
        Default rule: player must not have already played a card this
        turn, and the card must not have just been bought.
        """
        if self.just_bought:
            return False
        if game_state.get("played_this_turn", False):
            return False
        return True

    def apply(self, game_state: dict) -> str:
        """
        Execute the card's effect and return an ACTION_* tag.
        See individual subclasses for required game_state keys.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement apply()"
        )

    # ------------------------------------------------------------------
    # Serialisation helpers
    def to_dict(self) -> dict:
        """Convert to the plain dict format used by player.development_cards."""
        return {
            "type":        self.card_type(),
            "just_bought": self.just_bought,
        }

    @classmethod
    def card_type(cls) -> str:
        """Return the snake_case type string for this card class."""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, d: dict) -> "DevCard":
        """
        Reconstruct the correct DevCard subclass from a plain dict.
            card = DevCard.from_dict({"type": "knight", "just_bought": False})
        """
        mapping = {
            "knight":          KnightCard,
            "road_building":   RoadBuildingCard,
            "year_of_plenty":  YearOfPlentyCard,
            "monopoly":        MonopolyCard,
            "victory_point":   VictoryPointCard,
        }
        klass = mapping.get(d.get("type"))
        if klass is None:
            raise ValueError(f"Unknown dev-card type: {d.get('type')!r}")
        return klass(just_bought=d.get("just_bought", False))

    def __repr__(self):
        return f"<{self.__class__.__name__} just_bought={self.just_bought}>"


# ---------------------------------------------------------------------------
# Concrete card types
class KnightCard(DevCard):
    """
    Move the robber to any tile; optionally steal from an adjacent player.
    """

    @classmethod
    def card_type(cls) -> str:
        return "knight"

    def apply(self, game_state: dict) -> str:
        game_state["player"].__dict__["pending_robber"] = True
        return ACTION_BACK_TO_BOARD


class RoadBuildingCard(DevCard):
    """
    Place 2 free roads on the board immediately.
    """

    @classmethod
    def card_type(cls) -> str:
        return "road_building"

    def apply(self, game_state: dict) -> str:
        game_state["free_roads"] = 2
        return ACTION_BACK_TO_BOARD


class YearOfPlentyCard(DevCard):
    """
    Take any 2 resources from the bank.
    """

    @classmethod
    def card_type(cls) -> str:
        return "year_of_plenty"

    def apply(self, game_state: dict) -> str:
        return ACTION_POPUP_YOP

    @staticmethod
    def apply_resource(player, resource: str) -> None:
        """Grant one resource to the player (called twice for Year of Plenty)."""
        player.resource_cards[resource] = player.resource_cards.get(resource, 0) + 1


class MonopolyCard(DevCard):
    """
    Announce one resource; every other player gives you all of that resource.

    apply() returns ACTION_POPUP_MONOPOLY; PlayCardView opens the picker and
    calls apply_steal() once the player has chosen a resource.
    """

    @classmethod
    def card_type(cls) -> str:
        return "monopoly"

    def apply(self, game_state: dict) -> str:
        return ACTION_POPUP_MONOPOLY

    @staticmethod
    def apply_steal(players: list, current_player: int, resource: str) -> int:
        """
        Steal all of *resource* from every player except current_player.
        Returns
        int — total cards stolen (used in the notification message)
        """
        stolen = 0
        for i, p in enumerate(players):
            if i != current_player:
                amt = p.resource_cards.get(resource, 0)
                p.resource_cards[resource] = 0
                stolen += amt
        players[current_player].resource_cards[resource] = (
            players[current_player].resource_cards.get(resource, 0) + stolen
        )
        return stolen


class VictoryPointCard(DevCard):
    """
    Worth 1 VP; revealed automatically at end of game.
    Victory Point cards are NEVER manually played — can_play() always
    returns False.  The VP is granted at buy time by PlayCardView.
    """

    @classmethod
    def card_type(cls) -> str:
        return "victory_point"

    def can_play(self, game_state: dict) -> bool:
        return False

    def apply(self, game_state: dict) -> str:
        return ACTION_NONE
