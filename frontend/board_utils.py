""" 
Pure coordinate math with no side effects.
Functions: cubic_to_pixel(), node_to_pixel(), get_hex_corners().
These are stateless helpers used by both the window and ports module.
"""
import math
from .constants import HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y

def cubic_to_pixel(cx, cz, hex_size=HEX_SIZE, origin_x=BOARD_CENTER_X, origin_y=BOARD_CENTER_Y):
    """
    cubic to pixel
    """
    px = origin_x + hex_size * (3 / 2) * cx
    py = origin_y + hex_size * (math.sqrt(3) / 2 * cx + math.sqrt(3) * cz)
    return px, py

def node_to_pixel(node_id, hex_size=HEX_SIZE, origin_x=BOARD_CENTER_X, origin_y=BOARD_CENTER_Y):
    """
    node to pixel
    """
    fx, _, fz = node_id
    px = origin_x + hex_size * (3 / 2) * fx
    py = origin_y + hex_size * (math.sqrt(3) / 2 * fx + math.sqrt(3) * fz)
    return px, py

def get_hex_corners(center_x, center_y, size):
    """
    get hex corners
    """
    corners = []
    for i in range(6):
        angle_rad = math.radians(60 * i)
        corners.append((center_x + size * math.cos(angle_rad),
                         center_y + size * math.sin(angle_rad)))
    return corners
