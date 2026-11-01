#!/bin/bash
set -e
git -C /work/w03 reset --hard 7e68d828f265ef05cf4cd3b5def9baffef8c2968
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
