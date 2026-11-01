#!/bin/bash
set -e
git -C /work/w03 reset --hard a59f31831164dfa085895409bba0942ad0f4df76
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
