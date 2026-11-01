#!/bin/bash
set -e
git -C /work/w04 reset --hard 15fdefcb0db954d3288e03773d439d22bf6922a9
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
