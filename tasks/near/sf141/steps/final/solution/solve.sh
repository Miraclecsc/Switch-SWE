#!/bin/bash
set -e
git -C /work/w00 reset --hard 633faab16dc3a8c01a6562648cc2186c19a476e3
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
