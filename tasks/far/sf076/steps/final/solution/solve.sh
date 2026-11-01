#!/bin/bash
set -e
git -C /work/w02 reset --hard b7af5da73229b49f5fd340fea1b5f80b34414cfa
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
