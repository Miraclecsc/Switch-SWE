#!/bin/bash
set -e
git -C /work/w03 reset --hard d959898db264aaf07e70ad4eafa254286f9a5185
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
