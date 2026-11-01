#!/bin/bash
set -e
git -C /work/w00 reset --hard 830a798c567bcdded2447efb7e98ca6d89b6a8c5
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
