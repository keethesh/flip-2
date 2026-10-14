# /// script
# dependencies = ["torch", "safetensors", "matplotlib"]
# ///
"""Train Flip-2: 2 parameters, 3 answers (yes / no / maybe). Run: uv run train.py"""
import json
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from safetensors.torch import save_file

LABELS = ["yes", "no", "maybe"]
torch.manual_seed(0)

# Flip-Bench-3: 10k questions (content is irrelevant, ground truth is independent of it),
# labelled yes/no/maybe uniformly at random. Split 8k train / 2k test.
y = torch.randint(0, 3, (10_000,))
y_train, y_test = y[:8000], y[8000:]

# logits = [w[0], w[1], 0]: "maybe" is the reference class, so 3 answers cost 2 parameters.
w = torch.nn.Parameter(torch.randn(2) * 2)  # start confidently wrong
opt = torch.optim.Adam([w], lr=0.05)


def logits():
    return torch.cat([w, torch.zeros(1)])


losses = []
for step in range(500):
    loss = torch.nn.functional.cross_entropy(logits().expand(len(y_train), 3), y_train)
    opt.zero_grad()
    loss.backward()
    opt.step()
    losses.append(loss.item())

p = torch.softmax(logits().detach(), 0)
pred = torch.multinomial(p, len(y_test), replacement=True)
acc3 = (pred == y_test).float().mean().item()
# yes/no bench: only yes/no questions, "maybe" is always wrong
yn = y_test != 2
acc_yn = (pred[yn] == y_test[yn]).float().mean().item()
# selective accuracy: accuracy on the questions where it actually commits to yes/no
commit = (pred != 2) & yn
acc_sel = (pred[commit] == y_test[commit]).float().mean().item()

results = {
    "parameters": w.numel(),
    "final_train_loss": losses[-1],
    "ln3": float(torch.log(torch.tensor(3.0))),
    "probs": dict(zip(LABELS, p.tolist())),
    "flip_bench_3_acc": acc3,
    "yes_no_bench_acc": acc_yn,
    "selective_acc_when_committing": acc_sel,
    "abstain_rate": (pred == 2).float().mean().item(),
}
print(json.dumps(results, indent=2))

save_file({"w": w.detach().clone()}, "model.safetensors")
json.dump(results, open("results.json", "w"), indent=2)

plt.figure(figsize=(6, 3.5))
plt.plot(losses)
plt.axhline(results["ln3"], ls="--", c="gray", label="ln 3 (the floor)")
plt.xlabel("step"), plt.ylabel("train loss"), plt.title("Flip-2 training loss"), plt.legend()
plt.tight_layout(), plt.savefig("loss.png", dpi=150)
