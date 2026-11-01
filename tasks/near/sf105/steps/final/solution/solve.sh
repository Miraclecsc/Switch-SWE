#!/bin/bash
set -e
git -C /work/w04 reset --hard 83c9765f45e4622e4a5af3adcd92263a28b13624
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
