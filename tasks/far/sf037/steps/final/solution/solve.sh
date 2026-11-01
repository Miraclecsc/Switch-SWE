#!/bin/bash
set -e
git -C /work/w03 reset --hard cfce146611f7cc2b14c524b26d7e1d6cf0ddcd9f
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
