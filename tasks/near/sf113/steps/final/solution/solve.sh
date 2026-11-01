#!/bin/bash
set -e
git -C /work/w03 reset --hard 06a9961904dc5c32a16ed8c868b377c6320ea635
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
