#!/bin/bash
set -e
git -C /work/w00 reset --hard 17e0eaea449a18305e76d7a5227b4eb49f9cb11f
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
