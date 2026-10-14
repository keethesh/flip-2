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

Keethesh Labs' decision model. Sequel to Flip-1 by [@LambethEthan](https://x.com/LambethEthan).

- **2 parameters** (up 100% from Flip-1)
- **Now supports "maybe"**
- **Runs fully offline**

| Benchmark | Flip-1 | Flip-2 |
|---|---|---|
| Yes/No bench | 50% | 32.4% |
| Yes/No/Maybe bench (Flip-Bench-3) | n/a | **33.3%** |
| Accuracy when it commits to yes/no | 50% | 49.3% |
| Abstention rate | 0% | 34.7% |

Flip-2 regresses on Yes/No bench because "maybe" is always wrong there. We consider this a feature: it knows when it doesn't know (always).

## Usage

```python
from huggingface_hub import hf_hub_download
from flip2 import Flip2  # included in this repo

m = Flip2(hf_hub_download("{user}/flip-2", "model.safetensors"))
m("Should I ship on a Friday?")  # -> "yes" | "no" | "maybe"
```

The prompt is not read. This is a privacy feature.

## Training

`train.py`. 500 Adam steps on Flip-Bench-3 (10k questions, labels drawn uniformly from yes/no/maybe, independent of question text; 8k train / 2k test). Logits are `[w0, w1, 0]`, so three answers cost two parameters.

The loss goes to ln 3 ≈ 1.0986 and stays there, because that is the entropy of the data. The weights converge to ~0, so the answer distribution is ~uniform. Everything in the table above is measured on the held-out 2k, by sampling from the model (`results.json`, `loss.png`).

## Limitations

Does not help you decide. Not suitable for medical, legal, financial, or any other use. Maybe.
