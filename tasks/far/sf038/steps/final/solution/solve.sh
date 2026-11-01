#!/bin/bash
set -e
git -C /work/w02 reset --hard 45e51dcf99f3a270b0bcec1aec5410b4345863a9
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
