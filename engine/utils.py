from contextlib import contextmanager
from functools import lru_cache
from math import cos, exp, sin
from random import random, randrange, uniform
from time import time
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
    """Return the angle towards goal that is a most max_movement degrees from the start angle."""
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


def random_in_surface(surf: pygame.Surface, max_retries=100):
    """Return a random point that is not transparent in a surface.

    After max_retry, returns the center of the surface.
    """
    w, h = surf.get_size()
    color_key = surf.get_colorkey()
    with lock(surf):
        for _ in range(max_retries):
            pos = randrange(w), randrange(h)
            color = surf.get_at(pos)
            if not (color == color_key or color[3] == 0):
                # Pixel is not transparent.
                return pos
        return (w // 2, h // 2)


@contextmanager
def lock(surf):
    """A simple context manager to automatically lock and unlock the surface."""
    surf.lock()
    try:
        yield
    finally:
        surf.unlock()


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


def prop_in_rect(rect: pygame.Rect, prop_x: float, prop_y: float):
    """Return the point in a rectangle defined by the proportion.

    Examples:
        (0, 0) => topleft
        (1/3, 1/3) => point at the first third of the rect
        (-1, 0) => point on the top-line and one width on the leftj
    """

    return rect.x - rect.w * prop_x, rect.y - rect.h * prop_y


def bounce(x, f=0.2, k=60):
    """Easing function that bonces over 1 and then stabilises around 1.

    Graph:
         │   /^\
        1│  /   `------
        0│ /
         ┼———————————————
           0 f        1

    Args:
        x: The time to animate, usually between 0 and 1, but can be greater than one.
        f: Time to grow to 1
        k: Strength of the bump after it has reached 1
    """

    s = max(x - f, 0.0)
    return min(x * x / (f * f), 1 + (2.0 / f) * s * exp(-k * s))


def exp_impulse(x, k):
    """
    Easing function that rises quickly to one and slowly goes back to 0.

    Graph:
        1│   /^\
         │  /    \
        0│ /      `-_
         ┼————┼——————————
           0  │    1
              ╰ 1/k

    Args:
        x: The time to animate, usually between 0 and 1, but can be greater than one.
        k: Control the stretching of the function

    Returns: a float between 0 and 1.
    """

    h = k * x
    return h * exp(1.0 - h)


def auto_crop(surf: pygame.Surface):
    """Return the smallest subsurface of an image that contains all the visible pixels."""

    rect = surf.get_bounding_rect()
    return surf.subsurface(rect)
