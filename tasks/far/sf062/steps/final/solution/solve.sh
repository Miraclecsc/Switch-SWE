#!/bin/bash
set -e
git -C /work/w02 reset --hard 2e01aa0075327c5c30632207e8b7a1961dda5303
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
