#!/bin/bash
set -e
git -C /work/w03 reset --hard a126443d76deefab5363cdb0067e893162dc6393
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
