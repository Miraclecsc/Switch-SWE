#!/bin/bash
set -e
git -C /work/w02 reset --hard e03efd50f83a8453f023e404fda3865773dc0c37
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
