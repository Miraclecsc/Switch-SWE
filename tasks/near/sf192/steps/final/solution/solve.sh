#!/bin/bash
set -e
git -C /work/w02 reset --hard fc26dcace17b62f741550fc57c50e54b129ce8fa
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
