#!/bin/bash
set -e
git -C /work/w02 reset --hard 95cd9fe04e55c801d15d34405f252b7de52c5cac
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
