#!/bin/bash
set -e
git -C /work/w03 reset --hard 4826b30bfd187a32d64fdb7ac9f68ac2bf419ca1
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
