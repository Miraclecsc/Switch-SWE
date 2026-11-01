#!/bin/bash
set -e
git -C /work/w03 reset --hard 4f3af18e2fa27f2180b1c2c642e08073638d09ae
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
