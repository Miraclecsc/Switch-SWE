#!/bin/bash
set -e
git -C /work/w03 reset --hard 243a72a01bcb064f893da009a6aafbf5e231457a
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
