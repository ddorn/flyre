from functools import lru_cache
from typing import Tuple

import pygame


def vec2int(vec):
    """Convert a 2D vector to a tuple of integers."""
    return int(vec[0]), int(vec[1])


@lru_cache()
def load_img(path, alpha=False):
    if alpha:
        return pygame.image.load(path).convert_alpha()
    return pygame.image.load(path).convert()


@lru_cache()
def get_tile(tilesheet: pygame.Surface, size, x, y, w=1, h=1):
    return tilesheet.subsurface(x * size, y * size, w * size, h * size)


def mix(color1, color2, t):
    """Mix two colors. Return color1 when t=0 and color2 when t=1."""

    return (
        round((1 - t) * color1[0] + t * color2[0]),
        round((1 - t) * color1[1] + t * color2[1]),
        round((1 - t) * color1[2] + t * color2[2]),
    )


def chrange(
    x: float, initial_range: Tuple[float, float], target_range: Tuple[float, float]
):
    """Change the range of a number by mapping the initial_range to target_range using a linear transformation."""
    normalised = (x - initial_range[0]) / (initial_range[1] - initial_range[0])
    return normalised * (target_range[1] - target_range[0]) + target_range[0]


def from_polar(r: float, angle: float):
    """Create a vector with the given polar coordinates. angle is in degrees."""
    vec = pygame.Vector2()
    vec.from_polar((r, angle))
    return vec
