from typing import Tuple

import pygame


__all__ = [
    "Screen",
    "FixedScreen",
    "FreeScreen",
    "BlackBordersScreen",
    "IntegerScaleScreen",
    "ExtendFieldOfViewScreen",
]


class Screen:
    FLAGS = pygame.RESIZABLE

    draw_surface: pygame.Surface
    window_size: Tuple[int, int]
    window: pygame.Surface

    def resize(self, new_size=None):
        self.window = pygame.display.set_mode(new_size or self.window_size, self.FLAGS)
        self.window_size = (
            self.window.get_size()
        )  # We don't always get the size asked for.
        self.draw_surface = self.window

    def update_window(self):
        """Transfer the contents of the draw_surface to the window.
         Called every frame before pygame.display.flip()."""

    def fixup_mouse_input(self, event):
        """Fix the mouse events to take any resizing into account."""

    def _biggest_screen_available(self):
        return pygame.display.list_modes()[0]


class FixedScreen(Screen):
    FLAGS = 0

    def __init__(self, size):
        self.window_size = size

    def resize(self, new_size=None):
        super().resize(None)


class FreeScreen(Screen):
    def __init__(self, size=None):
        self.window_size = size or pygame.display.list_modes()[0]
        self.resize()


class IntegerScaleScreen(Screen):
    FLAGS = pygame.SCALED | pygame.RESIZABLE

    def __init__(self, design_size):
        self.design_size = design_size
        self.window = pygame.display.set_mode(self.design_size, self.FLAGS)
        self.window_size = self.window.get_size()
        self.draw_surface = self.window

    def resize(self, new_size=None):
        pass  # pygame does everything or use with SCALED


class BlackBordersScreen(Screen):
    def __init__(self, design_size, border_color="black"):
        self.border_color = border_color
        self.design_size = pygame.Vector2(design_size)
        self.window_size = self._biggest_screen_available()
        self.scaled_draw_rect = pygame.Rect(0, 0, 0, 0)
        self.resize()
        self.draw_surface = pygame.Surface(self.design_size)

    @property
    def scale(self):
        return min(
            self.window_size[0] / self.design_size[0],
            self.window_size[1] / self.design_size[1],
        )

    def resize(self, new_size=None):
        self.window = pygame.display.set_mode(new_size or self.window_size, self.FLAGS)
        self.window.fill(self.border_color)
        self.window_size = (
            self.window.get_size()
        )  # We don't always get the size asked for.

        scaled_draw_area = self.design_size * self.scale
        topleft = (pygame.Vector2(self.window_size) - scaled_draw_area) / 2
        self.scaled_draw_rect = pygame.Rect(topleft, scaled_draw_area)

        print(self.scaled_draw_rect, self.window)

    def update_window(self):
        scaled_draw = self.window.subsurface(self.scaled_draw_rect)
        pygame.transform.scale(
            self.draw_surface, self.scaled_draw_rect.size, scaled_draw
        )

    def fixup_mouse_input(self, event):
        # noinspection PyTypeChecker
        event.pos = (
            pygame.Vector2(event.pos) - self.scaled_draw_rect.topleft
        ) // self.scale


class ExtendFieldOfViewScreen(Screen):
    """
    A type of screen that scales only by an interger multiple,
    but the usualy black border space is left to the application to draw on to.

    The draw surface always covers the whole screen and one of its dimensions
    is at least less than 2x the prefered_size.
    """

    def __init__(self, prefered_size):
        self.prefered_size = prefered_size
        self.window_size = self._biggest_screen_available()
        self.scaled_draw_rect = pygame.Rect(0, 0, 0, 0)
        self.resize()

    @property
    def scale(self):
        return max(
            1,
            min(
                self.window_size[0] // self.prefered_size[0],
                self.window_size[1] // self.prefered_size[1],
            ),
        )

    def resize(self, new_size=None):
        self.window = pygame.display.set_mode(new_size or self.window_size, self.FLAGS)
        self.window_size = (
            self.window.get_size()
        )  # We don't always get the size asked for.
        self.window.fill("black")

        # We round the window_size to the nearest multiple
        scaled_draw_area = pygame.Vector2(self.window_size) // self.scale * self.scale
        topleft = (pygame.Vector2(self.window_size) - scaled_draw_area) // 2
        self.scaled_draw_rect = pygame.Rect(topleft, scaled_draw_area)
        self.draw_surface = pygame.Surface(scaled_draw_area // self.scale)

    def update_window(self):
        scaled_draw = self.window.subsurface(self.scaled_draw_rect)
        pygame.transform.scale(
            self.draw_surface, self.scaled_draw_rect.size, scaled_draw
        )

    def fixup_mouse_input(self, event):
        # noinspection PyTypeChecker
        event.pos = (
            pygame.Vector2(event.pos) - self.scaled_draw_rect.topleft
        ) // self.scale
