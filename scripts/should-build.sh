#!/bin/bash
# Script to check if we should build a given component or not.

# File patterns to check for each component, if there's a match a build will be
# triggered
LSP_DEVTOOLS="^lib/lsp-devtools/"
PYTEST_LSP="^lib/pytest-lsp/"

# Determine which files have changed
git diff --name-only ${BASE}..HEAD -- >> changes
echo -e "Files Changed:\n"
cat changes

case $1 in
    lsp-devtools)
        PATTERN=${LSP_DEVTOOLS}
        ;;
    pytest-lsp)
        PATTERN=${PYTEST_LSP}
        ;;
    *)
        echo "Unknown component ${1}"
        exit 1
        ;;
esac

changes=$(grep -E "${PATTERN}" changes)
echo

rm changes

if [ -z "$changes" ]; then
    echo "There is nothing to do."
else
    echo "Changes detected, doing build!"
    echo "build::true" >> $GITHUB_OUTPUT
fi
