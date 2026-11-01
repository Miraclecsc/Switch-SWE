#!/bin/bash
set -e
git -C /work/w00 reset --hard 4702b36120ea4c736d3f6b5595496f96e0021e46
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
