#!/bin/bash
set -e
git -C /work/w00 reset --hard b32f7446b80359167dbc40b77081dee883da7bb9
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
