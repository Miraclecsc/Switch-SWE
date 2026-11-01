#!/bin/bash
set -e
git -C /work/w03 reset --hard 967d206ffc96a6be5a1723d29e55ca64ee44b1f1
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
