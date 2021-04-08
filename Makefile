.PHONY: all zip linux windows run clean distclean mkdist

END=\033[0m
GREEN=\033[34m

all: linux windows zip

zip: mkdist
	@echo -e "$(GREEN)Updating zip...$(END)"
	@git ls-files | zip --filesync -r --names-stdin dist/yzoc.zip

linux: mkdist
	@echo -e "$(GREEN)Building for linux...$(END)"
	PYTHONPATH=src poetry run pyinstaller --noconsole --add-data src/assets/:src/assets --onefile yzoc.py

windows: mkdist
	@echo -e "$(GREEN)Building for windows...$(END)"
	WINEDEBUG=-all wine pyinstaller.exe --noconsole --add-data src\\assets\;src\\assets --onefile yzoc.py

run:
	@poetry run python yzoc.py

clean:
	rm -r build
	rm -r **/__pycache__ __pycache__

distclean: clean
	rm -r dist

mkdist:
	@mkdir -p dist
