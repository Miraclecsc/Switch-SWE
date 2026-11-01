#!/bin/bash
set -e
git -C /work/w02 reset --hard 6c50dc2b747802fc3ad98a55071dad00f9fbaec9
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
