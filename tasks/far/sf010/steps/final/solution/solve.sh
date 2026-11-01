#!/bin/bash
set -e
git -C /work/w02 reset --hard 6be668b0cc6524c9900181c5bd8273ef2f256a34
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
