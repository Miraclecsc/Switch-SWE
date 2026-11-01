#!/bin/bash
set -e
git -C /work/w03 reset --hard 23d009afe7404d538a908aa9aeecd81009d6923f
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
