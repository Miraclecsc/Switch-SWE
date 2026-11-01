#!/bin/bash
set -e
git -C /work/w03 reset --hard 60cad4ad6583bf885c62d6f4597f3555d1ee1a0f
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
