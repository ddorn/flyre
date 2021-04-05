from dataclasses import dataclass
from typing import Callable

import pygame

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


@Power.make("Attack up", "+10% damage to enemies", 0)
def attack_up(player):
    player.attack *= 1.1


class Node(Object):
    def __init__(self, value: Power, *children: "Node"):
        super().__init__((0, 0), (15, 15))

        self.parent = None
        self.value = value
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

        self.pos.y = depth * 40
        if self.children:
            self.pos.x = (self.children[0].pos.x + self.children[-1].pos.x) / 2
        else:
            self.pos.x = self.x_start * 40

    def draw(self, gfx: "GFX"):

        for child in self.children:
            mid_y = (self.center.y + child.center.y) / 2
            points = [
                self.center,
                (self.center.x, mid_y),
                (child.center.x, mid_y),
                child.center,
            ]
            pygame.draw.lines(gfx.surf, "white", False, points)
            child.draw(gfx)

        gfx.surf.blit(self.value.sprite, self.pos)


SKILLTREE = Node(
    attack_up,
    Node(attack_up, Node(attack_up), Node(attack_up), Node(attack_up),),
    Node(attack_up, Node(attack_up), Node(attack_up)),
    Node(attack_up),
    Node(attack_up),
)
