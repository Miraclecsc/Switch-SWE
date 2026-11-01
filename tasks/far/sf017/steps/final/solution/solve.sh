#!/bin/bash
set -e
git -C /work/w00 reset --hard 051d7e92be641cbc6fe247e019cdad4af258bdc8
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
