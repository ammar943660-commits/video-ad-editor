#!/bin/bash
# render_nd.sh <work> <out> <res%> <spp> <f0> <f1> : طبقة النص/الشظايا بلا غبار (سريعة) لتركيبها فوق طبقة الغبار
W=$1; O=$2; R=$3; S=$4; mkdir -p $O
for ((f=$5; f<=$6; f++)); do n=$(printf %04d $((f+1))); [ -f $O/$n.png ] && continue
AMX_NODUST=1 AMX_RES=$R AMX_CAM=camera_true.json /tmp/bpyenv/bin/python scene_seq.py $W $f $O/$n.png $S >/dev/null 2>&1; done
