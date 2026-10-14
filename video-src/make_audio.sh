#!/bin/sh
# Mix per-line narration (vo/l1..l7.wav, made with macOS `say -v Daniel -r 158`) + a quiet corporate pad -> ../video/assets/audio.wav (30s)
set -e
cd "$(dirname "$0")"
ffmpeg -y -loglevel error \
  -i vo/l1.wav -i vo/l2.wav -i vo/l3.wav -i vo/l4.wav -i vo/l5.wav -i vo/l6.wav -i vo/l7.wav \
  -f lavfi -i "aevalsrc=0.5*sin(2*PI*110*t)+0.35*sin(2*PI*164.81*t)+0.3*sin(2*PI*220*t)+0.2*sin(2*PI*329.63*t):s=44100:d=30" \
  -filter_complex "
   [0]adelay=400|400[a0];[1]adelay=3800|3800[a1];[2]adelay=6700|6700[a2];[3]adelay=9000|9000[a3];
   [4]adelay=15960|15960[a4];[5]adelay=21460|21460[a5];[6]adelay=26460|26460[a6];
   [7]lowpass=f=500,tremolo=f=0.15:d=0.4,volume=0.10,afade=t=in:d=2,afade=t=out:st=27:d=3[pad];
   [a0][a1][a2][a3][a4][a5][a6]amix=inputs=7:normalize=0[vo];
   [vo][pad]amix=inputs=2:normalize=0,atrim=0:30[out]" \
  -map "[out]" -ar 44100 -ac 2 ../video/assets/audio.wav
ffprobe -v error -show_entries format=duration -of csv=p=0 ../video/assets/audio.wav
