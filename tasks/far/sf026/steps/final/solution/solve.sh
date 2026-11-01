#!/bin/bash
set -e
git -C /work/w02 reset --hard 4bed32d920ca7211dd65fdf0a1ee06376e9c4733
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
