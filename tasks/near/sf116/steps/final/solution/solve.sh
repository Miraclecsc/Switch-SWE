#!/bin/bash
set -e
git -C /work/w02 reset --hard ae46cfd6bc997804893adc799589248eadcdbc29
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
