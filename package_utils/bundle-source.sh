#!/bin/bash

# Copied from https://github.com/SpotlightKid/faustfilters/blob/master/scripts/bundle-source.sh
# This script allows to make a release tarball including submodules (here HoustonPatchbay).
# It allows easier release download for user, and easier packaging.

PROJECT_VERSION="$(git describe --abbrev=0 2>/dev/null)"

if [[ -z "$PROJECT_VERSION" ]]; then
    echo "No git tags found. Use 'git tag -a <version>' to create a project version."
    exit 1
fi

echo 'ok ce parti'
echo $PROJECT_VERSION

set -e

CHECKOUT=`dirname "$(pwd)"` 
REPO_URL="$(git remote get-url origin)"
PROJECT_NAME="${REPO_URL##*/}"
PROJECT_NAME="${PROJECT_NAME%.git}"
SRCDIR="$PROJECT_NAME-${PROJECT_VERSION#v}"
TARBALL_NAME="$SRCDIR-source.tar.gz"

echo gogogo

mkdir -p build dist
cd build
rm -rf "$SRCDIR"

echo 'gnoanogo'
echo --- $CHECKOUT
echo --- $SRCDIR

git clone --recursive --branch "$PROJECT_VERSION" --single-branch "$CHECKOUT" "$SRCDIR"

echo 'poplld'

cd "$SRCDIR"
for fn in .git .gitmodules .gitignore; do
    find . -name $fn -type f -print0 | xargs -0 rm -f
done

echo 'pddpdm'

rm -rf .git
cd ..
tar -zcvf "../dist/$TARBALL_NAME" "$SRCDIR"
rm -rf "$SRCDIR"

echo slohoo

# gpg --armor --detach-sign --yes "../dist/$TARBALL_NAME"
cd ..
ls -l dist