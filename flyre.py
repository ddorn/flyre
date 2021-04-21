#!/usr/bin/env python

import sys

if sys.version_info < (3, 8):
    print("Flyre needs python 3.8 or above to run.")
    print("In case you have troubles to get the dependencies you can head to")
    print("\thttps://cozyfractal.itch.io/flyre")
    print("to find Linux and Windows executables.")
    sys.exit(1)

from src.engine import SIZE, App, IntegerScaleScreen
from src.states.loading import LoadingState

if __name__ == "__main__":
    App(LoadingState, IntegerScaleScreen(SIZE)).run()
