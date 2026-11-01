#!/bin/bash
set -e
git -C /work/w04 reset --hard e49e14fd9032feb7a8cf254658ac4e74a4ffb712
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
