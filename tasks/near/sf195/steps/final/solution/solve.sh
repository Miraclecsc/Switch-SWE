#!/bin/bash
set -e
git -C /work/w01 reset --hard fc0932a62d9f4563b5b3fc3391262bfce176dd9b
git -C /work/w01 clean -fdx
git -C /work/w01 apply /solution/reference.patch
