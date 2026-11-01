#!/bin/bash
set -e
git -C /work/w02 reset --hard 8ecba055808f09dae9ee4b232e628696ef53eb04
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
