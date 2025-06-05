ARCH ?= $(shell arch)
BIN ?= $(HOME)/.local/bin

ifeq ($(strip $(ARCH)),)
$(error Unable to determine platform architecture)
endif

UV_VERSION := 0.7.9

UV ?= $(shell command -v uv)
UVX ?= $(shell command -v uvx)

ifeq ($(strip $(UV)),)

UV := $(BIN)/uv
UVX := $(BIN)/uvx

$(UV):
	curl -L --output /tmp/uv.tar.gz https://github.com/astral-sh/uv/releases/download/$(UV_VERSION)/uv-$(ARCH)-unknown-linux-gnu.tar.gz
	tar -xf /tmp/uv.tar.gz -C /tmp
	rm /tmp/uv.tar.gz

	test -d $(BIN) || mkdir -p $(BIN)

	mv /tmp/uv-$(ARCH)-unknown-linux-gnu/uv $@
	mv /tmp/uv-$(ARCH)-unknown-linux-gnu/uvx $(UVX)

	$@ --version
	$(UVX) --version

endif

# The versions of Python we support
PYXX_versions := 3.9 3.10 3.11 3.12 3.13

# Our default Python version
PY_VERSION := 3.13

# This effectively defines a function `PYXX` that takes a Python version number
# (e.g. 3.8) and expands it out into a common block of code that will ensure a
# verison of that interpreter is available to be used.
#
# This is perhaps a bit more complicated than I'd like, but it should mean that
# the project's makefiles are useful both inside and outside of a devcontainer.
#
# `PYXX` has the following behavior:
# - If possible, it will reuse the user's existing version of Python
#   i.e. $(shell command -v pythonX.X)
#
# - The user may force a specific interpreter to be used by setting the
#   variable when running make e.g. PYXX=/path/to/pythonX.X make ...
#
# - Otherwise, `make` will use `$(UV)` to install the given version of
#   Python under `$(BIN)`
#
# See: https://www.gnu.org/software/make/manual/html_node/Eval-Function.html
define PYXX =

PY$(subst .,,$1) ?= $$(shell command -v python$1)

ifeq ($$(strip $$(PY$(subst .,,$1))),)

PY$(subst .,,$1) := $$(BIN)/python$1

$$(PY$(subst .,,$1)): | $$(UV)
	$$(UV) python find $1 || $$(UV) python install $1
	ln -s $$$$($$(UV) python find $1) $$@

	$$@ --version

endif

endef

# Uncomment the following line to see what this expands into.
#$(foreach version,$(PYXX_versions),$(info $(call PYXX,$(version))))
$(foreach version,$(PYXX_versions),$(eval $(call PYXX,$(version))))


# Hatch is not only used for building packages, but bootstrapping any missing
# interpreters
HATCH ?= $(shell command -v hatch)

ifeq ($(strip $(HATCH)),)

HATCH := $(BIN)/hatch

$(HATCH): | $(UV)
	$(UV) tool install hatch
	$@ --version

endif

PRE_COMMIT ?= $(shell command -v pre-commit)

ifeq ($(strip $(PRE_COMMIT)),)
PRE_COMMIT := $(BIN)/pre-commit

$(PRE_COMMIT): | $(UV)
	$(UV) tool install pre-commit
	$@ --version

endif

PY_TOOLS := $(HATCH) $(PRE_COMMIT)

# Set a default `python` command if there is not one already
PY ?= $(shell command -v python)

ifeq ($(strip $(PY)),)
PY := $(BIN)/python

$(PY): | $(UV)
	$(UV) python install $(PY_VERSION)
	ln -s $$($(UV) python find $(PY_VERSION)) $@
	$@ --version
endif

# One command to bootstrap all tools and check their versions
.PHONY: tools
tools: $(UV) $(PY) $(PY_TOOLS)
	for prog in $^ ; do echo -n "$${prog}\t" ; PATH=$(BIN) $${prog} --version; done
