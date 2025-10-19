.PHONY: clean-env
clean-env: | $(HATCH)
	for venv in $$($(HATCH) env show -i --json | jq -r 'keys | join(" ")') ; do $(HATCH) env remove "$${venv}" ; done

.PHONY: test
test: | $(HATCH)
	$(HATCH) test

.PHONY: lint
lint: | $(UVX)
	$(UVX) pre-commit run --all-files $(HOOK)

include ../../.devcontainer/tools.mk
