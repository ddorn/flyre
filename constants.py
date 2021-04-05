from pathlib import Path

import pygame

SIZE = (640, 360)
W, H = SIZE

WORLD = pygame.Rect(0, 0, W * 2 / 3, H)
INFO_RECT = pygame.Rect(WORLD.right, 0, W - WORLD.right, H)

YELLOW = (255, 224, 145)
RED = (221, 55, 69)
GREEN = (99, 199, 77)

ASSETS_DIR = Path(__file__).parent / "assets"
IMAGES = ASSETS_DIR / "images"
ANIMATIONS = ASSETS_DIR / "animations"
FONTS = ASSETS_DIR / "fonts"

UPWARDS = -90  # degrees
DOWNWARDS = 90  # degrees

DEBUG = False
