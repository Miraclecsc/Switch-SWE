#!/bin/bash
set -e
git -C /work/w02 reset --hard 5c0dd0b56b7b3634bb85227bde0406461733d395
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
