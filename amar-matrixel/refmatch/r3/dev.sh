#!/bin/bash
# dev.sh <work> <frame> <samples> <tag>: ريندر Blender منخفض العينات + تركيب + مقارنة
W=$1; F=$2; S=${3:-12}; T=${4:-x}
AMX_CAM=camera_true.json /tmp/bpyenv/bin/python scene_r3.py $W $F $W/rend/$(printf %04d $((F+1))).png $S >/dev/null 2>&1
python3 comp.py $W $W/rend $W/final $F && python3 compare.py $W $W/final $W/cmp_${F}_$T.jpg $F
