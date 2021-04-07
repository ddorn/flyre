from time import time
from typing import Type

import pygame
import sys

from .gfx import GFX
from .screen import ExtendFieldOfViewScreen, Screen
from .settings import settings
from .state_machine import State, StateMachine

__all__ = ["App"]


class App(StateMachine):
    """
    The app is the largest element in the game, as it contains everything else.

    The purpose of the class is to:
        - handle the main loop
        - orchestrate the dance between the StateMachine, the Screen and the GFX

    All the game logic and randering is done by the states themselves.
    """

    FPS = 60
    NAME = "Pygame window"
    MAIN_APP: "App" = None
    MOUSE_VISIBLE = False

    def __init__(self, initial_state: Type[State], resizing: Screen):
        App.MAIN_APP = self

        self.clock = pygame.time.Clock()
        self.screen = resizing
        self.gfx = GFX(self.screen.draw_surface)
        pygame.display.set_caption(self.NAME)

        pygame.mouse.set_visible(self.MOUSE_VISIBLE)

        super().__init__(initial_state)

    def run(self):
        """The main loop of the app."""

        frame = 0
        start = time()
        while self.running:
            self.events()
            self.state.logic()
            self.state.draw(self.gfx)
            self.screen.update_window()

            pygame.display.update()
            self.clock.tick(self.FPS)

            frame += 1
            self.state = self.state.next_state

        duration = time() - start
        print(f"Game played for {duration:.2f} seconds, at {frame / duration:.1f} FPS.")
        settings.save()

    def events(self):

        events = list(pygame.event.get())
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                old = self.screen.draw_surface.get_size()
                self.screen.resize(event.size)
                self.gfx = GFX(self.screen.draw_surface)
                new = self.screen.draw_surface.get_size()
                if old != new:
                    self.state.resize(old, new)
            elif event.type in (
                pygame.MOUSEMOTION,
                pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP,
            ):
                self.screen.fixup_mouse_input(event)

        self.state.handle_events(events)

    @classmethod
    def current_state(cls):
        """Current state of the main app."""
        return cls.MAIN_APP.state

    def quit(self):
        """Properly exit the app."""

        while self.stack:
            self.state = None

        sys.exit()


if __name__ == "__main__":

    class MyState(State):
        BG_COLOR = "#60a450"

        def draw(self, gfx: GFX):
            super().draw(gfx)

            gfx.rect(0, 0, 1, 1, "blue", 1)

            # center = display.get_rect().center
            # r = pygame.Rect(0, 0, *App.MAIN_APP.DESIGN_SIZE)
            # r.center = center
            # pygame.draw.rect(display, 'red', r, 2)

    #

    pygame.init()
    # App(MyState, BlackBordersScreen((200, 100))).run()
    App(MyState, ExtendFieldOfViewScreen((200, 100))).run()
    # App(MyState, BlackBordersScreen((200, 100))).run()
