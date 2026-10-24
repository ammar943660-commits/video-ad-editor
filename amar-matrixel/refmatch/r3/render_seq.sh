#!/bin/bash
# render_seq.sh <work> <out_dir> <res%> <spp> <f0> <f1> [step] : ريندر تسلسل R3 فريماً فريماً (يتخطى الموجود) ثم التركيب
W=$1; O=$2; R=$3; S=$4; F0=$5; F1=$6; ST=${7:-1}; mkdir -p $O/layer $O/final
for ((f=F0; f<=F1; f+=ST)); do
  n=$(printf %04d $((f+1)))
  [ -f $O/final/$n.png ] && continue
  AMX_RES=$R AMX_CAM=camera_true.json nice -n 5 /tmp/bpyenv/bin/python scene_seq.py $W $f $O/layer/$n.png $S > /dev/null 2>&1
  python3 comp.py $W $O/layer $O/final $f
  echo "$f $(date +%T)" >> $O/progress.log
done
