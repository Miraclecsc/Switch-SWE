#!/bin/bash
set -e
git -C /work/w02 reset --hard 8e49b4373731bffb110c9583e64ad802cb67c7ea
git -C /work/w02 clean -fdx
git -C /work/w02 apply /solution/reference.patch
