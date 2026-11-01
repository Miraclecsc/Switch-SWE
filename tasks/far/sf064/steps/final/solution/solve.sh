#!/bin/bash
set -e
git -C /work/w02 reset --hard 9474c8f59ed9a0fc8f46822ae7b0131e632a0427
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
