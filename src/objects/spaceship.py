from random import gauss, random, uniform

from src.engine import *

__all__ = ["SpaceShip"]


from .bullets import Bomb


class Cooldown:
    def __init__(self, delay):
        self.delay = delay
        self.timer = 0

    def tick(self, fire_probability):
        self.timer += 1

        if self.timer > self.delay and random() < fire_probability:
            self.timer = 0
            return True
        return False


class SpaceShip(Entity):
    GUN = (16, 18)
    MAX_THRUST = 0.2
    KNOCK_BACK = 2
    CONTACT_DAMAGE = 100
    INITIAL_BULLET_DAMAGE = 100

    def __init__(
        self,
        pos,
        image: pygame.Surface,
        offset=(0, 0),
        size=(1, 1),
        vel=(0, 0),
        rotation=0,
    ):
        super().__init__(pos, image, offset, size, vel, rotation)

        self.max_speed = 3
        self.bullet_speed = 10
        self.bullet_damage = self.INITIAL_BULLET_DAMAGE
        self.crit_chance = 0.01
        self.crit_mult = 3
        self.fire_chance = 0.02
        self.fire_dmg = 0.1
        self.fire_duration = 2 * 60
        self.nb_bullets = 1

        # TODO: Not implemented !
        self.shield = False

        self.debuffs = set()

        self.overlapping_ships = {}

    def force_to_move_towards(self, goal):
        direction = goal - self.pos
        direction.scale_to_length(self.max_speed)

        perp = part_perp_to(direction, self.vel)
        return perp

    def force_slow_down_around(self, point, radius=60):
        slow_force = pygame.Vector2()
        dist = self.pos.distance_to(point)
        if dist < radius:
            slow_force = -self.vel * chrange(
                radius - dist, (0, radius), (0, self.MAX_THRUST * 2), 2
            )

        return slow_force

    def force_to_accelerate(self):
        if self.vel.length() < self.max_speed:
            return self.vel * self.MAX_THRUST
        return pygame.Vector2()

    def force_to_slow_down(self, target=0.0):
        if self.vel.length() < target:
            return pygame.Vector2()
        return -self.vel.normalize() * self.MAX_THRUST

    def force_to_avoid_walls(self, radius):
        p = self.pos

        wall = [
            p.x - WORLD.left,
            p.y - WORLD.top,
            WORLD.right - self.size.x - p.x,
            WORLD.bottom - self.size.y - p.y,
        ]
        normals = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        force = pygame.Vector2()
        for dist, normal in zip(wall, normals):
            normal = pygame.Vector2(normal)
            if dist < radius:
                normal.scale_to_length(2 * radius / max(1, dist) * self.MAX_THRUST)
                force += normal

        return force

    def force_to_avoid(self, pos, radius):
        p = self.center
        distance = pos - p
        dist = distance.length()

        if dist > radius or dist == 0:
            return pygame.Vector2()

        norm = chrange(
            max(0, dist - radius / 2),
            (0, radius / 2),
            (0, self.MAX_THRUST * 2),
            flipped=True,
        )

        distance.scale_to_length(norm)
        return -distance

    def force_to_avoid_all_ships(self, avoid_player=True):
        from src.objects import Enemy

        thrust = pygame.Vector2()
        for ship in self.state.get_all(SpaceShip if avoid_player else Enemy, Bomb):
            if ship is self:
                continue
            r = ship.size.length() + self.size.length()
            thrust += self.force_to_avoid(ship.center, r)
        return thrust

    def force_to_stay_close(self, pos, radius):
        p = self.pos
        distance = pos - p
        dist = distance.length()

        if dist < radius:
            return pygame.Vector2()

        dist = min(dist, 2 * radius)

        norm = chrange(dist, (radius, 2 * radius), (0, self.MAX_THRUST * 2))
        distance.scale_to_length(norm)
        return distance

    def force_to_stay_up(self, up=0):
        dist = self.pos.y - up

        dist = max(0, dist)
        return (
            pygame.Vector2(0, -1)
            * self.MAX_THRUST
            * chrange(dist, (0, WORLD.height - up), (0, 1))
        )

    def random_but_high(self, avoid=(), margin=40) -> pygame.Vector2:

        rect = WORLD.inflate(-2 * margin, -2 * margin)
        rect.height = WORLD.height / 2 - 2 * margin
        return random_in_rect_and_avoid(
            rect, avoid, 2 * self.size.length(), default=random_in_rect(rect)
        )

    def go_to(self, goal=None, precision=30):

        if goal is None:
            goal = self.random_but_high(
                [e.center for e in self.state.get_all(SpaceShip)], 100
            )

        while self.center.distance_to(goal) > precision:

            thrust = self.force_to_avoid_all_ships()
            if thrust.length() == 0:
                self.state.debug.point(*self.center, "red")
                thrust += self.force_to_move_towards(goal)
                thrust += self.force_to_accelerate() * 0.1
                thrust += self.force_slow_down_around(goal, 60)
                thrust += self.force_to_avoid_walls(30)
            else:
                self.state.debug.point(*self.center, "green")

            clamp_length(thrust, self.MAX_THRUST)

            self.vel += thrust

            yield

    def go_straight_to(self, goal=None, precision=40, max_duration=3 * 60):
        if goal is None:
            goal = self.random_but_high(
                [e.center for e in self.state.get_all(SpaceShip)], 100
            )

        timer = 0
        while self.center.distance_to(goal) > precision and timer < max_duration:
            timer += 1

            thrust = self.force_to_avoid_all_ships(False)
            if thrust.length() == 0:
                self.state.debug.point(*self.center, "red")
                thrust += (goal - self.center).normalize() * self.MAX_THRUST
            else:
                self.state.debug.point(*self.center, "green")

            clamp_length(thrust, self.MAX_THRUST)

            self.vel += thrust

            yield

    def run_and_wait(self, generator, waiting, exact=False):
        frames = 0
        for _ in generator:
            frames += 1
            yield
            if exact and frames == waiting:
                return

        for _ in range(frames, waiting):
            yield

    def hover_around(self, duration):
        from . import Enemy

        state = App.current_state()
        player = state.player

        for _ in range(int(duration)):

            thrust = self.force_to_avoid_all_ships()
            if thrust.length() == 0:
                # dont go too close to the player
                thrust += self.force_to_avoid(player.pos, 100) * 0.3
                # don't go too far either
                thrust += self.force_to_stay_close(player.pos, 300)
                thrust += self.force_to_slow_down(self.max_speed / 5) * 0.1
                thrust += self.force_to_stay_up(WORLD.height / 4)

                thrust += self.force_to_avoid_walls(30)

                # Avoid other enemies
                for enemy in state.get_all(Enemy):
                    if enemy is not self:
                        thrust += self.force_to_avoid(enemy.pos, 50)

            self.vel += clamp_length(thrust, self.MAX_THRUST)
            yield

    def slow_down_and_stop(self, frames=1):
        # Stopped
        while self.vel.length() != 0 or frames > 0:
            if self.vel.length():
                self.vel -= self.vel.normalize() * min(
                    self.MAX_THRUST, self.vel.length()
                )
            frames -= 1
            yield

    def charge_to_player(self):
        direction = self.state.player.pos - self.pos
        direction.scale_to_length(self.MAX_THRUST * 3)
        self.max_speed *= 4
        rotation = self.rotation
        while WORLD.inflate(100, 100).colliderect(self.rect):
            self.vel += direction
            self.rotation = rotation
            self.state.particles.add(self.get_charge_particle(1))
            yield

    def get_charge_particle(self, t):
        direction = self.state.player.pos - self.pos
        angle = -direction.angle_to((1, 0))
        angle = gauss(angle, 10) + 180

        return (
            LineParticle(chrange(t, (0, 1), (2, 15)), YELLOW)
            .builder()
            .at(self.center + from_polar(self.size.length() / 2, angle), angle,)
            .living(10)
            .velocity(chrange(t, (0, 1), (0.5, 3)))
            .anim_fade()
            .build()
        )

    def logic(self, state: State):
        super().logic(state)

        new_overlapping = {}
        for ship in state.get_all(SpaceShip):
            if ship is self:
                continue

            radius_sum = self.size.length() / 2 + ship.size.length() / 2
            if self.center.distance_to(ship.center) < radius_sum:
                new_overlapping[ship] = self.overlapping_ships.get(ship, -1) + 1

        self.overlapping_ships = new_overlapping
        for ship, duration in self.overlapping_ships.items():
            if duration % 20 == 0:
                play("hit")
                self.damage(ship.CONTACT_DAMAGE, ignore_invincibility=True)

        to_remove = set()
        for debuff in self.debuffs:
            debuff.apply(self)
            if debuff.done:
                to_remove.add(debuff)
        self.debuffs.difference_update(to_remove)

    def on_death(self, state):
        play("explosion")
        for _ in range(200):
            state.particles.add(
                SquareParticle()
                .builder()
                .at(self.center, uniform(0, 360))
                .velocity(v := gauss(6, 1), 0)
                # .hsv(h := gauss(20, 8), 0)
                .living(int(v / 0.4))
                .acceleration(-0.4)
                .sized(gauss(3, 1))
                .anim_gradient_to(h := gauss(10, 8), 1, 1, h, 1, 0.8)
                .anim_fade(0.5)
                .build()
            )

    def hit(self, bullet):
        if not self.invincible:
            self.state.debug.text("Hit: ", bullet, bullet.damage, self)
            self.damage(bullet.damage)
            self.vel += from_polar(self.KNOCK_BACK, bullet.angle)
            if bullet.crit:
                play("critical")
            else:
                play("hit")


class HorizontalBehavior(SpaceShip):
    def script(self):

        fire_cooldown = Cooldown(20)
        start = True
        enemy = self
        direction = 1  # or -1
        while True:
            if (
                start
                or self.pos.x + enemy.vel.x < WORLD.left
                or self.pos.x + enemy.vel.x + enemy.size.x > WORLD.right
            ):
                start = False
                direction *= -1
                enemy.vel.x = gauss(2, 0.3) * direction

            if abs(enemy.pos.x - self.state.player.pos.x) < 20:
                if fire_cooldown.tick(0.1):
                    enemy.fire(self.state)
            else:
                fire_cooldown.tick(0)

            yield
