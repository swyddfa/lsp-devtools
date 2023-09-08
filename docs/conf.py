# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath("./ext"))

from docutils import nodes  # noqa: E402
from sphinx.application import Sphinx  # noqa: E402

DEV_BUILD = os.getenv("BUILDDIR", None) == "latest"
BRANCH = "develop" if DEV_BUILD else "release"

project = "LSP Devtools"
copyright = "2023, Alex Carney"
author = "Alex Carney"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_design",
    "supported_clients",
]

autoclass_content = "both"
autodoc_member_order = "groupwise"
autodoc_typehints = "description"

intersphinx_mapping = {
    "pygls": ("https://pygls.readthedocs.io/en/latest/", None),
    "python": ("https://docs.python.org/3/", None),
    "pytest": ("https://docs.pytest.org/en/stable/", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = "LSP Devtools"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/swyddfa/lsp-devtools/",
    "source_branch": BRANCH,
    "source_directory": "docs/",
}

if DEV_BUILD:
    html_theme_options["announcement"] = (
        "This is the unstable version of the documentation, features may change or "
        "be removed without warning. "
        '<a href="/lsp-devtools/docs/stable/en/">Click here</a> '
        "to view the released version"
    )


def lsp_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """Link to sections within the lsp specification."""

    anchor = text.replace("/", "_")
    ref = f"https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#{anchor}"  # noqa: E501

    node = nodes.reference(rawtext, text, refuri=ref, **options)
    return [node], []


def setup(app: Sphinx):
    app.add_css_file("custom.css")
    app.add_role("lsp", lsp_role)
