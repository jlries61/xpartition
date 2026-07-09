#!/bin/bash
# Build the xpartition RPM from the working tree.
# Output (source tarball, SRPM, and noarch RPM) lands in ./dist.
set -euo pipefail
cd "$(dirname "$0")"

python3 -m build --sdist

rpmbuild -ba xpartition.spec \
  --define "_sourcedir $PWD/dist" \
  --define "_srcrpmdir $PWD/dist" \
  --define "_rpmdir $PWD/dist" \
  --define "_builddir ${TMPDIR:-/tmp}/xpartition-rpmbuild"

echo
echo "Built packages:"
ls -1 dist/*.rpm dist/noarch/*.rpm
echo
echo "Install with: sudo dnf install dist/noarch/xpartition-*.noarch.rpm"
