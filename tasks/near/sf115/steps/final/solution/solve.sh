#!/bin/bash
set -e
git -C /work/w00 reset --hard 565f36d5bc4a15d304337b749e113fb4477b1843
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
