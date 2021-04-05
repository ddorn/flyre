from dataclasses import dataclass
from typing import Callable

import pygame

from constants import YELLOW
from engine import Object
from engine.assets import tilemap
from objects import Player


@dataclass
class Power:
    sprite_index: int
    description: str
    name: str
    effect: Callable[[Player], None]
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


@Power.make("Attack up", "+10% damage to enemies", 0)
def attack_up(player):
    player.attack *= 1.1


@Power.make("Bullets up", "Shoot one more bullet.", 1)
def bullets_up(player):
    pass


@Power.make("Bullet speed up", "Bullets go 10% faster", 3)
def bullet_speed_up(player):
    pass


@Power.make("Critical hit probability", "+10% of critical hits", 7)
def crit_prob(player):
    pass


@Power.make("Critical hit damage", "+20% of damage for critical hits", 8)
def crit_dmg(player):
    pass


@Power.make("Regeneration", "Regenerate 1% of life every 5s", 10)
def regen(player):
    pass


@Power.make("Life up", "+10% of life", 11)
def life_up(player):
    pass


@Power.make("Fire attack", "+20% probability of burning the target", 12)
def fire_atk(player):
    pass


@Power.make("Fire damage", "+100% fire damage", 13)
def fire_dmg(player):
    pass


@Power.make("Fire duration", "Fire last +1s", 14)
def fire_duration(player):
    pass


@Power.make("Shield", "Activate shield with X.", 15)
def shield(player):
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
