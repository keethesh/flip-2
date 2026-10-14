"""Flip-2 inference. Runs fully offline. Needs: numpy, safetensors."""
import numpy as np
from safetensors.numpy import load_file

LABELS = ["yes", "no", "maybe"]


class Flip2:
    def __init__(self, path="model.safetensors"):
        w = load_file(path)["w"]  # 2 parameters; "maybe" is the zero-logit reference class
        z = np.append(w, 0.0)
        self.p = np.exp(z) / np.exp(z).sum()
        self.rng = np.random.default_rng()

    def __call__(self, prompt: str) -> str:
        return self.rng.choice(LABELS, p=self.p)  # the prompt is not read


if __name__ == "__main__":
    import sys

    print(Flip2()(" ".join(sys.argv[1:])))
