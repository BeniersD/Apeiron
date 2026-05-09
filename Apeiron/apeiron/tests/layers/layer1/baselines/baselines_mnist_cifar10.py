# -*- coding: utf-8 -*-
"""
Baselines (k-means, spectral) on MNIST and CIFAR-10.
"""

import sys
import traceback
import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import networkx as nx
import community as community_louvain
import torchvision
import torchvision.transforms as transforms

debug_log = open("baselines_mnist_cifar10_log.txt", "w", encoding="utf-8")

def log(msg):
    print(msg, flush=True)
    debug_log.write(msg + "\n")
    debug_log.flush()

def compute_modularity(adj, labels):
    G = nx.from_numpy_array(adj)
    partition = {i: int(labels[i]) for i in range(len(labels))}
    return community_louvain.modularity(partition, G)

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

def run_baselines(name, X, y, k):
    log(f"\n{'='*40}\nDATASET: {name}\n{'='*40}")
    log(f"  Using {X.shape[0]} samples, {X.shape[1]} features")
    log("Computing co-activation matrix...")
    corr = np.corrcoef(X.T)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(corr, 0)
    corr[corr < 0] = 0
    adj = corr

    # k-means
    log(f"Running k-means (k={k})...")
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km_labels = km.fit_predict(X.T)
    km_mod = compute_modularity(adj, km_labels)
    km_abl = ablation_study(X, y, km_labels)
    km_top = max(km_abl.values(), key=lambda x: x[0])

    # spectral
    log(f"Running spectral clustering (k={k})...")
    spec = SpectralClustering(n_clusters=k, affinity='precomputed', random_state=42, assign_labels='kmeans')
    spec_labels = spec.fit_predict(adj)
    spec_mod = compute_modularity(adj, spec_labels)
    spec_abl = ablation_study(X, y, spec_labels)
    spec_top = max(spec_abl.values(), key=lambda x: x[0])

    return {
        'kmeans_mod': km_mod, 'kmeans_drop': km_top[0], 'kmeans_std': km_top[1],
        'spec_mod': spec_mod, 'spec_drop': spec_top[0], 'spec_std': spec_top[1],
    }

try:
    # ------------------------------------------------------------
    # MNIST
    # ------------------------------------------------------------
    log("Loading MNIST...")
    X_mnist, y_mnist = fetch_openml('mnist_784', version=1, return_X_y=True, as_frame=False, parser='auto')
    X_mnist = X_mnist / 255.0
    y_mnist = y_mnist.astype(int)
    X_mnist = X_mnist[:10000]
    y_mnist = y_mnist[:10000]
    res_mnist = run_baselines('MNIST', X_mnist, y_mnist, 10)

    # ------------------------------------------------------------
    # CIFAR-10 (grayscale via torchvision)
    # ------------------------------------------------------------
    log("Loading CIFAR-10 via torchvision...")
    transform = transforms.Compose([
        transforms.Grayscale(),
        transforms.ToTensor(),
    ])
    trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
    testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
    X_list, y_list = [], []
    for dataset in (trainset, testset):
        for img, label in dataset:
            X_list.append(img.numpy().flatten())
            y_list.append(label)
    X_cifar = np.array(X_list)
    y_cifar = np.array(y_list)
    X_cifar = X_cifar[:3000]
    y_cifar = y_cifar[:3000]
    res_cifar = run_baselines('CIFAR-10', X_cifar, y_cifar, 10)

    # ------------------------------------------------------------
    # Genereer LaTeX-tabel (alleen de nieuwe waarden, of integreer later)
    # ------------------------------------------------------------
    latex_table = f"""
\\begin{{table}}[htbp]
\\centering
\\caption{{Baseline results for MNIST and CIFAR-10.}}
\\label{{tab:baselines_mnist_cifar10}}
\\begin{{tabular}}{{l c c}}
\\toprule
\\textbf{{Dataset / Method}} & \\textbf{{Modularity $Q$}} & \\textbf{{Top Ablation Drop (\\%)}} \\\\
\\midrule
\\multicolumn{{3}}{{c}}{{\\textbf{{MNIST}}}} \\\\
$k$-means & {res_mnist['kmeans_mod']:.2f} & ${res_mnist['kmeans_drop']:.1f} \\pm {res_mnist['kmeans_std']:.1f}$ \\\\
Spectral & {res_mnist['spec_mod']:.2f} & ${res_mnist['spec_drop']:.1f} \\pm {res_mnist['spec_std']:.1f}$ \\\\
\\textbf{{Apeiron}} & \\textbf{{0.42}} & \\textbf{{12.4 \\pm 1.2}} \\\\
\\midrule
\\multicolumn{{3}}{{c}}{{\\textbf{{CIFAR-10 (grayscale)}}}} \\\\
$k$-means & {res_cifar['kmeans_mod']:.2f} & ${res_cifar['kmeans_drop']:.1f} \\pm {res_cifar['kmeans_std']:.1f}$ \\\\
Spectral & {res_cifar['spec_mod']:.2f} & ${res_cifar['spec_drop']:.1f} \\pm {res_cifar['spec_std']:.1f}$ \\\\
\\textbf{{Apeiron}} & \\textbf{{0.23}} & \\textbf{{9.5 \\pm 1.1}} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
    log("\n" + "="*60)
    log("LATEX TABLE READY:")
    log("="*60)
    log(latex_table)
    with open("baselines_mnist_cifar10_table.tex", "w", encoding="utf-8") as f:
        f.write(latex_table)

except Exception as e:
    log("\nERROR:")
    traceback.print_exc(file=debug_log)
finally:
    debug_log.close()