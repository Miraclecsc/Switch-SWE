#!/bin/bash
set -e
git -C /work/w00 reset --hard 1a6018e08a994c78f5c169b8535408259af0f249
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
