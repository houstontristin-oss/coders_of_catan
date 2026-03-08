""" 
Pure coordinate math with no side effects.
Functions: cubic_to_pixel(), node_to_pixel(), get_hex_corners().
These are stateless helpers used by both the window and ports module.
"""
import math
from .constants import HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y

def cubic_to_pixel(cx, cz, hex_size=HEX_SIZE, origin_x=BOARD_CENTER_X, origin_y=BOARD_CENTER_Y):
    """
    cubic to pixel — flat-top orientation (flat sides face top/bottom of window)
    """
    px = origin_x + hex_size * (math.sqrt(3) * cx + math.sqrt(3) / 2 * cz)
    py = origin_y + hex_size * (3 / 2) * cz
    return px, py

def node_to_pixel(node_id, hex_size=HEX_SIZE, origin_x=BOARD_CENTER_X, origin_y=BOARD_CENTER_Y):
    """
    node to pixel — flat-top orientation (flat sides face top/bottom of window)
    """
    fx, _, fz = node_id
    px = origin_x + hex_size * (math.sqrt(3) * fx + math.sqrt(3) / 2 * fz)
    py = origin_y + hex_size * (3 / 2) * fz
    return px, py

def get_hex_corners(center_x, center_y, size):
    """
    get hex corners — flat-top orientation (30 degree offset so flat sides face top/bottom)
    """
    corners = []
    for i in range(6):
        angle_rad = math.radians(60 * i + 30)
        corners.append((center_x + size * math.cos(angle_rad),
                         center_y + size * math.sin(angle_rad)))
    return corners