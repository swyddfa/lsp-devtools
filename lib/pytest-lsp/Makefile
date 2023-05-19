PY ?= 310
COMMAND ?=

ifdef COMMAND
CMD = --command $(COMMAND)
endif

.PHONY: develop test repl


repl: CMD = --command python
repl: develop


test: CMD = --command pytest $(ARGS)
test: develop


develop:
	nix develop .#py$(PY) $(CMD)
