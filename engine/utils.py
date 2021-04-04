from functools import lru_cache
from random import uniform
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
    x: float,
    initial_range: Tuple[float, float],
    target_range: Tuple[float, float],
    power=1,
    flipped=False,
):
    """Change the range of a number by mapping the initial_range to target_range using a linear transformation."""
    normalised = (x - initial_range[0]) / (initial_range[1] - initial_range[0])
    normalised **= power
    if flipped:
        normalised = 1 - normalised
    return normalised * (target_range[1] - target_range[0]) + target_range[0]


def from_polar(r: float, angle: float):
    """Create a vector with the given polar coordinates. angle is in degrees."""
    vec = pygame.Vector2()
    vec.from_polar((r, angle))
    return vec


def clamp(x, mini, maxi):
    if x < mini:
        return mini
    if x > maxi:
        return maxi
    return x


def angle_towards(start, goal, max_movement):
    """Return the angle towards goal that is a most max_movement for the start."""
    start %= 360
    goal %= 360

    if abs(start - goal) > 180:
        return start + clamp(start - goal, -max_movement, max_movement)
    else:
        return start + clamp(goal - start, -max_movement, max_movement)


def random_in_rect(rect: pygame.Rect, x_range=(0.0, 1.0), y_range=(0.0, 1.0)):
    """Return a random point inside a rectangle.

    If x_range or y_range are given, they are interpreted as relative to the size of the rectangle.
    For instance, a x_range of (-1, 3) would make the x range in a rectangle that is 3 times wider,
    but still centered at the same position. (-2, 1) you expand the rectangle twice its size on the
    left.
    """
    w, h = rect.size

    return (
        uniform(rect.x + w * x_range[0], rect.x + w * x_range[1]),
        uniform(rect.y + h * y_range[0], rect.y + h * y_range[1]),
    )


def clamp_length(vec, maxi):
    """Scale the vector so it has a length of at most :maxi:"""

    if vec.length() > maxi:
        vec.scale_to_length(maxi)

    return vec


def part_perp_to(u, v):
    """Return the part of u that is perpendicular to v"""
    if v.length_squared() == 0:
        return u

    v = v.normalize()
    return u - v * v.dot(u)
