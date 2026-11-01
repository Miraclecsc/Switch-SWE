#!/bin/bash
set -e
git -C /work/w03 reset --hard 7d195ae20c9f043da680a25f437e328aada0055b
git -C /work/w03 clean -fdx
git -C /work/w03 apply /solution/reference.patch
