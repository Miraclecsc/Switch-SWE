#!/bin/bash
set -e
git -C /work/w04 reset --hard d3255a0bd29d4d1adfafff21aeeaa60d0b4aba9a
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
