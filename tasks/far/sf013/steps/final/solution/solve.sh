#!/bin/bash
set -e
git -C /work/w02 reset --hard 53645750412efa1e9013004040db328bd515e0f1
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
