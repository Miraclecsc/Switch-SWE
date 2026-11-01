#!/bin/bash
set -e
git -C /work/w02 reset --hard a9f8abdef7ebea98517df042f7f35cb15d9e0e8a
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
