#!/bin/bash
set -e
git -C /work/w04 reset --hard 59ae37602bf0b26f069bc9b7e997af3574ee877a
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
