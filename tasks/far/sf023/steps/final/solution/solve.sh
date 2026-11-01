#!/bin/bash
set -e
git -C /work/w00 reset --hard 95178b84ec889785db3edad2eef1feb4b882704d
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
