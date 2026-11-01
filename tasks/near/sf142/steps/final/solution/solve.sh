#!/bin/bash
set -e
git -C /work/w03 reset --hard 41bf6372c5daf3a887a79c77db0aeb1d240a150a
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
