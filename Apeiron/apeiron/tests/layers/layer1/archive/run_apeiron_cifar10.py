# -*- coding: utf-8 -*-
"""
Apeiron Layer 1-2-3 applied to CIFAR-10 (grayscale, 32x32).
Loads data via fetch_openml (no Keras required).
"""

import sys
import traceback
import numpy as np
import networkx as nx
import community as community_louvain
from sklearn.datasets import fetch_openml
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

debug_log = open("apeiron_cifar10_log.txt", "w", encoding="utf-8")

def log(msg):
    print(msg, flush=True)
    debug_log.write(msg + "\n")
    debug_log.flush()

log("=" * 60)
log("APEIRON ON CIFAR-10 (32x32 GRAYSCALE)")
log("=" * 60)

try:
    log("Step 1: Loading CIFAR-10 from local ARFF file...")
    from scipy.io.arff import loadarff
    import pandas as pd

    # Pad naar het ARFF-bestand in de cache
    arff_path = r"C:\Users\DIAG_LP\scikit_learn_data\openml\data\16797613\CIFAR_10.arff"
    data, meta = loadarff(arff_path)
    df = pd.DataFrame(data)

    # Alle kolommen behalve de laatste zijn pixelwaarden (bytes)
    X = df.iloc[:, :-1].values.astype(np.float32)
    y = df.iloc[:, -1].values
    # Converteer class labels naar integers
    y = pd.factorize(y)[0]

    log(f"  Loaded {X.shape[0]} samples, {X.shape[1]} features")
    # X is shape (60000, 3072): 32x32x3 kanaal
    X = X / 255.0
    y = y.astype(int)

    # Converteren naar grijswaarden: gemiddelde van de 3 kanalen per pixel
    # Reshape naar (n_samples, 32, 32, 3)
    X_reshaped = X.reshape(-1, 32, 32, 3)
    # Grijswaarden met standaard gewichten
    X_gray = np.dot(X_reshaped[..., :3], [0.2989, 0.5870, 0.1140])
    X_flat = X_gray.reshape(X_gray.shape[0], -1)

    # Subset voor snelheid
    n_samples = 3000
    X_flat = X_flat[:n_samples]
    y = y[:n_samples]
    n_features = X_flat.shape[1]
    log(f"  Dataset: {X_flat.shape[0]} samples, {n_features} features, {len(np.unique(y))} classes")

    log("Step 2: Computing co-activation matrix (correlation)...")
    corr = np.corrcoef(X_flat.T)
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
    apeiron_ablation = ablation_study(X_flat, y, cluster_labels, n_runs=3)
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