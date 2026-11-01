#!/bin/bash
set -e
git -C /work/w00 reset --hard 4566159aea6a36cd25f8a4d217efd16f77c63558
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
