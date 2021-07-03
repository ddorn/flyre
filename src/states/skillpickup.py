from pygame.locals import *

from src.objects import Node
from src.engine import *
from src.engine.pygame_input import Button, clamp
from .my_state import MyState


class SkillPickUp(MyState):
    def __init__(self, player):
        super().__init__()

        self.player = player
        self.tree.power.selected = True

        self.error_message = ""
        self.error_timer = -1

    def create_inputs(self):
        inputs = super().create_inputs()
        inputs["left"] = Button(
            K_LEFT,
            K_d,
            JoyAxisTrigger(JOY_HORIZ_LEFT, -0.5, False),
            JoyAxisTrigger(JOY_HORIZ_RIGHT, -0.5, False),
        )
        inputs["left"].on_press(lambda _: self.go_to_sibling(-1))

        inputs["right"] = Button(
            K_RIGHT,
            K_a,
            JoyAxisTrigger(JOY_HORIZ_LEFT),
            JoyAxisTrigger(JOY_HORIZ_RIGHT),
        )
        inputs["right"].on_press(lambda _: self.go_to_sibling(+1))

        inputs["down"] = Button(
            K_DOWN, K_s, JoyAxisTrigger(JOY_VERT_LEFT), JoyAxisTrigger(JOY_VERT_RIGHT)
        )
        inputs["down"].on_press(self.go_child)

        inputs["up"] = Button(
            K_UP,
            K_w,
            JoyAxisTrigger(JOY_VERT_LEFT, -0.5, False),
            JoyAxisTrigger(JOY_VERT_RIGHT, -0.5, False),
        )
        inputs["up"].on_press(self.go_parent)

        inputs["select"] = Button(
            K_SPACE, K_RETURN, JoyButton(JOY_A), JoyButton(JOY_START)
        )
        inputs["select"].on_press(self.select)

        return inputs

    def error(self, msg):
        play("denied")
        self.do_shake(5)
        self.error_message = msg
        self.error_timer = 2 * 60

    def selected(self):
        for node in self.tree.bfs():
            if node.power.selected:
                return node
        raise ValueError("No node is selected")

    def select(self, *args):
        play("powerup")
        current = self.selected()
        current.power.apply(self.player)
        self.pop_state()

    def go_parent(self, *args):
        current = self.selected()
        if current.parent:
            play("menu")
            current.power.selected = False
            current.parent.power.selected = True
        else:
            play("no")

    def go_child(self, *args):
        current = self.selected()
        if current.children:
            idx = (len(current.children) - 1) // 2
            child = current.children[idx]

            if child.reachable():
                play("menu")
                child.power.selected = True
                current.power.selected = False
            else:
                msg = (
                    ("Unlock ", RED),
                    (current.power.name, YELLOW),
                    (" before higher level skills.", RED),
                )
                self.error(msg)
        else:
            play("no")

    def go_to_sibling(self, offset):
        current = self.selected()
        if current.parent:
            siblings = current.parent.children
            idx = siblings.index(current)
            new = clamp(idx + offset, 0, len(siblings) - 1)
            current.power.selected = False
            siblings[new].power.selected = True

            if new != idx:
                play("menu")
            else:
                play("no")
        else:
            play("no")

    def on_exit(self):
        super().on_exit()
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

        # Bottom backgorund
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
            # Skills name/description
            current = self.selected()
            s = text(current.power.name, 20, YELLOW)
            r: Rect = gfx.blit(s, midtop=(W / 2, bottom_rect.y + 6))

            r_right = r.move(6, 0)
            r_left = r.move(-6, 0)

            star = tilemap("sprites", 4, 0, 16)
            for i in range(current.power.level):
                r_right = gfx.blit(star, midleft=r_right.midright)
                r_left = gfx.blit(star, midright=r_left.midleft)

            s = text(current.power.description, 14, WHITE, "pixelmillennium")
            gfx.blit(s, midtop=r.midbottom)
