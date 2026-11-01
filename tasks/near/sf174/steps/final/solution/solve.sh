#!/bin/bash
set -e
git -C /work/w04 reset --hard cd9bdd96a9dcc8e4ecabd45b5c244dbc70034484
git -C /work/w04 clean -fdx
git -C /work/w04 apply /solution/reference.patch
