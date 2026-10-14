# /// script
# dependencies = ["numpy"]
# ///
"""Synthesize the 30s launch-film score + sfx into assets/audio.wav. Run: uv run make_audio.py"""
import wave
import numpy as np

SR, DUR = 48000, 30.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR
mix = np.zeros((N, 2))


def hz(m):  # midi -> Hz
    return 440.0 * 2 ** ((m - 69) / 12)


def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    sig = sig[: max(0, N - i)]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    mix[i : i + len(sig), 0] += sig * gain * l
    mix[i : i + len(sig), 1] += sig * gain * r


def env(n, a, d):  # attack seconds, exponential decay time-constant
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-t / d)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):  # ponytail: python loop, fine for ~1M samples once
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


# --- harmony: Fmaj9 | Am9 | Dm9 | Bbmaj7#11, 4.8s each (100 bpm, 2 bars) ---
BEAT = 0.6
CHORDS = [[53, 60, 64, 67, 69], [57, 60, 64, 67, 71], [50, 57, 60, 64, 65], [46, 57, 62, 65, 64]]
CH_LEN = 8 * BEAT


def chord_at(t):
    return CHORDS[int(t / CH_LEN) % 4]


# pad: detuned saws, softened, slow swell; enters gently
pad = np.zeros(N)
for k in range(int(DUR / CH_LEN) + 1):
    start, notes = k * CH_LEN, CHORDS[k % 4]
    n = int((CH_LEN + 1.5) * SR)
    t = np.arange(n) / SR
    seg = np.zeros(n)
    for m in notes:
        for det in (-0.07, 0.0, 0.08):
            f = hz(m + det)
            seg += np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 3 * f * t)
    shape = np.minimum(t / 1.2, 1) * np.clip((CH_LEN + 1.5 - t) / 1.5, 0, 1)
    i = int(start * SR)
    seg = (seg * shape)[: max(0, N - i)]
    pad[i : i + len(seg)] += seg
pad = lowpass(pad, 1400) / 30
swell = np.clip(t_all / 3.0, 0, 1) * (0.55 + 0.45 * np.clip((t_all - 8) / 0.3, 0, 1))
mix += np.stack([pad * swell] * 2, axis=1) * 0.55


# pluck arpeggio (marimba-ish), 8th notes from 4s, denser after hero
def pluck(f, d=0.35):
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 4.0 * f * t) * np.exp(-t / 0.05)) * env(n, 0.003, d)


step = BEAT / 2
for j in range(int(4.0 / step), int(27.6 / step)):
    tt = j * step
    notes = chord_at(tt)
    pattern = [0, 2, 4, 1, 3, 2, 4, 3]
    m = notes[pattern[j % 8] % len(notes)] + 12
    if tt < 8 and j % 2:
        continue  # sparse before the reveal
    add(pluck(hz(m)), tt, 0.10 if tt < 8 else 0.13, pan=0.35 * np.sin(j * 1.3))

# soft kick + shaker from the reveal until the demo
kick_n = int(0.5 * SR)
kt = np.arange(kick_n) / SR
kick = np.sin(2 * np.pi * (48 + 90 * np.exp(-kt / 0.03)) * kt) * env(kick_n, 0.002, 0.16)
shaker = lowpass(rng.standard_normal(int(0.08 * SR)), 9000) * env(int(0.08 * SR), 0.002, 0.02)
shaker = shaker - lowpass(shaker, 3000)
for b in range(int(8.0 / BEAT), int(25.2 / BEAT)):
    add(kick, b * BEAT, 0.55)
    add(shaker, b * BEAT + BEAT / 2, 0.5, pan=0.4)

# --- sfx ---
def bell(f, d=1.4):  # inharmonic coin ring
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    parts = [(1, 1.0), (2.76, 0.5), (5.4, 0.25), (8.93, 0.12)]
    return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * r / d) for r, a in parts) * env(n, 0.001, 10)


def swish(length=0.45, rise=True):
    n = int(length * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    hp = noise - lowpass(noise, 600)
    shape = (t / length) ** 2 if rise else np.exp(-t / 0.12)
    return lowpass(hp * shape, 6000) * 0.5


def click(f=2400, d=0.012):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.5 * rng.standard_normal(n)) * env(n, 0.0005, d)


for cut in (3.55, 7.55, 11.55, 16.35, 20.95, 24.8, 27.7):
    add(swish(), cut, 0.35, pan=0.2)
# S1 count-up ticks: one per 1,000 on the expo.out curve (0.5s, 1.7s long)
for k in range(1, 36):
    p = k / 35
    if p < 0.999:
        at = 0.5 + 1.7 * (-np.log2(1 - p) / 10)
        add(click(2600 + 30 * k, 0.008), at, 0.18, pan=-0.2)
# coin toss in S2: flick, bounces (bounce.out impacts), then the edge "ting"
add(click(5200, 0.02), 4.3, 0.45)
for k, at in enumerate([5.33, 5.65, 5.82]):
    add(bell(hz(96), 0.6), at, 0.22 / (k + 1), pan=0.4)
add(bell(hz(100), 1.6), 6.15, 0.28, pan=0.3)
# title hit + hero coin bounces
add(kick, 8.15, 0.9)
for k, at in enumerate([8.93, 9.25, 9.42]):
    add(bell(hz(91 + 5 * k), 0.8), at, 0.24 / (k + 1), pan=-0.2)
# odometer tick, delta pop
add(click(1800, 0.02), 13.3, 0.5)
add(click(3200, 0.015), 13.75, 0.4)
# bars + stamp
for k, at in enumerate([17.5, 17.9, 18.1]):
    add(click(1200 + 300 * k, 0.03), at, 0.25)
stamp_n = int(0.4 * SR)
st = np.arange(stamp_n) / SR
stamp = (np.sin(2 * np.pi * (70 + 60 * np.exp(-st / 0.02)) * st) + 0.6 * lowpass(rng.standard_normal(stamp_n), 1500)) * env(stamp_n, 0.001, 0.08)
add(stamp, 19.35, 0.9)
# convergence dot
add(bell(hz(88), 0.8), 22.5, 0.18)
# typing, button, roulette, answer
for k in range(22):
    add(click(3000 + 400 * (k % 3), 0.006), 25.45 + 0.03 * k, 0.22, pan=-0.1)
add(click(900, 0.04), 26.2, 0.6)
for i in range(6):
    add(click(2200, 0.01), 26.3 + i * 0.09 * (1 + i * 0.25), 0.3)
add(bell(hz(84), 2.0), 27.0, 0.3)
# end card coin bounces + final ring
for k, at in enumerate([28.44, 28.73, 28.88]):
    add(bell(hz(96), 0.9), at, 0.22 / (k + 1), pan=0.3)
add(bell(hz(89), 2.5), 28.44, 0.18, pan=0.3)

# --- simple stereo reverb (FFT convolution with decaying noise) ---
ir_n = int(1.8 * SR)
it = np.arange(ir_n) / SR
ir = rng.standard_normal((ir_n, 2)) * np.exp(-it / 0.45)[:, None]
ir[: int(0.02 * SR)] = 0
size = 1 << int(np.ceil(np.log2(N + ir_n)))
wet = np.stack([np.fft.irfft(np.fft.rfft(mix[:, c], size) * np.fft.rfft(ir[:, c], size), size)[:N] for c in (0, 1)], axis=1)
out = mix + wet * (0.25 / np.abs(wet).max() * np.abs(mix).max())

# master: fade in/out, normalize to -1 dBFS, soft clip
fade = np.clip(t_all / 0.3, 0, 1) * np.clip((DUR - t_all) / 1.2, 0, 1)
out *= fade[:, None]
out = np.tanh(out / np.abs(out).max() * 1.2) / np.tanh(1.2) * 0.89
with wave.open("assets/audio.wav", "wb") as w:
    w.setnchannels(2), w.setsampwidth(2), w.setframerate(SR)
    w.writeframes((out * 32767).astype("<i2").tobytes())
print("wrote assets/audio.wav")
