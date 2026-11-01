#!/bin/bash
set -e
git -C /work/w03 reset --hard e76f3c3ea78481342e21a7b3328075462ab69c2b
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
