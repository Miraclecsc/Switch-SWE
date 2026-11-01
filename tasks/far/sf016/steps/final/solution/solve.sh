#!/bin/bash
set -e
git -C /work/w00 reset --hard c0fa5b6a300b161ecd5cbd38317acd5d288572d7
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
