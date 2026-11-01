#!/bin/bash
set -e
git -C /work/w04 reset --hard 1a994adbb114d402275a614942e2f838a654e648
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
