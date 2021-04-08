from random import gauss, random

from pygame import Vector2

from src.engine import *
from .bullets import Bomb, Bullet, Laser
from .spaceship import SpaceShip

__all__ = ["Enemy", "LaserEnemy", "ChargeEnemy", "CopyEnemy", "BomberEnemy"]


class Enemy(SpaceShip):
    SCALE = 2
    INVICIBILITY_DURATION = 5

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
            yield

        yield from self.charge_to_player()

        self.alive = False


class CopyEnemy(Enemy):
    SCALE = 2
    MAX_THRUST = 0.5

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

    def fire(self, state, direction=None):
        state.add(Bomb(self.center, self, state.player.center, self.bullet_damage))

    def script(self):
        while True:
            yield from self.go_straight_to()
            yield from self.slow_down_and_stop()
            self.fire(self.state)
