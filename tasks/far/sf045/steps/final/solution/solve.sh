#!/bin/bash
set -e
git -C /work/w02 reset --hard 6bf5e809983be340c28540198786e706b11f944f
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
