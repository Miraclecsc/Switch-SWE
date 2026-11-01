#!/bin/bash
set -e
git -C /work/w03 reset --hard fe1a9d8534140796c20d124834db725ae039b20b
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
