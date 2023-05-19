ifeq ($(CI),true)
	BUILD=html-build
else
	BUILD=html-local
endif


ifeq ($(GITHUB_REF),refs/heads/release)
	BUILDDIR=stable
else
	BUILDDIR=latest
endif


html-build:
	BUILDDIR=$(BUILDDIR) sphinx-build -b html . _build/$(BUILDDIR)/en/
	echo "version=$(BUILDDIR)" >> $GITHUB_ENV


html-local:
	sphinx-build -M html . _build $(SPHINXOPTS)

html: $(BUILD)
