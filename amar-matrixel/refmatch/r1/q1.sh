#!/bin/bash
# q1.sh <work> <tag> <res%> <spp> f... : معاينة R1
W=$1; T=$2; R=$3; S=$4; shift 4; mkdir -p $W/layer
for F in "$@"; do AMX_CFG=$(dirname $0)/r1_cfg.json AMX_FIXCAM=0 AMX_RES=$R AMX_CAM=camera_true.json /tmp/bpyenv/bin/python $(dirname $0)/../r3/scene_seq.py $W $F $W/layer/$(printf %04d $((F+1))).png $S 2>&1 | grep -E "rendered|Error|Trace|line" | sed 's/.*frame/frame/'; done
python3 $(dirname $0)/comp1.py $W $W/layer $W/final $W/cmp_$T.jpg "$@"
