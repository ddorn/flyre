from math import exp
from random import gauss, random, uniform

from constants import *
from engine import ImageParticle, LineParticle, SquareParticle
from engine.assets import Animation, font, play, tilemap
from engine.object import Object, SpriteObject
from engine.utils import auto_crop, bounce, from_polar, vec2int

__all__ = ["Bullet", "Laser", "DebuffBullet"]


from objects.skilltree import Debuff


class BaseBullet:
    Z = 1

    def __init__(self, owner, damage=100, speed=5, angle=0.0, crit=False):
        self.owner = owner
        self.damage = damage
        self.speed = speed
        self.crit = crit
        self.angle = angle

    def logic(self, state):
        if self.owner is state.player:
            from .enemies import Enemy

            for enemy in state.get_all(Enemy):
                if self.handle_collision(enemy, state):
                    break
        else:
            self.handle_collision(state.player, state)

    def handle_collision(self, other, state) -> bool:
        return False


class Bullet(SpriteObject, BaseBullet):
    SPEED = 5
    SIZE = (1, 1)
    INITIAL_ROTATION = 90

    def __init__(self, pos, direction, owner, damage=100, speed=5, crit=False):
        play("shoot")

        img = auto_crop(tilemap("sprites", 0, 0, 16))

        vel = pygame.Vector2(direction)
        vel.scale_to_length(speed)
        w, h = img.get_size()

        # noinspection PyTypeChecker
        angle = -vel.angle_to((1, 0))
        pos += from_polar(h, angle) + from_polar(w / 2, angle - 90) - vel

        BaseBullet.__init__(self, owner, damage, speed, angle, crit)
        SpriteObject.__init__(self, pos, img, (0, 0), img.get_size(), vel, 90 - angle)

    def logic(self, state):
        SpriteObject.logic(self, state)
        BaseBullet.logic(self, state)

        screen = WORLD.inflate(32, 32)
        if not screen.collidepoint(*self.pos):
            self.alive = False

    def handle_collision(self, other, state):
        if other.rect.collidepoint(self.pos):
            other.hit(self)
            self.alive = False
            for _ in range(36 if self.crit else 12):
                state.particles.add(
                    LineParticle(gauss(8, 2), YELLOW)
                    .builder()
                    .at(self.pos, gauss(self.angle + 180, 20))
                    .velocity(gauss(5, 1))
                    .sized(uniform(1, 3))
                    .living(10)
                    .anim_fade()
                    .build()
                )
            if self.crit:
                crit_text = font(42).render("CRIT!", False, RED)

                def expand(particle):
                    particle.size = 20 * bounce(particle.life_prop)
                    particle.need_redraw = True

                state.particles.add(
                    ImageParticle(crit_text)
                    .builder()
                    .at(self.pos, 0)
                    .velocity(0)
                    .sized(4)
                    .anim(expand)
                    .anim_fade(0.75)
                    .living(2 * 60)
                    .build()
                )

            return True
        return False


class DebuffBullet(Bullet):
    def __init__(
        self, debuff: Debuff, pos, direction, owner, damage=100, speed=5, crit=False
    ):
        super().__init__(pos, direction, owner, damage, speed, crit)
        self.debuff = debuff

    def handle_collision(self, other, state):
        if super().handle_collision(other, state):
            other.debuffs.add(self.debuff)
            return True
        return False


class Laser(Object, BaseBullet):
    def __init__(
        self,
        owner,
        target,
        follow_player_duration=60,
        preshoot_duration=40,
        laser_duration=20,
        damage=100,
    ):
        Object.__init__(self, owner.sprite_to_screen(owner.GUN))
        BaseBullet.__init__(self, owner, damage, angle=owner.angle)
        self.target = target

        self.timer = 0
        self.follow_player_end = follow_player_duration
        self.preshoot_end = preshoot_duration + self.follow_player_end
        self.laser_duration = laser_duration + self.preshoot_end

    def logic(self, state):
        Object.logic(self, state)

        self.timer += 1

        # Keep in sync with the shooter
        if not self.owner.alive:
            self.alive = False
        self.pos = self.owner.sprite_to_screen(self.owner.GUN)
        if self.timer < self.follow_player_end:
            self.angle = self.owner.angle
        else:
            self.owner.angle = self.angle

        # Shooting
        if self.timer == self.preshoot_end:
            play("laser")
        if self.timer > self.preshoot_end:
            state.particles.add(
                LineParticle(20)
                .builder()
                .at(self.pos, self.angle)
                .velocity(30)
                .living(40)
                .hsv(uniform(0, 360), 0.8, 1)
                .build()
            )

            BaseBullet.logic(self, state)

        # End
        if self.timer > self.laser_duration:
            self.alive = False

    def handle_collision(self, other, state):
        start = self.pos
        end = self.pos + from_polar(1000, self.angle)

        if p := other.rect.clipline((start, end)):
            other.hit(self)
            start, end = p
            for _ in range(6):
                pos = start + random() * (pygame.Vector2(end) - start)
                state.particles.add_fire_particle(pos, self.angle)
            return True
        return False

    def draw(self, gfx):
        if self.timer < self.preshoot_end:
            d = from_polar(3, self.angle)
            for i in range(200):
                p = vec2int(self.pos + d * i)
                gfx.surf.set_at(p, RED)


class Bomb(Object, BaseBullet):
    SIZE = (9, 9)

    def __init__(self, center, owner, damage=200, timer=3 * 60):

        Object.__init__(self, center, self.SIZE)
        self.center = center

        BaseBullet.__init__(self, owner, damage, 0)
        self.animation = Animation(f"bomb")
        self.timer = timer

    def logic(self, state):
        from .spaceship import SpaceShip

        super().logic(state)
        self.animation.logic()

        self.timer -= 1

        if self.timer == 0:
            self.animation = Animation("explosion")
            for ship in state.get_all(SpaceShip):
                if ship.center.distance_to(self.center) < 20 + ship.size.length() / 2:
                    ship.hit(self)

        if self.timer == -len(self.animation):
            self.alive = False

    def draw(self, gfx):
        frame = self.animation.image()
        gfx.blit(frame, center=self.center)
