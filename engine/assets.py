import json
from functools import lru_cache

import pygame

from constants import *
from engine.utils import overlay

VOLUMES = {"shoot": 0.4, "denied": 0.8, "hit": 0.7}


@lru_cache()
def _play(name):
    file = SFX / (name + ".wav")
    sound = pygame.mixer.Sound(file)

    sound.set_volume(VOLUMES.get(name, 1.0) * 0.1)

    return sound


def play(name: str):
    sound = _play(name)
    sound.stop()
    sound.play()


@lru_cache()
def image(name: str):
    file = IMAGES / (name + ".png")
    img = pygame.image.load(file)

    if name.startswith("planet"):
        return overlay(img, (0, 0, 0, 100))
    return img


@lru_cache(10000)
def rotate(image, degrees):
    return pygame.transform.rotate(image, degrees)


@lru_cache(1000)
def scale(image, factor):
    size = factor * image.get_width(), factor * image.get_height()
    return pygame.transform.scale(image, size)


@lru_cache()
def font(size: int, name: str = None):
    name = name or "Wellbutrin"
    file = FONTS / (name + ".ttf")
    return pygame.font.Font(file, size)


@lru_cache(10000)
def text(txt, size, color, name=None):
    return font(size, name).render(txt, False, color)


@lru_cache(1000)
def colored_text(size, *parts, name=None):
    surfaces = []
    for txt, color in parts:
        s = text(txt, size, color, name)
        surfaces.append(s)

    w = sum(s.get_width() for s in surfaces)
    h = max(s.get_height() for s in surfaces)
    output = pygame.Surface((w, h))
    output.set_colorkey((0, 0, 0))

    x = 0
    for surf in surfaces:
        output.blit(surf, (x, 0))
        x += surf.get_width()

    return output


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

    def __len__(self):
        """Number of frames for one full loop."""
        return self.frame_nb * self.frame_duration

    def logic(self):
        self.timer += 1

    def image(self):
        time = self.timer % len(self)
        frame_nb = time // self.frame_duration
        return tilemap(self.name, frame_nb, 0, self.tile_size)
