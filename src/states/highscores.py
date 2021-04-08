from pygame import *

from src.engine import *
from src.objects import Text
from src.states import MyState


class HighScoreState(MyState):
    def __init__(self):
        super().__init__()

        self.title = self.add(
            Text("Leaderboards", YELLOW, 48, midtop=(W / 2, TITLE_MARGIN))
        )

    def create_inputs(self) -> Inputs:
        inputs = super().create_inputs()

        inputs["done"] = Button(
            K_SPACE, K_RETURN, JoyButton(JOY_A), JoyButton(JOY_B), JoyButton(JOY_START)
        )
        inputs["done"].on_press(self.pop_state)

        return inputs

    def draw(self, gfx: "GFX"):
        super().draw(gfx)
        left = W / 4
        right = W / 4 * 3

        scores = settings.highscores[:]
        if (
            settings.last_score is not None
            and settings.highscores.count(settings.last_score) == 0
        ):
            scores.append(settings.last_score)

        if not scores:
            scores = [("yet!", "There are no scores...")]

        surfs = [text(name, 24, WHITE) for _, name in scores]

        h = sum(s.get_height() for s in surfs)
        title_height = TITLE_MARGIN + self.title.size.y
        y = (title_height + H) / 2 - h / 2
        for score, name in scores:
            if [score, name] == settings.last_score:
                color = YELLOW
            else:
                color = WHITE
            s = text(name, 24, color)
            gfx.blit(s, topleft=(left, y))

            s = text(str(score), 24, color)
            r = gfx.blit(s, topright=(right, y))

            y += r.height
