#!/bin/bash
set -e
git -C /work/w04 reset --hard 684d8663895beb3201db6eb77795dfb270c2a378
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
