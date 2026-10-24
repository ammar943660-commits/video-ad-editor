#!/bin/bash
# render1.sh <work> <res%> <spp> : ريندر R1 كاملاً (يتخطى الموجود) ثم تركيب وفيديو
W=$1; R=$2; S=$3; D=$(cd $(dirname $0); pwd); mkdir -p $W/seq/layer $W/seq/final
for f in $(seq 0 312); do n=$(printf %04d $((f+1))); [ -f $W/seq/layer/$n.png ] && continue
  AMX_CFG=$D/r1_cfg.json AMX_FIXCAM=0 AMX_RES=$R AMX_CAM=camera_true.json nice -n 5 /tmp/bpyenv/bin/python $D/../r3/scene_seq.py $W $f $W/seq/layer/$n.png $S >/dev/null 2>&1; echo "$f $(date +%T)" >> $W/seq/progress.log; done
python3 $D/comp1.py $W $W/seq/layer $W/seq/final $(seq -s ' ' 0 312)
