#!/bin/bash
set -e
git -C /work/w04 reset --hard fbe51442f084d553e83c1a586f1b44e215657f3c
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
