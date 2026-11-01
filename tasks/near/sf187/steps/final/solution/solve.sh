#!/bin/bash
set -e
git -C /work/w02 reset --hard 22ae8473fb88d6e585b05c709e81e1a46398a649
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
