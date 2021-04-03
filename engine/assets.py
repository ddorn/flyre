import itertools
import json
from bisect import bisect_left, bisect_right
from functools import lru_cache
from pathlib import Path

import pygame

from constants import *


@lru_cache()
def image(name: str):
    file = IMAGES / (name + ".png")
    return pygame.image.load(file)


@lru_cache(10000)
def rotate(image, degrees):
    return pygame.transform.rotate(image, degrees)


@lru_cache()
def font(name: str, size: int):
    file = ASSETS_DIR / "fonts" / (name + ".ttf")
    return pygame.font.Font(file, size)


@lru_cache()
def tilemap(name, x, y, tile_size=32):
    img = image(name)
    w = img.get_width()

    # Wrap x when bigger than line length
    tiles_in_a_row = w // tile_size
    y += x // tiles_in_a_row
    x %= tiles_in_a_row

    return img.subsurface((x * tile_size, y * tile_size, tile_size, tile_size))


class Animation:
    def __init__(self, name: str, override_frame_duration=None, flip_x=False):
        self.timer = 0
        self.name = name

        data = ANIMATIONS / (self.name + ".json")
        data = json.loads(data.read_text())

        self.tile_size = data["tile_size"]
        self.frame_nb = data["length"]
        self.frame_duration = override_frame_duration or data["duration"]
        self.flip_x = flip_x

        print(data)

    def __len__(self):
        """Number of frames for one full loop."""
        return self.frame_nb * self.frame_duration

    def logic(self):
        self.timer += 1

    def image(self):
        time = self.timer % len(self)
        frame_nb = time // self.frame_duration
        return tilemap(self.name, frame_nb, 0, self.tile_size)
