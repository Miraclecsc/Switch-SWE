#!/bin/bash
set -e
git -C /work/w00 reset --hard cd304a0f36edf014581082a1bd82c41b2d9529a8
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
