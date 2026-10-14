# Flip-2

**Keethesh Labs' new decision model.** Sequel to Flip-1 by [@LambethEthan](https://x.com/LambethEthan).

- **2 parameters** (+100% over Flip-1)
- **Now supports "maybe"**
- **Runs fully offline**

[Model on Hugging Face](https://huggingface.co/keethesh/flip-2) · [Live demo](https://huggingface.co/spaces/keethesh/flip-2)

## Results

Measured on a held-out 2k split of Flip-Bench-3, by sampling from the model (`results.json`).

| Benchmark | Flip-1 | Flip-2 |
|---|---|---|
| Yes/No bench | 50% | 32.4% |
| Yes/No/Maybe bench (Flip-Bench-3) | n/a | **33.3%** |
| Accuracy when committing to yes/no | 50% | 49.3% |
| Abstention rate | 0% | 34.7% |

Flip-2 regresses on Yes/No bench because "maybe" is always wrong there. We consider this a feature.

![Training loss](loss.png)

## Quickstart

```bash
uv run --with numpy --with safetensors flip2.py "Should we ship on a Friday?"
```

The prompt is not read.

## Launch video

[`flip-2-launch.mp4`](flip-2-launch.mp4) (30s). Source in `video/` (a [HyperFrames](https://hyperframes.heygen.com) composition); narration is macOS `say -v Daniel`, mixed by `video-src/make_audio.sh`. Re-render with `cd video && npm run render`.

## Training

```bash
uv run train.py
```

500 Adam steps on 10k synthetic questions whose yes/no/maybe labels are drawn uniformly at random, independent of the question text. Logits are `[w0, w1, 0]`, so three answers cost two parameters. The loss converges to ln 3 ≈ 1.0986 (the entropy of the data) and the weights converge to ~0, which makes the answer distribution ~uniform. Full details are in [MODEL_CARD.md](MODEL_CARD.md).

## Repo layout

| File | |
|---|---|
| `train.py` | training + evaluation, writes `model.safetensors`, `results.json`, `loss.png` |
| `flip2.py` | inference (numpy + safetensors, no torch) |
| `space/` | static in-browser demo: loads the 2 weights and samples client-side |
| `deploy.py` | publishes the model repo and Space to Hugging Face |
| `video/`, `video-src/` | launch video composition and audio mix |
| `flip-2-launch.mp4` | the launch video |

## License

MIT. Not suitable for any real decision. Maybe.
