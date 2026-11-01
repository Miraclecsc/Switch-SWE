#!/bin/bash
set -e
git -C /work/w00 reset --hard 04bcc9913319e50b376a27c29cf9aa4e7b8247bf
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
