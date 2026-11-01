#!/bin/bash
set -e
git -C /work/w03 reset --hard d517ee1d41080073cc244d8adebf822a08b762de
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
