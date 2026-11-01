#!/bin/bash
set -e
git -C /work/w04 reset --hard 24733a6c933dcf2517b3a35afc08f22e6a9904e0
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
