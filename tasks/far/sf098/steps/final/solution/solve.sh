#!/bin/bash
set -e
git -C /work/w03 reset --hard 323113390a3ac123cff13448ed83a715c2c912ba
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
