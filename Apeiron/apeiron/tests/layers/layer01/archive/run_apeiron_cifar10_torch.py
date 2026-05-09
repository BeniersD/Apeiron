# -*- coding: utf-8 -*-
"""
Apeiron on CIFAR-10 (grayscale) using torchvision.
"""

import sys
import traceback
import numpy as np
import networkx as nx
import community as community_louvain
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

try:
    import torchvision
    import torchvision.transforms as transforms
except ImportError:
    raise ImportError("PyTorch and torchvision are required. Install with: pip install torch torchvision")

debug_log = open("apeiron_cifar10_log.txt", "w", encoding="utf-8")

def log(msg):
    print(msg, flush=True)
    debug_log.write(msg + "\n")
    debug_log.flush()

log("=" * 60)
log("APEIRON ON CIFAR-10 (TORCHVISION, GRAYSCALE)")
log("=" * 60)

try:
    log("Step 1: Loading CIFAR-10 via torchvision...")
    transform = transforms.Compose([
        transforms.Grayscale(),
        transforms.ToTensor(),
    ])
    trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
    testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
    
    # Combineer train en test
    X_list, y_list = [], []
    for dataset in (trainset, testset):
        for img, label in dataset:
            X_list.append(img.numpy().flatten())
            y_list.append(label)
    X = np.array(X_list)
    y = np.array(y_list)
    
    n_samples = 3000
    X = X[:n_samples]
    y = y[:n_samples]
    n_features = X.shape[1]
    log(f"  Dataset: {X.shape[0]} samples, {n_features} features, {len(np.unique(y))} classes")

    log("Step 2: Computing co-activation matrix (correlation)...")
    corr = np.corrcoef(X.T)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(corr, 0)
    corr[corr < 0] = 0
    adj_matrix = corr
    log(f"  Adjacency matrix shape: {adj_matrix.shape}")

    log("Step 3: Running Louvain community detection...")
    G = nx.from_numpy_array(adj_matrix)
    partition = community_louvain.best_partition(G, random_state=42)
    cluster_labels = np.array([partition[i] for i in range(n_features)])
    n_clusters = len(np.unique(cluster_labels))
    log(f"  Found {n_clusters} clusters")

    apeiron_mod = community_louvain.modularity(partition, G)
    log(f"  Apeiron modularity Q = {apeiron_mod:.4f}")

    def ablation_study(X, y, cluster_labels, n_runs=3):
        n_clusters = len(np.unique(cluster_labels))
        drops = {c: [] for c in range(n_clusters)}
        for run in range(n_runs):
            log(f"    Ablation run {run+1}/{n_runs}...")
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, stratify=y, random_state=None
            )
            clf = LogisticRegression(max_iter=1000)
            clf.fit(X_train, y_train)
            baseline_acc = accuracy_score(y_test, clf.predict(X_test))
            for c in range(n_clusters):
                mask = (cluster_labels == c)
                X_test_ablated = X_test.copy()
                X_test_ablated[:, mask] = 0.0
                acc_ablated = accuracy_score(y_test, clf.predict(X_test_ablated))
                drops[c].append(baseline_acc - acc_ablated)
        result = {}
        for c in range(n_clusters):
            mean_drop = np.mean(drops[c]) * 100
            std_drop = np.std(drops[c]) * 100
            result[c] = (mean_drop, std_drop)
        return result

    log("Step 4: Apeiron ablation study...")
    apeiron_ablation = ablation_study(X, y, cluster_labels, n_runs=3)
    top_cluster_ap = max(apeiron_ablation, key=lambda c: apeiron_ablation[c][0])
    apeiron_top_drop, apeiron_top_std = apeiron_ablation[top_cluster_ap]
    log(f"  Top cluster ablation drop = {apeiron_top_drop:.2f}% +/- {apeiron_top_std:.2f}%")

    latex_table = f"""
\\begin{{table}}[htbp]
\\centering
\\caption{{Apeiron performance on CIFAR-10 (grayscale, subset of {n_samples} samples).}}
\\label{{tab:apeiron_cifar10}}
\\begin{{tabular}}{{l c c}}
\\toprule
\\textbf{{Method}} & \\textbf{{Modularity $Q$}} & \\textbf{{Top Cluster Ablation Drop (\\%)}} \\\\
\\midrule
\\textbf{{Apeiron}} & \\textbf{{{apeiron_mod:.2f}}} & \\textbf{{{apeiron_top_drop:.1f} \\pm {apeiron_top_std:.1f}}} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
    log("\n" + "=" * 60)
    log("LATEX TABLE READY:")
    log("=" * 60)
    log(latex_table)

    with open("apeiron_cifar10_table.tex", "w", encoding="utf-8") as f:
        f.write(latex_table)
    log("Table written to apeiron_cifar10_table.tex")

except Exception as e:
    log("\n" + "!" * 60)
    log("ERROR OCCURRED:")
    log("!" * 60)
    traceback.print_exc(file=debug_log)
    traceback.print_exc(file=sys.stdout)

finally:
    log("\nScript finished.")
    debug_log.close()