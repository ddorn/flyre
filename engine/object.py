from functools import lru_cache

import pygame

from constants import RED
from . import App, GFX
from .assets import font, rotate
from .settings import settings

__all__ = ["Object", "Entity", "SpriteObject"]


class Object:
    Z = 0

    def __init__(self, pos, size=(1, 1), vel=(0, 0)):
        self.pos = pygame.Vector2(pos)
        self.size = pygame.Vector2(size)
        self.vel = pygame.Vector2(vel)
        self.alive = True
        self.scripts = {self.script()}
        self.state = None

    def script(self):
        yield

    def wait_until_dead(self):
        while self.alive:
            yield

    @property
    def center(self):
        return self.pos + self.size / 2

    @center.setter
    def center(self, value):
        self.pos = value - self.size / 2

    @property
    def rect(self):
        return pygame.Rect(self.pos, self.size)

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
        self.state.debug.rectangle(self.rect)

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
    SCALE = 1
    INITIAL_ROTATION = -90

    def __init__(
        self,
        pos,
        image: pygame.Surface,
        offset=(0, 0),
        size=(1, 1),
        vel=(0, 0),
        rotation=0,
    ):
        # :size: is not related to the image, but to the hitbox

        super().__init__(pos, size, vel)
        if self.SCALE > 1:
            image = pygame.transform.scale(
                image, (self.SCALE * image.get_width(), self.SCALE * image.get_height())
            )
        self.base_image = image
        self.image_offset = pygame.Vector2(offset)
        self.rotation = rotation

    @property
    def angle(self):
        return (-self.rotation + self.INITIAL_ROTATION) % 360

    @angle.setter
    def angle(self, value):
        self.rotation = -value + self.INITIAL_ROTATION

    @property
    def image(self):
        return rotate(self.base_image, int(self.rotation))

    def draw(self, gfx: "GFX"):
        super().draw(gfx)
        gfx.surf.blit(self.image, self.image.get_rect(center=self.sprite_center))

    @property
    def sprite_pos(self):
        return self.pos + self.image_offset * self.SCALE

    @property
    def sprite_center(self):
        return (
            self.pos
            + self.image_offset * self.SCALE
            + pygame.Vector2(self.base_image.get_size()) / 2
        )

    def sprite_to_screen(self, pos):
        """Convert a position in the sprite to its world coordinates."""
        pos = (
            pygame.Vector2(pos)
            - pygame.Vector2(self.base_image.get_size()) / 2 / self.SCALE
        )
        pos.rotate_ip(-self.rotation)
        pos *= self.SCALE
        r = self.sprite_center + pos
        return r


class Entity(SpriteObject):
    """An object with heath and a sprite."""

    INVICIBILITY_DURATION = 0

    def __init__(
        self,
        pos,
        image: pygame.Surface,
        offset=(0, 0),
        size=(1, 1),
        vel=(0, 0),
        rotation=0,
        max_life=1000,
    ):
        super().__init__(pos, image, offset, size, vel, rotation)
        self.max_life = max_life
        self.life = max_life
        self.last_hit = 100000000

    def damage(self, amount):
        if self.invincible:
            return

        self.last_hit = 0

        self.life -= amount
        if self.life < 0:
            self.life = 0

        surf = font(20).render(str(amount), False, RED)

        from engine import ImageParticle

        App.current_state().particles.add(
            ImageParticle(surf)
            .builder()
            .at(self.center, 90)
            .velocity(1)
            .sized(10)
            .anim_fade()
            .build()
        )

    def logic(self, state):
        super().logic(state)

        self.last_hit += 1

        if self.life <= 0:
            self.alive = False

    def draw(self, gfx):
        if self.last_hit < 3:
            gfx.surf.blit(
                self.red_image(self.image),
                self.image.get_rect(center=self.sprite_center),
            )
            return

        if self.invincible and self.last_hit % 6 > 3:
            return  # no blit

        super().draw(gfx)

    @staticmethod
    @lru_cache(1000)
    def red_image(image: pygame.Surface):
        img = image.copy()
        mask = pygame.mask.from_surface(img)
        img = mask.to_surface(setcolor=RED)
        img.set_colorkey((0, 0, 0))
        return img

    @property
    def invincible(self):
        return self.last_hit < self.INVICIBILITY_DURATION
