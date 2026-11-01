#!/bin/bash
set -e
git -C /work/w04 reset --hard 2a883ca86300bab76ad6296860797907b3432871
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
