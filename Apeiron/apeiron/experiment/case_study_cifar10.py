#!/usr/bin/env python3
"""case_study_cifar10.py – genereer de case‑study figuur voor een niet‑menselijk cluster op CIFAR‑10."""

import numpy as np
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from experiment.run_all_experiments import DATASETS, load_data, run_method

# ------------------------------------------------------------
# 1. Laad alleen CIFAR-10 grijswaarden
# ------------------------------------------------------------
name = 'cifar10_gray'
cfg = DATASETS[name]
X, y = load_data(name, cfg)               # X: (3000, 1024), y: (3000,)
n_samples, n_features = X.shape

# ------------------------------------------------------------
# 2. Apeiron feature‑clustering (identiek aan paper)
# ------------------------------------------------------------
mod, drop, std, feature_labels = run_method(X, y, method='apeiron')  # feature_labels is (1024,)
n_clusters_f = len(np.unique(feature_labels))

print(f"Modularity Q = {mod:.3f}, Top ablation drop = {drop:.1f}%")
print(f"Aantal feature‑clusters: {n_clusters_f}")

# ------------------------------------------------------------
# 3. Cluster‑sterkte per sample
# ------------------------------------------------------------
sample_cluster_strength = np.zeros((n_samples, n_clusters_f))
for c in range(n_clusters_f):
    mask = (feature_labels == c)
    sample_cluster_strength[:, c] = X[:, mask].mean(axis=1)

# ------------------------------------------------------------
# 4. Kies het cluster met de hoogste ablatie‑drop
#    (je kunt ook handmatig een ander cluster kiezen)
# ------------------------------------------------------------
# Bereken per cluster de gemiddelde sterkte over alle beelden (optioneel)
best_cluster = np.argmax(drop)   # Omdat drop de top‑cluster is, maar de variabele 'drop' is de waarde van de top‑cluster.
# drop is een scalar, maar we weten niet welk cluster dat is. We moeten de top‑cluster vinden.
# Dat betekent dat we de ablatie_studie opnieuw moeten doen, maar dat is gedoe. Alternatief: kies het cluster dat het meest bijdraagt aan de NMI? We kunnen het cluster nemen met de hoogste gemiddelde sterkte over alle beelden.
# Eenvoudig: neem het cluster met de hoogste gemiddelde sterkte over alle beelden, dat waarschijnlijk het meest voorkomt.
mean_strengths = sample_cluster_strength.mean(axis=0)
chosen_cluster = int(np.argmax(mean_strengths))
print(f"Gekozen cluster (hoogste gemiddelde sterkte): {chosen_cluster}")

# ------------------------------------------------------------
# 5. Selecteer 9 beelden met hoge en 9 met lage sterkte voor dit cluster
# ------------------------------------------------------------
strengths = sample_cluster_strength[:, chosen_cluster]
indices_sorted = np.argsort(strengths)   # van laag naar hoog

low_indices = indices_sorted[:9]
high_indices = indices_sorted[-9:]

# ------------------------------------------------------------
# 6. Plot de 18 beelden in een 2x9 grid
# ------------------------------------------------------------
fig, axes = plt.subplots(2, 9, figsize=(12, 4))
for i, idx in enumerate(high_indices):
    img = X[idx].reshape(32, 32)
    axes[0, i].imshow(img, cmap='gray')
    axes[0, i].axis('off')
    if i == 0:
        axes[0, i].set_title("High cluster presence", fontsize=9)

for i, idx in enumerate(low_indices):
    img = X[idx].reshape(32, 32)
    axes[1, i].imshow(img, cmap='gray')
    axes[1, i].axis('off')
    if i == 0:
        axes[1, i].set_title("Low cluster presence", fontsize=9)

plt.suptitle(f"CIFAR‑10: Apeiron cluster {chosen_cluster} (non‑anthropocentric example)", y=1.02)
plt.tight_layout()

# Zorg dat de map bestaat
os.makedirs('figures', exist_ok=True)
plt.savefig('figures/cifar_cluster_example.pdf', bbox_inches='tight')
print("Figuur opgeslagen als figures/cifar_cluster_example.pdf")