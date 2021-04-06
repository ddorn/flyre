from random import randint
from typing import Optional, Type, TypeVar, Union

import pygame
from pygame.locals import *

from engine.particles import ParticleSystem
from engine.pygame_input import Button, Inputs, QuitEvent

T = TypeVar("T")

__all__ = ["State", "StateMachine"]


class State:
    BG_COLOR = "black"
    BG_MUSIC = None

    def __init__(self):
        self.timer = 0
        self.add_later = []
        self.add_object_lock = False
        self.objects = set()
        self.next_state = self
        self.shake = 0

        self.particles = ParticleSystem()
        from objects import Debug

        self.debug = self.add(Debug())

        self.inputs = Inputs()

    def create_inputs(self):
        inputs = Inputs()
        inputs["quit"] = Button(QuitEvent(), K_ESCAPE, K_q)
        inputs["quit"].on_press(lambda e: setattr(self, "next_state", None))

        inputs["debug"] = Button(K_F11)
        inputs["debug"].on_press(self.debug.toggle)

        for object in self.objects:
            obj_inputs = object.create_inputs()
            if not set(inputs).isdisjoint(obj_inputs):
                raise ValueError("Conflicting key inputs.")

            inputs.update(object.create_inputs())

        return inputs

    # Life phase of state

    def on_resume(self):
        self.inputs = self.create_inputs()
        self.next_state = self
        if self.BG_MUSIC:
            pygame.mixer.music.load(self.BG_MUSIC)
            # pygame.mixer.music.set_volume(VOLUME['BG_MUSIC'] * Settings().music)
            pygame.mixer.music.play(-1)

    def on_exit(self):
        pass

    def logic(self):
        """All the logic of the state happens here.

        To change to an other state, you need to set self.next_state"""
        self.timer += 1

        # Add all object that have been queued
        self.add_object_lock = False
        for object in self.add_later:
            self.add(object)
        self.add_later = []
        self.add_object_lock = True

        # Logic for all objects
        for object in self.objects:
            object.logic(self)
        self.particles.logic()

        # Clean dead objects
        to_remove = set()
        for object in self.objects:
            if not object.alive:
                to_remove.add(object)
                object.on_death(self)
        self.objects.difference_update(to_remove)

    def draw(self, gfx: "GFX"):
        if self.BG_COLOR:
            gfx.fill(self.BG_COLOR)

        for z in sorted(set(o.Z for o in self.objects)):
            for obj in self.objects:
                if z == obj.Z:
                    obj.draw(gfx)

        self.particles.draw(gfx.surf)

        if self.shake:
            s = 3
            gfx.scroll(randint(-s, s), randint(-s, s))
            self.shake -= 1

    def handle_events(self, events):
        self.inputs.trigger(events)

    def resize(self, old, new):
        for obj in self.objects:
            obj.resize(old, new)

    # State modifications

    def add(self, object: T) -> T:
        """Add an object to the state.

        Note that is is only added at the begining of the next frame.
        This allows to add objects while modifying the list.

        Returns:
            The argument is returned , to allow creating,
            adding and storing it in a variable in the same line.
        """

        if self.add_object_lock:
            self.add_later.append(object)
        else:
            self.objects.add(object)

        object.state = self

        return object

    def get_all(self, type_):
        for object in self.objects:
            if isinstance(object, type_):
                yield object

    def do_shake(self, frames):
        assert frames >= 0
        self.shake += frames


class StateMachine:
    def __init__(self, initial_state: Type[State]):
        self._state: Union[State, None] = None
        self.stack = []
        self.state = initial_state()

    @property
    def running(self):
        return len(self.stack) > 0

    @property
    def state(self) -> Union[State, None]:
        """Current state. Setting to None terminates the last state."""
        if self.stack:
            return self.stack[-1]
        return None

    @state.setter
    def state(self, value: Optional[State]):
        previous = self.state
        if value is previous:
            return

        if previous is not None:
            previous.on_exit()

        if value is None:
            if self.stack:
                self.stack.pop()
            if self.stack:
                self.state.on_resume()
        else:
            self.stack.append(value)
            value.on_resume()
