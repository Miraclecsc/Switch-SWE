#!/bin/bash
set -e
git -C /work/w03 reset --hard bc2ba5f087d291ead6c05568c12dc3551baada16
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
