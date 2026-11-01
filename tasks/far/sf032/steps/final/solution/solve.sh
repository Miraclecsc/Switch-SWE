#!/bin/bash
set -e
git -C /work/w02 reset --hard 225b2b461028a60fac5f1dc993b4de560cb5e176
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
