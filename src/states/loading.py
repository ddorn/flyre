import os
from glob import glob
from time import time

from src.engine import *
from .my_state import MyState
from .menu import MenuState
from ..objects import Text


class LoadingState(State):
    FPS = 500

    BG_COLOR = MyState.BG_COLORS[0]

    def __init__(self):
        super().__init__()
        self.images = list(IMAGES.glob("*.png"))
        self.progress = 0
        self.debug.enabled = 0

        self.add(Text(GAME_NAME, YELLOW, TITLE_SIZE, center=(W / 2, H / 3)))

    def script(self):
        start = time()
        for path in self.images:
            self.progress += 1
            image(Path(path).stem)
            self.debug.text(f"Loading: {path}")
            yield

        end = time()
        print(f"Loading done in {round(end - start, 2)}s!")

        # So they can the the 100% load
        for _ in range(100):
            yield
        self.replace_state(MenuState())

    def draw(self, gfx: "GFX"):
        super().draw(gfx)
        start = W / 3
        end = W * 2 / 3
        y = H * 2 / 3
        height = 10
        prop = self.progress / len(self.images)
        r = (start, y - height / 2, (end - start) * prop, height)
        gfx.box(r, YELLOW)
        gfx.rect(start, y - height / 2 - 1, end - start, height + 2, YELLOW, 1)

        # s = text(f"{round(prop * 100)}%", 14, YELLOW)
        # gfx.blit(s, midleft=(end + 10, y))
