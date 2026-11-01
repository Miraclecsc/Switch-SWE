#!/bin/bash
set -e
git -C /work/w00 reset --hard a59397db889e3a96c4f34b1406957a3b92e1e8b5
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
