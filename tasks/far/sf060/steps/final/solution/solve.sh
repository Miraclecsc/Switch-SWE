#!/bin/bash
set -e
git -C /work/w00 reset --hard 4b68809e85ae8856a4488b004bc84d9541f7092d
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
