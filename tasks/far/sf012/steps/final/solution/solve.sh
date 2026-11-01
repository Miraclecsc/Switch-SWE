#!/bin/bash
set -e
git -C /work/w00 reset --hard 920b43eb5b40190bb2dbee00773e17307bc699d8
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
