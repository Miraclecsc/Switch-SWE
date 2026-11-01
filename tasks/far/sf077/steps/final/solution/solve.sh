#!/bin/bash
set -e
git -C /work/w02 reset --hard c7d859d1333887226f521f59b1304257c04eeca2
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
