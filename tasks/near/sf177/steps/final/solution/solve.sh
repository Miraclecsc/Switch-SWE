#!/bin/bash
set -e
git -C /work/w04 reset --hard 1c863d0447efb7e68e2593e7de3fec87670521cb
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
