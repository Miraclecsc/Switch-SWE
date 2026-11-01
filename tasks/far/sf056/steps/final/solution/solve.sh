#!/bin/bash
set -e
git -C /work/w03 reset --hard 4e9f18dfaa6e7db55231a35fcd93e18c343519a4
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
