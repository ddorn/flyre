import pygame

from .settings import settings

__all__ = ["Object"]


class Object:
    Z = 0

    def __init__(self, pos, size=(1, 1), vel=(0, 0)):
        self.pos = pygame.Vector2(pos)
        self.size = pygame.Vector2(size)
        self.vel = pygame.Vector2(vel)
        self.alive = True
        self.scripts = set()

    @property
    def center(self):
        return self.pos + self.size / 2

    @center.setter
    def center(self, value):
        self.pos = value - self.size / 2

    def logic(self, state):
        """Overwrite this to update the object every frame.

        Args:
            state (State): Current state of the app
        """

        self.pos += self.vel

        to_remove = set()
        for script in self.scripts:
            try:
                next(script)
            except StopIteration:
                to_remove.add(script)
        self.scripts.difference_update(to_remove)

    def draw(self, gfx: "GFX"):
        if settings.debug:
            gfx.rect(*self.pos, *self.size, "red", 1)

    def on_death(self, state):
        """Overwrite this to have a logic when the object dies.

        Args:
            state (State): Current state of the app.
        """

    def resize(self, old, new):
        """Called every time the window resizes.

        This should not have any impoact on position/speed,
        as they should not depend on the window size. Instead
        this should handle the different sprite sizes.
        Args:
            old (pygame.Vector2): previous size of the window
            new (pygame.Vector2): actual size of the window
        """


class SpriteObject(Object):
    def __init__(
        self, pos, image: pygame.Surface, offset=(0, 0), size=(1, 1), vel=(0, 0)
    ):
        super().__init__(pos, size, vel)
        self.image = image
        self.image_offset = pygame.Vector2(offset)

    def draw(self, gfx):
        gfx.surf.blit(
            self.image, self.image.get_rect(topleft=self.pos + self.image_offset)
        )

    @property
    def sprite_pos(self):
        return self.pos + self.image_offset
