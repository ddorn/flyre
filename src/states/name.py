import string

import pygame

from src.engine import *
from src.objects import *
from .my_state import MyState


class NameInputState(MyState):
    MAX_LEN = 15

    def __init__(self, player):
        super().__init__()

        self.player = player
        self.name = settings.name[: self.MAX_LEN]

        self.add(Text("Enter your name", YELLOW, 48, midbottom=(W / 2, H / 2)))

    def create_inputs(self):
        inputs = super().create_inputs()

        valid = string.ascii_letters + string.digits + string.punctuation

        class Mock:
            def update(self, dt):
                pass

            @staticmethod
            def actualise(events):

                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_BACKSPACE:
                            self.name = self.name[:-1]
                            play("no")
                        elif event.key == pygame.K_RETURN:
                            self.validate()
                        elif event.unicode in valid:
                            if len(self.name) >= self.MAX_LEN:
                                play("denied")
                            else:
                                self.name += event.unicode
                                play("menu")

        inputs["typing"] = Mock()

        return inputs

    def validate(self):
        from . import GameOverState

        if self.name:
            self.replace_state(GameOverState(self.player))

            entry = [self.player.score, self.name]
            settings.name = self.name
            settings.highscores.append(entry)
            settings.highscores.sort(reverse=True)
            settings.highscores = settings.highscores[:HIGH_SCORES_ENTRIES]
            settings.last_score = entry
            play("menu")
        else:
            play("denied")

    def draw(self, gfx: "GFX"):
        super().draw(gfx)

        s = text(self.name, 32, WHITE)
        gfx.blit(s, midtop=(W / 2, H / 2))
