from pygame import Vector2

from src.engine import *
from pygame import Vector2

from src.level import LEVELS
from src.objects import *
from .my_state import MyState
from .skillpickup import SkillPickUp


class GameState(MyState):
    def __init__(self):
        super().__init__()

        self.player = self.add(Player((100, 200)))
        self.add(
            HealthBar((INFO_RECT.topleft + Vector2(9, 347), (180, 5)), RED, self.player)
        )

    def create_inputs(self):
        inputs = super().create_inputs()
        inputs["horizontal"] = Axis(
            [pygame.K_a, pygame.K_LEFT],
            [pygame.K_d, pygame.K_RIGHT],
            JoyAxis(JOY_HORIZ_LEFT),
        )
        inputs["horizontal"].always_call(self.player.move_horizontally)

        inputs["vertical"] = Axis(
            [pygame.K_w, pygame.K_UP],
            [pygame.K_s, pygame.K_DOWN],
            JoyAxis(JOY_VERT_LEFT),
        )
        inputs["vertical"].always_call(self.player.move_vertically)

        inputs["fire"] = Button(
            pygame.K_SPACE, JoyAxisTrigger(JOY_RT), JoyAxisTrigger(JOY_RL)
        )
        inputs["fire"].on_press_repeated(lambda _: self.player.fire(self), 0.1)

        inputs["pause"] = Button(pygame.K_p, JoyButton(JOY_Y))
        inputs["pause"].on_press(self.set_pause)

        def cheat(_):
            self.lvl.skip = True
            for en in self.get_all(Enemy):
                en.alive = False

        inputs["cheat"] = Button(pygame.K_c)
        inputs["cheat"].on_press(cheat)

        return inputs

    def set_pause(self, *args):
        from . import PauseState

        self.push_state(PauseState(self))

    def on_resume(self):
        super().on_resume()
        self.debug.paused = False

    def on_exit(self):
        self.debug.paused = True

    def logic(self):
        super().logic()

        if not self.player.alive:
            from . import GameOverState

            self.replace_state(GameOverState(self.player))

    def script(self):
        for i, level in enumerate(LEVELS):
            # Draw level name
            self.add(Title(f"Level {i + 1}", duration=2 * 60))

            # Run the level
            self.lvl = level(self)
            yield from self.lvl.script()
            yield from self.lvl.wait_until_dead()

            # Write cleared
            yield from self.add(
                Title("Level cleared", GREEN, animation="blink")
            ).wait_until_dead()

            self.push_state(SkillPickUp(self.player))

        from . import GameOverState

        self.replace_state(GameOverState(self.player))

    def draw(self, gfx: "GFX"):
        super().draw(gfx)
        self.draw_info(gfx)

    def draw_info(self, gfx: GFX):
        bg = image("inforect")
        gfx.surf.blit(bg, INFO_RECT)

        # The score
        score = auto_crop(font(20).render(str(self.player.score), False, YELLOW))
        gfx.blit(score, bottomright=INFO_RECT.topleft + Vector2(197, 34))

        self.player.skill_tree.layout((INFO_RECT.centerx + 1, 209))
        self.player.skill_tree.draw(gfx)

        HP = (24 + INFO_RECT.x, 81 + INFO_RECT.y)
        CRIT = HP[0], HP[1] + 26
        REGEN = HP[0], CRIT[1] + 48
        ATK = HP[0] + 161, HP[1] + 5
        BURN = ATK[0], ATK[1] + 69

        def get(txt, color):
            if isinstance(txt, (float)):
                txt = int(txt)
            return text(str(txt), 7, WHITE, name="pixelmillennium")

        # HP
        s = get(self.player.life, GREEN)
        gfx.blit(s, topleft=HP)

        # CRIT
        s = get(f"{int(self.player.crit_chance * 100)}%", RED)
        gfx.blit(s, topleft=CRIT)

        # REGEN
        regen = 0
        for debuff in self.player.debuffs:
            if isinstance(debuff, RegenDebuff):
                regen = debuff.strength * self.player.max_life
        s = get(regen, GREEN)
        gfx.blit(s, topleft=REGEN)

        # ATK
        s = get(self.player.bullet_damage, RED)
        gfx.blit(s, topright=ATK)

        # BURN
        s = get(f"{int(100 * self.player.fire_chance)}%", ORANGE)
        gfx.blit(s, topright=BURN)
