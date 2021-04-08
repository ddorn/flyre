from pathlib import Path

import pygame

SIZE = (640, 360)
W, H = SIZE

SCREEN = pygame.Rect(0, 0, W, H)
WORLD = pygame.Rect(0, 0, W - 208, H)
INFO_RECT = pygame.Rect(WORLD.right, 0, W - WORLD.right, H)
assert INFO_RECT.width == 208

YELLOW = (255, 224, 145)
RED = (221, 55, 69)
ORANGE = (254, 174, 52)
WHITE = (192, 203, 220)
GREEN = (99, 199, 77)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
IMAGES = ASSETS_DIR / "images"
ANIMATIONS = ASSETS_DIR / "animations"
FONTS = ASSETS_DIR / "fonts"
MUSIC = ASSETS_DIR / "music"
SFX = ASSETS_DIR / "sfx"

print("Assets:", ASSETS_DIR)
print("Images:", IMAGES)

UPWARDS = -90  # degrees
DOWNWARDS = 90  # degrees

DEBUG = False


# Joystick buttons id on my joystick (xbox)
JOY_A = 0
JOY_B = 1
JOY_X = 2
JOY_Y = 3
JOY_BACK = 6
JOY_START = 7
# Joystick axis id on my joystick (xbox)
JOY_HORIZ_LEFT = 0
JOY_HORIZ_RIGHT = 3
JOY_VERT_LEFT = 1
JOY_VERT_RIGHT = 4
JOY_RL = 2
JOY_RT = 5
