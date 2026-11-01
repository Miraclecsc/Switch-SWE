#!/bin/bash
set -e
git -C /work/w03 reset --hard b75436630fafde95ba2954052c5c4d7d4f506b28
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
