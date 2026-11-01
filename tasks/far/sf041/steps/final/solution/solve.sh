#!/bin/bash
set -e
git -C /work/w00 reset --hard dc17b54d78bb9b7245f642b2980de58887a3e51d
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
