#!/bin/bash
set -e
git -C /work/w03 reset --hard 07a16407452f5b62594661ae7ae589eca8cccd4d
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
