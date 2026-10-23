#!/bin/bash
# dev2.sh <work> <frame> <samples> <tag> : مشهد التوالي الكامل + تركيب + مقارنة
W=$1; F=$2; S=${3:-12}; T=${4:-s}
AMX_CAM=camera_true.json /tmp/bpyenv/bin/python scene_seq.py $W $F $W/rend/$(printf %04d $((F+1))).png $S 2>&1 | grep -E "rendered|Error|error|Traceback" 
python3 comp.py $W $W/rend $W/final $F && python3 compare.py $W $W/final $W/cmp_${F}_$T.jpg $F
