from itertools import chain
from random import choice, gauss, random

from pygame import Vector2

from src.engine import *
from .bullets import Bomb, Bullet, Laser
from .spaceship import SpaceShip

__all__ = ["Enemy", "LaserEnemy", "ChargeEnemy", "CopyEnemy", "BomberEnemy", "Boss"]


class Enemy(SpaceShip):
    SCALE = 2
    INVICIBILITY_DURATION = 5
    SCORE = 100

    OFFSET = (-8, -9)
    SIZE = Vector2(17, 17) * SCALE

    def __init__(self, pos, kind=0):
        image = tilemap("spaceships", kind, 1, 32)
        super().__init__(pos, image, self.OFFSET, self.SIZE, rotation=180)
        # self.behavior = StationaryMultipleShooter(self)

    def logic(self, state):
        clamp_length(self.vel, self.max_speed)
        super().logic(state)

        angle_towards_player = -90 + (
            state.player.center - self.sprite_to_screen(self.GUN)
        ).angle_to((1, 0))
        self.rotation = angle_towards(self.rotation, angle_towards_player, 2)

    def script(self):
        while True:
            yield from self.go_to()

            state = App.current_state()
            for _ in range(3):
                self.fire(state, state.player.pos - self.pos)
                yield from range(8)

    def fire(self, state, direction):
        return state.add(Bullet(self.sprite_to_screen(self.GUN), direction, self))

    def hit(self, bullet):
        super().hit(bullet)

        player = App.current_state().player
        if self.life <= 0 and bullet.owner is player:
            player.did_kill(self)


class LaserEnemy(Enemy):
    GUN = (15.5, 7)
    SIZE = Vector2(22, 16) * Enemy.SCALE
    OFFSET = (-6, -11)
    KNOCK_BACK = 1.5

    def __init__(self, pos):
        super().__init__(pos, 2)

    def fire(self, state, target):
        return state.add(Laser(self, target))

    def script(self):
        state = App.current_state()

        while True:
            yield from self.go_straight_to()
            yield from self.hover_around(gauss(2 * 60, 20))
            yield from self.slow_down_and_stop()

            bullet = self.fire(state, self.state.player)
            while bullet.alive:
                yield from self.slow_down_and_stop()
                # slow_down_and_stop is an empty generator,
                # if we are already stopped. It would result in an empty loop
                yield


class ChargeEnemy(Enemy):
    SIZE = Vector2(22, 18) * Enemy.SCALE
    OFFSET = (-6, -8)
    GUN = (16.5, 13)
    CONTACT_DAMAGE = 400
    SCORE = 150

    INITIAL_LIFE = 750

    def __init__(self, pos):
        super().__init__(pos, 1)

    def script(self):
        yield from self.go_to()

        hover_duration = gauss(0 * 60, 30)
        yield from self.hover_around(hover_duration)
        yield from self.slow_down_and_stop()

        # Preparation
        prep_len = 60
        for t in range(prep_len):
            self.state.particles.add(self.get_charge_particle(t / prep_len))
            yield from self.slow_down_and_stop(1)

        yield from self.charge_to_player()

        self.alive = False


class CopyEnemy(Enemy):
    SCALE = 2
    MAX_THRUST = 0.5
    SCORE = 200

    SIZE = Vector2(17, 13) * SCALE
    OFFSET = Vector2(-7, -11)
    JET1 = Vector2(14, 22)
    JET2 = Vector2(16, 22)

    def __init__(self, pos, player):
        self.INITIAL_LIFE = player.max_life
        super().__init__(pos, 3)

        self.player = player

    def fire(self, state, angle):
        from src.objects import Player

        for pos in Player.get_guns_positions(self.player):
            crit = random() < self.player.crit_chance
            state.add(
                Bullet(
                    self.sprite_to_screen(pos) + (1, 0),
                    from_polar(1, self.angle),
                    self,
                    self.player.bullet_damage
                    * (1 if not crit else self.player.crit_mult),
                    self.player.bullet_speed,
                    crit,
                )
            )

    def logic(self, state):
        for jet in (self.JET1, self.JET2):
            state.debug.point(*self.sprite_to_screen(jet))
            state.particles.add(
                SquareParticle(YELLOW)
                .builder()
                .at(self.sprite_to_screen(jet), gauss(self.angle + 180, 10))
                .sized(4)
                .living(5)
                .constant_force(self.vel / 2)
                .velocity(gauss(4, 0.6),)
                .anim_fade()
                .build()
            )

        super().logic(state)

    def script(self):
        yield from self.go_straight_to()
        while True:
            yield from self.hover_around(1000)


class BomberEnemy(Enemy):
    SIZE = Vector2(22, 22) * Enemy.SCALE
    OFFSET = (-5, -5)

    INITIAL_LIFE = 2000
    INITIAL_BULLET_DAMAGE = 250

    def __init__(self, pos):
        super().__init__(pos, 4)

        self.last_fire = 0

    def logic(self, state):
        super().logic(state)
        self.last_fire += 1

    def fire(self, state, direction=None):
        state.add(Bomb(self.center, self, state.player.center, self.bullet_damage))
        self.last_fire = 0

    def script(self):
        while True:
            yield from self.go_straight_to()
            yield from self.slow_down_and_stop()

            if self.last_fire > 30:
                self.fire(self.state)


class Boss(Enemy):
    MAX_THRUST = Enemy.MAX_THRUST * 2
    INITIAL_LIFE = 20_000
    OFFSET = (-2, 0)
    SIZE = Vector2(27, 31) * Enemy.SCALE
    GUN = (16, 4)
    SIDE_GUNS = ((5, 2), (26, 2))
    KNOCK_BACK = 0.1

    SCORE = 2000

    def __init__(self, pos, home_pos=WORLD.center):
        super().__init__(pos, 5)

        from . import HealthBar

        self.health_bar = HealthBar((0, 0, 30, 2), (255, 0, 0, 200), self)
        self.home_pos = home_pos

    def logic(self, state):
        super().logic(state)
        self.health_bar.center = (
            self.center.x,
            self.center.y - self.image.get_height() / 2 - 5,
        )
        self.health_bar.logic(state)

    def draw(self, gfx):
        super().draw(gfx)
        self.health_bar.draw(gfx)

    def fire(self, *args):
        choice([self.fire_bullets, self.fire_laser()])()

    def _fire(self, pos, angle, kind):
        self.state.add(
            Bullet(pos, from_polar(1, angle), self, self.bullet_damage, kind=kind,)
        )

    def random_fire(self):
        kind = randrange(0, 2)
        if kind == 0:
            for _ in range(3):
                self.fire_bullets()
                yield from self.hover_around(6)
        elif kind == 1:
            lasers = list(self.fire_laser())
            while any(l.alive for l in lasers):
                yield from self.slow_down_and_stop()
                yield
        else:
            yield from self.go_straight_to(prop_in_rect(WORLD, 0.5, 0.2), 10)
            for i in range(100):
                angle = i * 14
                self._fire(self.center, angle, 1 + i % 2)
                yield from self.run_and_wait(
                    chain(
                        self.go_straight_to(prop_in_rect(WORLD, 0.5, 0.2), 10),
                        self.slow_down_and_stop(),
                    ),
                    3,
                    exact=True,
                )

    def fire_bullets(self):
        for gun, delta_angle in zip(self.SIDE_GUNS, (7, -7)):
            self.state.add(
                Bullet(
                    self.sprite_to_screen(gun),
                    from_polar(1, self.angle + delta_angle),
                    self,
                )
            )

    def fire_laser(self):
        nb_lasers = choice([3, 5])
        for i in range(nb_lasers):
            offset = (i - nb_lasers // 2) * 30
            yield self.state.add(
                Laser(self, self.state.player, 40, 30, 30, offset_angle=offset)
            )

    def fire_spiral(self):
        lines = 5
        for angle in range(0, 360, 5):
            for line in range(lines):
                self.state.add(
                    Bullet(
                        self.center,
                        from_polar(1, angle + line * 360 / lines),
                        self,
                        kind=1 + (angle + line) % 2,
                    )
                )

                yield

    def script(self):
        yield from self.go_straight_to(self.home_pos)

        phase = 1
        while True:
            prop = self.life / self.max_life
            yield from self.go_straight_to()
            yield from self.hover_around(30 * (1 - prop))
            yield from self.random_fire()

            if prop < 1 - phase / 3:
                phase += 1

                for i in range(20):
                    self.state.particles.add(
                        SquareParticle(ORANGE)
                        .builder()
                        .at(self.center, uniform(0, 360))
                        .velocity(gauss(10, 1), 2)
                        .living(15)
                        .sized(5)
                        .anim_fade()
                        .anim_shrink()
                        .build()
                    )

                yield from self.go_straight_to(self.home_pos, 10)
                yield from self.slow_down_and_stop()
                yield from self.fire_spiral()
                yield from range(60)

            if len(list(self.state.get_all(Enemy))) < phase + 1:
                en = choice([Enemy, LaserEnemy, BomberEnemy, ChargeEnemy,])
                self.state.add(en((uniform(WORLD.left, WORLD.right), WORLD.top - 40)))
