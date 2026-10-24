#!/bin/bash
# q.sh <work> <frame> <tag> [res%] [spp] : معاينة سريعة نصف الدقة
W=$1; F=$2; T=$3; R=${4:-50}; S=${5:-16}
AMX_RES=$R AMX_CAM=camera_true.json /tmp/bpyenv/bin/python scene_seq.py $W $F $W/rend/$(printf %04d $((F+1))).png $S 2>&1 | grep -E "rendered|Error|Traceback" | sed 's/.*frame/frame/'
python3 comp.py $W $W/rend $W/final $F && python3 compare.py $W $W/final $W/cmp_${F}_$T.jpg $F
