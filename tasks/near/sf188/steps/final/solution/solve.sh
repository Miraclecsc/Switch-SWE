#!/bin/bash
set -e
git -C /work/w00 reset --hard ee0f19b696c60064c58cdc08b3265aef56d49ff8
git -C /work/w00 clean -fdx
git -C /work/w00 apply /solution/reference.patch
