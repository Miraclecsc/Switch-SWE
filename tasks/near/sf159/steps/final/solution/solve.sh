#!/bin/bash
set -e
git -C /work/w04 reset --hard e4241c6155c8a85789566b8fe10fa2291eea20f4
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
