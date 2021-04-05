from random import shuffle, uniform

from constants import *
from engine import GFX, ParticleFountain, SquareParticle
from engine.pygame_input import Axis, Button
from engine.state_machine import State
from engine.utils import mix, random_in_rect
from level import LEVELS
from objects import Planet, Player, Title


class GameState(State):
    BG_COLORS = [pygame.Color(c) for c in ["#203040", "#481e66", "#008782", "#3f1f3c"]]

    def __init__(self):
        super().__init__()

        self.generate_planets(6 * (1 - DEBUG))

        self.player = self.add(Player((100, 200)))

        self.inputs["horizontal"] = Axis(
            [pygame.K_a, pygame.K_LEFT], [pygame.K_d, pygame.K_RIGHT]
        )
        self.inputs["horizontal"].always_call(self.player.move_horizontally)

        self.inputs["vertical"] = Axis(
            [pygame.K_w, pygame.K_UP], [pygame.K_s, pygame.K_DOWN]
        )
        self.inputs["vertical"].always_call(self.player.move_vertically)

        self.inputs["fire"] = Button(pygame.K_SPACE)
        self.inputs["fire"].on_press_repeated(lambda _: self.player.fire(self), 0.1)

        self.paused = False
        self.inputs["pause"] = Button(pygame.K_p)
        self.inputs["pause"].on_press(self.toggle_pause)

        self.particles.fountains.append(
            ParticleFountain(
                lambda: SquareParticle("white")
                .builder()
                .at(random_in_rect(WORLD, (0, 1), (-1 / 3, 1)), 90)
                .velocity(0.2)
                .living(6 * 60)
                .sized(uniform(1, 3))
                .anim_blink()
                .build(),
                0.2,
            )
        )

        self.running_script = self.script()

    def generate_planets(self, nb):
        positions = []
        possibilities = list(range(Planet.TOTAL_PLANETS))
        shuffle(possibilities)

        for number in possibilities[:nb]:
            planet = Planet.random_planet(number, positions)
            if planet:
                self.add(planet)
                positions.append(planet.pos)

    def toggle_pause(self, *args):
        self.paused = not self.paused
        self.debug.paused = self.paused

    def logic(self):
        if not self.paused:
            transition = 20 * 60
            first = self.timer // transition % len(self.BG_COLORS)
            second = (first + 1) % len(self.BG_COLORS)
            t = (self.timer % transition) / transition
            bg = mix(self.BG_COLORS[first], self.BG_COLORS[second], t)

            self.BG_COLOR = bg

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
        gfx.surf.set_clip(WORLD)
        super().draw(gfx)

        with gfx.focus(INFO_RECT):
            self.draw_info(gfx)

    def draw_info(self, gfx: GFX):
        gfx.fill(self.BG_COLOR)
        gfx.rect(0, 0, *INFO_RECT.size, YELLOW, 1)
