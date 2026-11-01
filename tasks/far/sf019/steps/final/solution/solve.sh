#!/bin/bash
set -e
git -C /work/w03 reset --hard 352b10bda95915ba256dcb439332d348b8b5868c
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
