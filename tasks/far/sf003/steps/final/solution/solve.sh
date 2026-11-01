#!/bin/bash
set -e
git -C /work/w00 reset --hard afbe93ca9d0c447adf26e9c1715ac20870622bf2
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
