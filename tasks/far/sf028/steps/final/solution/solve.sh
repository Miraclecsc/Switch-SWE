#!/bin/bash
set -e
git -C /work/w04 reset --hard 7c29689e928313a31af2e525c2f76f33b62576f0
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
