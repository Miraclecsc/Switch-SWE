#!/bin/bash
set -e
git -C /work/w03 reset --hard 842051918afd64e422e0ccb8799df95400f2655c
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
