#!/bin/bash
set -e
git -C /work/w03 reset --hard 30afbe52cebf2b03bab230320b9c67c9e1b96711
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
