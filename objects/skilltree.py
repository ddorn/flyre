from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

import pygame

from constants import UPWARDS, YELLOW
from engine import Object
from engine.assets import tilemap
from engine.utils import random_in_rect, random_in_surface

if TYPE_CHECKING:
    from objects import SpaceShip
    from objects.player import Player


@dataclass
class Power:
    sprite_index: int
    description: str
    name: str
    effect: Callable[["Player"], None]
    level: int = 0

    @classmethod
    def make(cls, name, description, sprite_index):
        def wrapper(effect):
            return cls(sprite_index, description, name, effect)

        return wrapper

    @property
    def sprite(self):
        return tilemap("sprites", self.sprite_index, 4, 16)

    @property
    def background(self):
        return tilemap("sprites", 0, 3, 32)

    def draw(self, gfx, pos):
        bg = self.background
        r = self.sprite.get_rect(topleft=pos)
        gfx.surf.blit(bg, bg.get_rect(center=r.center))
        gfx.surf.blit(self.sprite, r)


@Power.make("Attack up", "+20% damage to enemies", 0)
def attack_up(player):
    player.bullet_damage *= 1.2


@Power.make("Bullets up", "Shoot one more bullet.", 1)
def bullets_up(player):
    player.nb_bullets += 1


@Power.make("Bullet speed up", "Bullets go 10% faster", 3)
def bullet_speed_up(player):
    player.bullet_speed *= 1.1


@Power.make("Critical hit probability", "+1% of critical hits", 7)
def crit_prob(player):
    player.crit_chance += 0.01


@Power.make("Critical hit damage", "+1 to critical hit damage multiplier", 8)
def crit_dmg(player):
    player.crit_mult += 0.5


@Power.make("Regeneration", "Regenerate 1% of life every 5s", 10)
def regen(player):
    for buff in player.debuffs:
        if isinstance(buff, RegenDebuff):
            buff.strength += 0.01
            return
    player.debuffs.add(RegenDebuff(1000000000000000, 0.01))


@Power.make("Life up", "+10% of life", 11)
def life_up(player):
    to_add = player.max_life * 0.1
    player.max_life += to_add
    player.life += to_add


@Power.make("Fire attack", "+2% probability of burning the target", 12)
def fire_atk(player):
    player.fire_chance += 0.02


@Power.make("Fire damage", "+1 to the fire damage multiplier", 13)
def fire_dmg(player):
    player.fire_dmg += 0.1  # this is not a typo, the base multipler is 0.1, not 1.


@Power.make("Fire duration", "Fire last +0.5s", 14)
def fire_duration(player):
    player.fire_duration += 30


@Power.make("Shield", "Activate shield with X.", 15)
def shield(player):
    # TODO: idk how to do the shield
    pass


class Node(Object):
    def __init__(self, value: Power, *children: "Node"):
        super().__init__((0, 0), (15, 15))

        self.parent = None
        self.power = value
        self.children = children

        for child in self.children:
            child.parent = self

        # For the layout
        self.x_start = 0
        self.x_end = 0

    def bfs(self):
        yield self
        for child in self.children:
            yield from child.bfs()

    def layout(self, topleft):
        self.layout_phase1()
        self.layout_phase2()

        for node in self.bfs():
            node.pos += topleft

    def layout_phase1(self):
        x = self.x_start
        for child in self.children:
            child.x_start = x
            child.layout_phase1()
            x = child.x_end + 1

        if self.children:
            self.x_end = x - 1
        else:
            self.x_end = self.x_start

    def layout_phase2(self, depth=0):
        for child in self.children:
            child.layout_phase2(depth + 1)

        self.pos.y = depth * 35
        if self.children:
            self.pos.x = (self.children[0].pos.x + self.children[-1].pos.x) / 2
        else:
            self.pos.x = self.x_start * 35

    def draw(self, gfx: "GFX"):

        for child in self.children:
            mid_y = (self.center.y + child.center.y) / 2
            points = [
                self.center,
                (self.center.x, mid_y),
                (child.center.x, mid_y),
                child.center,
            ]
            pygame.draw.lines(gfx.surf, YELLOW, False, points)
            child.draw(gfx)

        self.power.draw(gfx, self.pos)


SKILLTREE = Node(
    bullets_up,
    Node(life_up, Node(regen), Node(shield)),
    Node(attack_up, Node(crit_dmg), Node(crit_prob)),
    Node(fire_atk, Node(fire_dmg), Node(fire_duration)),
)


class Debuff:
    duration: int

    def __init__(self, duration):
        self.duration = duration

    def apply(self, ship):
        self.duration -= 1

    @property
    def done(self):
        return self.duration <= 0


class FireDebuff(Debuff):
    def __init__(self, duration, damage):
        super().__init__(duration)
        self.damage = damage

    def apply(self, ship: "SpaceShip"):
        super().apply(ship)

        if self.duration % 10 == 0:
            ship.damage(self.damage)

        for _ in range(6):
            pos = pygame.Vector2(random_in_surface(ship.image))
            pos += ship.image.get_rect(center=ship.center).topleft
            ship.state.particles.add_fire_particle(pos, 180 + ship.angle)


class RegenDebuff(Debuff):
    def __init__(self, duration, strength):
        super().__init__(duration)
        self.strength = strength

    def apply(self, ship):
        super().apply(ship)

        if self.duration % 60 == 0:
            ship.heal(ship.max_life * self.strength)
