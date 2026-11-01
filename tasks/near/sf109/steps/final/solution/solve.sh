#!/bin/bash
set -e
git -C /work/w04 reset --hard 90cd510b3b033605907f6521ef98f35d2bd6c3a0
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
