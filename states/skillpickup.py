import pygame
from pygame.locals import *

from constants import H, ORANGE, RED, SCREEN, W, WHITE, YELLOW
from engine import GFX
from engine.assets import colored_text, text
from engine.pygame_input import Button, clamp
from objects.skilltree import Node
from states.my_state import MyState


class SkillPickUp(MyState):
    def __init__(self, player):
        super().__init__()

        self.player = player
        self.tree.power.selected = True

        self.error_message = ""
        self.error_timer = -1

    def create_inputs(self):
        inputs = super().create_inputs()
        inputs["left"] = Button(K_LEFT, K_d)
        inputs["left"].on_press(lambda _: self.go_to_sibling(-1))

        inputs["right"] = Button(K_RIGHT, K_a)
        inputs["right"].on_press(lambda _: self.go_to_sibling(+1))

        inputs["down"] = Button(K_DOWN, K_s)
        inputs["down"].on_press(self.go_child)

        inputs["up"] = Button(K_UP, K_w)
        inputs["up"].on_press(self.go_parent)

        inputs["select"] = Button(K_SPACE, K_RETURN)
        inputs["select"].on_press(self.select)

        return inputs

    def error(self, msg):
        self.do_shake(5)
        self.error_message = msg
        self.error_timer = 2 * 60

    def selected(self):
        for node in self.tree.bfs():
            if node.power.selected:
                return node
        raise ValueError("No node is selected")

    def select(self, *args):
        current = self.selected()
        current.power.apply(self.player)
        # self.next_state = None

    def go_parent(self, *args):
        current = self.selected()
        if current.parent:
            current.power.selected = False
            current.parent.power.selected = True

    def go_child(self, *args):
        current = self.selected()
        if current.children:
            idx = (len(current.children) - 1) // 2
            child = current.children[idx]

            if child.reachable():
                child.power.selected = True
                current.power.selected = False
            else:
                msg = (
                    ("Unlock ", RED),
                    (current.power.name, YELLOW),
                    (" before higher level skills.", RED),
                )
                self.error(msg)

    def go_to_sibling(self, offset):
        current = self.selected()
        if current.parent:
            siblings = current.parent.children
            idx = siblings.index(current)
            idx = clamp(idx + offset, 0, len(siblings) - 1)
            current.power.selected = False
            siblings[idx].power.selected = True

    def on_exit(self):
        for node in self.tree.bfs():
            node.power.selected = False

    @property
    def tree(self) -> Node:
        return self.player.skill_tree

    def logic(self):
        super().logic()
        self.error_timer -= 1

    def draw(self, gfx: "GFX"):
        super().draw(gfx)

        s = text("Choose your next skill", 40, ORANGE)
        gfx.blit(s, midtop=(W / 2, 32))

        self.tree.layout((SCREEN.centerx, 150), 64, 64)
        self.tree.draw(gfx, 2)

        bottom_rect = pygame.Rect(0, H - 54, W, 54)
        gfx.box(bottom_rect, (0, 0, 0, 180))
        pygame.draw.line(gfx.surf, YELLOW, bottom_rect.topright, bottom_rect.topleft)

        if self.error_timer > 0:
            if isinstance(self.error_message, str):
                s = text(self.error_message, 20, RED)
            else:
                s = colored_text(20, *self.error_message)
            gfx.blit(s, center=bottom_rect.center)
        else:
            current = self.selected()
            s = text(current.power.name, 20, YELLOW)
            r = gfx.blit(s, midtop=(W / 2, bottom_rect.y + 6))

            s = text(current.power.description, 15, WHITE, "pixelmillennium")
            gfx.blit(s, midtop=r.midbottom)
