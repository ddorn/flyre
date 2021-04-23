from random import gauss
from typing import Optional, TYPE_CHECKING

import pygame

from .gfx import GFX
from .assets import font, rotate
from .constants import GREEN, RED
from .particles import ImageParticle

if TYPE_CHECKING:
    from . import State

__all__ = ["Object", "Entity", "SpriteObject", "Scriptable"]

from .utils import overlay, random_in_rect, random_rainbow_color


class Scriptable:
    def __init__(self):
        self.scripts = set()

    def add_script(self, generator):
        self.scripts.add(generator)

    def logic(self):
        to_remove = set()
        for script in self.scripts:
            try:
                next(script)
            except StopIteration:
                to_remove.add(script)
        self.scripts.difference_update(to_remove)

    def do_later(self, nb_of_frames):
        """Decorator to automatically call a function :nb_of_frames: later."""
        def decorator(func):
            def script():
                yield from range(nb_of_frames)
                func()
            self.add_script(script())
            return func
        return decorator

class Object(Scriptable):
    Z = 0

    def __init__(self, pos, size=(1, 1), vel=(0, 0)):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.size = pygame.Vector2(size)
        self.vel = pygame.Vector2(vel)
        self.alive = True
        self.scripts = {self.script()}
        self.state: Optional["State"] = None

        # A somewhat unique color per object, that can be used for debugging
        self._random_color = random_rainbow_color(80)

    def __str__(self):
        return f"{self.__class__.__name__}(at {self.pos})"

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

    def logic(self):
        """Overwrite this to update the object every frame.

        """

        super().logic()

        self.pos += self.vel

        self.state.debug.rectangle(self.rect, self._random_color)
        self.state.debug.vector(self.vel * 10, self.center, self._random_color)

    def draw(self, gfx: "GFX"):
        pass

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

    def create_inputs(self):
        """Return an Input object that handles events for the object."""
        return {}


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
            + (0.5, 0.5)  # To get the center of the pixel
            - pygame.Vector2(self.base_image.get_size()) / 2 / self.SCALE
        )
        pos.rotate_ip(-self.rotation)
        pos *= self.SCALE
        r = self.sprite_center + pos
        return r


class Entity(SpriteObject):
    """An object with heath and a sprite."""

    INVICIBILITY_DURATION = 0
    INITIAL_LIFE = 1000

    def __init__(
        self,
        pos,
        image: pygame.Surface,
        offset=(0, 0),
        size=(1, 1),
        vel=(0, 0),
        rotation=0,
    ):
        super().__init__(pos, image, offset, size, vel, rotation)
        self.max_life = self.INITIAL_LIFE
        self.life = self.INITIAL_LIFE
        self.last_hit = 100000000

    def heal(self, amount):
        if self.life + amount > self.max_life:
            amount = self.max_life - self.life

        if amount <= 0:
            return

        self.life += amount

        surf = font(20).render(str(int(amount)), False, GREEN)
        pos = random_in_rect(self.rect)
        self.state.particles.add(
            ImageParticle(surf)
            .builder()
            .at(pos, 90)
            .velocity(0)
            .sized(15)
            .anim_fade(0.5)
            .anim_bounce_size_and_shrink()
            .build()
        )

    def damage(self, amount, ignore_invincibility=False):
        if amount < 0:
            self.heal(amount)
            return

        if self.invincible and not ignore_invincibility:
            return

        amount *= gauss(1, 0.1)

        self.last_hit = 0

        self.life -= amount
        if self.life < 0:
            self.life = 0

        surf = font(20).render(str(int(amount)), False, RED)

        from src.engine import ImageParticle

        pos = random_in_rect(self.rect)
        self.state.particles.add(
            ImageParticle(surf)
            .builder()
            .at(pos, 90)
            .velocity(0)
            .sized(15)
            .anim_fade(0.5)
            .anim_bounce_size()
            .build()
        )

    def logic(self):
        super().logic()

        self.last_hit += 1

        if self.life <= 0:
            self.alive = False

    def draw(self, gfx):
        if self.last_hit < 3:
            gfx.surf.blit(
                overlay(self.image, RED),
                self.image.get_rect(center=self.sprite_center),
            )
            return

        if self.invincible and self.last_hit % 6 > 3:
            return  # no blit

        super().draw(gfx)

    @property
    def invincible(self):
        return self.last_hit < self.INVICIBILITY_DURATION
