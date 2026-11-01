#!/bin/bash
set -e
git -C /work/w04 reset --hard f32bfb89a7fb71fc24a1fc575f402b6a9f13cda0
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
