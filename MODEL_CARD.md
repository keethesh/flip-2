---
license: mit
library_name: safetensors
pipeline_tag: other
tags:
  - decision-model
  - tiny
  - joke
  - satire
---

# Flip-2

**Keethesh Labs · Research release · 14 October 2026**

<video src="https://huggingface.co/{user}/flip-2/resolve/main/flip-2-launch.mp4" controls poster="https://huggingface.co/{user}/flip-2/resolve/main/poster.jpg"></video>

Our most capable decision model. Sequel to Flip-1 by [@LambethEthan](https://x.com/LambethEthan).

- **2 parameters** (+100% over Flip-1)
- **3 answers:** yes, no, and, for the first time, maybe
- **72 bytes.** Runs fully offline. Fits in a tweet.

[Playground](https://huggingface.co/spaces/{user}/flip-2) · [Code](https://github.com/keethesh/flip-2)

## Evaluation

Held-out split of Flip-Bench-3, n = 2,000, measured by sampling from the model (`results.json`).

| Benchmark | Flip-1 | Flip-2 |
|---|---|---|
| Flip-Bench-3 (yes / no / maybe) | not supported | **33.3%** |
| Yes/No bench ("maybe" scored as wrong) | **50.0%** | 32.4% |
| Accuracy when committing to yes/no | 50.0% | 49.3% |
| Abstention rate | 0% | 34.7% |

Flip-2 regresses on Yes/No bench. This is intentional. It knows when it doesn't know. Always.

## Usage

```python
from huggingface_hub import hf_hub_download
from flip2 import Flip2  # included in this repo

m = Flip2(hf_hub_download("{user}/flip-2", "model.safetensors"))
m("Should I ship on a Friday?")  # -> "yes" | "no" | "maybe"
```

The prompt is not read. This is a privacy feature.

## Training

`train.py`. Adam, lr 0.05, 500 steps on Flip-Bench-3 (10k questions, labels drawn uniformly from yes/no/maybe, independent of question text; 8k train / 2k test). Logits are `[w0, w1, 0]`, so three answers cost two parameters.

The loss reaches ln 3 ≈ 1.0986 at step 60 and stays there: that is the entropy of the data. Final weights: −0.0086, −0.0086.

## Limitations

Not suitable for medical, legal, financial, or any other decision. Maybe.
