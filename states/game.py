from pygame import Vector2
from random import shuffle, uniform

from constants import *
from engine import GFX, ParticleFountain, SquareParticle
from engine.assets import font, image
from engine.pygame_input import Axis, Button
from engine.state_machine import State
from engine.utils import auto_crop, mix, random_in_rect
from level import LEVELS
from objects import Planet, Title
from objects.player import Player
from objects.skilltree import SKILLTREE
from states.my_state import MyState


class GameState(MyState):
    def __init__(self):
        super().__init__()

        self.player = self.add(Player((100, 200)))

        self.skill_tree = SKILLTREE
        self.skill_tree.layout((WORLD.right + 9, 201))

        self.running_script = self.script()

    def create_inputs(self):
        inputs = super().create_inputs()
        inputs["horizontal"] = Axis(
            [pygame.K_a, pygame.K_LEFT], [pygame.K_d, pygame.K_RIGHT]
        )
        inputs["horizontal"].always_call(self.player.move_horizontally)

        inputs["vertical"] = Axis(
            [pygame.K_w, pygame.K_UP], [pygame.K_s, pygame.K_DOWN]
        )
        inputs["vertical"].always_call(self.player.move_vertically)

        inputs["fire"] = Button(pygame.K_SPACE)
        inputs["fire"].on_press_repeated(lambda _: self.player.fire(self), 0.1)

        inputs["pause"] = Button(pygame.K_p)
        inputs["pause"].on_press(self.set_pause)

        return inputs

    def set_pause(self, *args):
        from states.pause import PauseState

        self.next_state = PauseState(self)

    def on_resume(self):
        super().on_resume()
        self.debug.paused = False

    def on_exit(self):
        self.debug.paused = True

    def logic(self):

        next(self.running_script)
        super().logic()

    def script(self):
        for i, level in enumerate(LEVELS):
            # Draw level name
            yield from self.add(Title(f"Level {i + 1}")).wait_until_dead()

            # Run the level
            yield from level(self).script()

            # Write cleared
            yield from self.add(
                Title("Level cleared", GREEN, animation="blink")
            ).wait_until_dead()

    def draw(self, gfx: "GFX"):
        super().draw(gfx)
        self.draw_info(gfx)

    def draw_info(self, gfx: GFX):
        bg = image("inforect")
        gfx.surf.blit(bg, INFO_RECT)

        # The score
        score = auto_crop(font(20).render(str(self.player.score), False, YELLOW))
        gfx.blit(score, bottomright=INFO_RECT.topleft + Vector2(197, 34))

        self.skill_tree.draw(gfx)
