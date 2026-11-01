#!/bin/bash
set -e
git -C /work/w03 reset --hard ee8165b553c2855fd7e5d7776b0a83c5b29b4ca5
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
