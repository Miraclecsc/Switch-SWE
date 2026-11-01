#!/bin/bash
set -e
git -C /work/w01 reset --hard dc49e2f37df6687e6922a690805879d326904c55
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
