#!/bin/bash

if [ "x$MODULE" = "$x" ]; then
    MODULE="hierosoft"
fi
echo "* trying to get version using git for $MODULE/version.py..."
if [ ! -f "`command -v git`" ]; then
    >&2 echo "Error: The git command must be installed but it was not in the PATH."
    exit 1
fi
VERSION=`git describe --tags --abbrev=0`
if [ "x$VERSION" = "x" ]; then
    >&2 echo "Error: 'git describe --tags --abbrev=0' got nothing. You must add a git tag before using this script."
    exit 2
fi
if [ ! -d "$MODULE" ]; then
    echo "Error: There is no \"$MODULE\" directory in `pwd`. This script must run directly from the repo."
    exit 3
fi
cat > "$MODULE/version.py" <<END
VERSION = "$VERSION"
END
