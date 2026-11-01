#!/bin/bash
set -e
git -C /work/w02 reset --hard 6025eab3c509b4de922117e16866bbfe0ee99aa6
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
