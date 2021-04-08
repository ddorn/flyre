from glob import glob
from math import ceil
from random import choice, randint

from pygame import Vector2
from pygame.locals import *

from src.engine import *

__all__ = ["Planet", "Debug", "Title", "HealthBar", "Text", "Debug", "Menu"]


class Planet(Object):
    Z = -1
    TOTAL_PLANETS = len(glob(str(ANIMATIONS) + "/planet*.json"))

    def __init__(self, number, center, speed, wrap_rect):
        self.number = number
        self.animation = Animation(f"planet{number}", speed)
        self.wrap_rect = wrap_rect

        s = self.animation.tile_size
        super().__init__(center - Vector2(s, s) / 2, (s, s), vel=(0, 0.5))

    @classmethod
    def random_planet(cls, number, avoid_positions, wrap_rect, y=None, max_trials=1000):
        rect = pygame.Rect(wrap_rect)
        rect.top -= rect.height / 2
        rect.height *= 1.5

        pos = random_in_rect_and_avoid(
            rect, avoid_positions, 200, max_trials=max_trials, force_y=y
        )

        if pos is None:
            return

        speed = randint(2, 5)
        return Planet(number, pos, speed, wrap_rect)

    def logic(self, state):
        super().logic(state)
        self.animation.logic()

        if self.pos.y > self.wrap_rect.bottom + self.size.y:

            numbers_taken = [planet.number for planet in state.get_all(Planet)]
            number = choice(
                [i for i in range(self.TOTAL_PLANETS) if i not in numbers_taken]
            )
            positions = [planet.pos for planet in state.get_all(Planet)]
            # planet can be none if it can't place it, so I keep the old planet alive until I can place it.
            planet = Planet.random_planet(
                number, positions, self.wrap_rect, self.wrap_rect.top - 200
            )

            if planet is not None:
                self.alive = False
                state.add(planet)

    def draw(self, gfx):
        frame = self.animation.image()
        gfx.blit(frame, topleft=self.pos)


class Debug(Object):
    Z = 1000000000

    def __init__(self):
        super().__init__((0, 0))
        self.points = []
        self.vectors = []
        self.rects = []
        self.texts = []
        self.nb_txt_this_frame = 0

        self.lasts = [[], [], [], []]

        self.enabled = DEBUG
        self.paused = False

    def toggle(self, *args):
        self.enabled = not self.enabled

    def point(self, x, y, color="red"):
        if self.enabled:
            self.points.append((x, y, color))
        return x, y

    def vector(self, vec, anchor, color="red", scale=1):
        if self.enabled:
            self.vectors.append((Vector2(anchor), Vector2(vec) * scale, color))
        return vec

    def rectangle(self, rect, color="red"):
        if self.enabled:
            self.rects.append((rect, color))
        return rect

    def text(self, *obj):
        if self.enabled:
            self.texts.append(obj)
            self.nb_txt_this_frame += 1

    def draw(self, gfx):
        if self.paused:
            self.points, self.vectors, self.rects, self.texts = self.lasts

        for (x, y, color) in self.points:
            pygame.draw.circle(gfx.surf, color, (x, y), 1)

        for (anchor, vec, color) in self.vectors:
            pygame.draw.line(gfx.surf, color, anchor, anchor + vec)

        for rect, color in self.rects:
            pygame.draw.rect(gfx.surf, color, rect, 1)

        y = 3
        for i, obj in enumerate(self.texts):
            color = (
                WHITE if len(self.texts) - i - 1 >= self.nb_txt_this_frame else YELLOW
            )
            s = text(" ".join(map(str, obj)), 7, color, "pixelmillennium")
            r = gfx.blit(s, topleft=(3, y))
            y = r.bottom

        self.lasts = [self.points, self.vectors, self.rects, self.texts]
        self.points = []
        self.vectors = []
        self.rects = []
        self.texts = self.texts[-5:]
        if not self.paused:
            self.nb_txt_this_frame = 0


class Title(Object):
    Z = 10

    def __init__(self, text, color=YELLOW, duration=4 * 60, animation="enlarge"):
        self.duration = duration
        self.color = color
        self.bg_rect = pygame.Rect(0, 0, 0, 3)

        surf = font(42).render(text, True, color)
        rect = surf.get_rect(center=WORLD.center)

        self.text_surf = surf
        self.shown_image = pygame.Surface((0, 0))
        super().__init__(rect.topleft, surf.get_size())
        self.scripts = {getattr(self, animation)()}

    def enlarge(self):
        widen_frames = 40
        for i in range(widen_frames):
            self.bg_rect.width = (WORLD.width + 2) * chrange(
                i, (0, widen_frames - 1), (0, 1)
            )
            self.bg_rect.center = self.center
            yield

        larger_frames = 20
        for i in range(larger_frames):
            self.bg_rect.height = (self.size.y + 10) * chrange(
                i, (0, larger_frames - 1), (0, 1)
            )
            self.bg_rect.center = self.center
            yield

        text_appear_frames = 40
        for i in range(text_appear_frames):
            r = self.text_surf.get_rect()
            r.inflate_ip(
                -r.w * chrange(i, (0, text_appear_frames), (0, 1), flipped=True), 0
            )
            self.shown_image = self.text_surf.subsurface(r)
            yield

        for i in range(self.duration):
            if i % 60 < 45:
                self.shown_image = self.text_surf
            else:
                self.shown_image = pygame.Surface((0, 0))
            yield

        for i in range(larger_frames):
            self.bg_rect.height = (self.size.y + 10) * chrange(
                i, (0, larger_frames - 1), (0, 1), flipped=True
            )
            self.bg_rect.center = self.center
            self.shown_image = self.text_surf.subsurface(
                self.text_surf.get_rect().inflate(
                    0, -self.size.y * chrange(i, (0, larger_frames - 1), (0, 1)),
                )
            )
            yield

        for i in range(widen_frames):
            self.bg_rect.width = (WORLD.width + 2) * chrange(
                i, (0, widen_frames - 1), (0, 1), flipped=True
            )
            self.bg_rect.center = self.center
            yield

    def blink(self):
        for i in range(self.duration):
            if i % 60 < 45:
                self.shown_image = self.text_surf
            else:
                self.shown_image = pygame.Surface((0, 0))
            yield

    def logic(self, state):
        super().logic(state)

        if not self.scripts:
            self.alive = False

    def draw(self, gfx: "GFX"):
        super().draw(gfx)
        gfx.box(self.bg_rect, (0, 0, 0, 80))
        gfx.rect(*self.bg_rect, self.color, 1)
        gfx.blit(self.shown_image, center=self.center)


class Menu(Object):
    Z = 10

    def __init__(self, midtop, actions: dict):
        super().__init__((0, 0))

        self.draw_midtop = midtop
        self.actions = actions
        self.selected = 0

    def create_inputs(self):
        up = Button(K_UP, K_w)
        up.on_press(lambda _: self.change_selection(-1))

        down = Button(K_DOWN, K_s)
        down.on_press(lambda _: self.change_selection(+1))

        select = Button(K_SPACE, K_RETURN, K_RIGHT, K_d)
        select.on_press(self.select)

        return {up: up, down: down, select: select}

    def change_selection(self, amount):
        self.selected += amount
        self.selected %= len(self.actions)

        play("menu")

    def select(self, *args):
        key = list(self.actions)[self.selected]
        self.actions[key]()

        play("menu")

    def draw(self, gfx: GFX):
        super().draw(gfx)

        midtop = self.draw_midtop
        for i, action in enumerate(self.actions):
            if i == self.selected:
                color = YELLOW
            else:
                color = "white"

            s = text(action, 32, color)
            r = s.get_rect(midtop=midtop)
            gfx.surf.blit(s, r)
            midtop = r.midbottom


class Text(SpriteObject):
    Z = 10

    def __init__(self, txt, color, size: int, font_name=None, **anchor):

        img = text(txt, size, color, font_name)
        pos = img.get_rect(**anchor).topleft

        super().__init__(pos, img, size=img.get_size())


class HealthBar(Object):
    Z = 10

    def __init__(self, rect, color, entity):
        rect = pygame.Rect(rect)
        super().__init__(rect.topleft, rect.size)

        self.color = pygame.Color(color)
        self.entity = entity

        self.flash_size = 0
        self.flash_duration = -1
        self.last_health = entity.life

    def logic(self, state):
        self.flash_duration -= 1

        loss = self.last_health - self.entity.life
        self.flash_size += loss

        if loss > 0:
            self.flash_duration = 10

        if self.flash_duration <= 0:
            self.flash_size -= 1
            self.flash_size *= 0.98
            self.flash_size = max(0, self.flash_size - 3)

        self.last_health = self.entity.life

    def draw(self, gfx: "GFX"):

        prop = self.entity.life / self.entity.max_life
        width = ceil(self.size.x * prop)
        flash = ceil(self.size.x * self.flash_size / self.entity.max_life)
        lost = self.size.x - width - flash

        x, y = self.pos
        gfx.box((*self.pos, width, self.size.y), self.color)
        if flash > 0:
            gfx.box((x + width, y, flash, self.size.y), WHITE + (self.color.a,))

        if lost > 0:
            gfx.box(
                (x + width + flash, y, lost, self.size.y,), (0, 0, 0, self.color.a),
            )
