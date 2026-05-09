# -*- coding: utf-8 -*-
"""
Apeiron Layer 1-2-3 toegepast op de digits dataset (8x8).
Eerlijke vergelijking met k-means en spectral clustering.
"""

import sys
import traceback
import numpy as np
import networkx as nx
import community as community_louvain
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
debug_log = open("apeiron_digits_log.txt", "w", encoding="utf-8")

def log(msg):
    print(msg, flush=True)
    debug_log.write(msg + "\n")
    debug_log.flush()

log("=" * 60)
log("APEIRON ON DIGITS DATASET (8x8)")
log("=" * 60)

try:
    # ------------------------------------------------------------
    # 1. Laad digits dataset
    # ------------------------------------------------------------
    log("Step 1: Loading digits dataset...")
    digits = load_digits()
    X = digits.data / 16.0       # 1797 samples, 64 features
    y = digits.target
    n_samples, n_features = X.shape
    log(f"  Dataset: {n_samples} samples, {n_features} features, {len(np.unique(y))} classes")

    # ------------------------------------------------------------
    # 2. Co-activatie matrix (identiek aan Layer 2 hypergraph)
    # ------------------------------------------------------------
    log("Step 2: Computing co-activation matrix (correlation)...")
    corr = np.corrcoef(X.T)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(corr, 0)
    corr[corr < 0] = 0
    adj_matrix = corr
    log(f"  Adjacency matrix shape: {adj_matrix.shape}")

    # ------------------------------------------------------------
    # 3. Louvain clustering (Layer 3)
    # ------------------------------------------------------------
    log("Step 3: Running Louvain community detection...")
    G = nx.from_numpy_array(adj_matrix)
    partition = community_louvain.best_partition(G, random_state=42)
    # Converteer naar array van labels
    cluster_labels = np.array([partition[i] for i in range(n_features)])
    n_clusters = len(np.unique(cluster_labels))
    log(f"  Found {n_clusters} clusters")

    # Modulariteit berekenen
    apeiron_mod = community_louvain.modularity(partition, G)
    log(f"  Apeiron modularity Q = {apeiron_mod:.4f}")

    # ------------------------------------------------------------
    # 4. Ablatiestudie (identiek aan baseline script)
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # 5. Resultaten van eerdere baselines (hardcoded uit volledige run)
    # ------------------------------------------------------------
    kmeans_mod = 0.1657
    kmeans_top_drop = 13.61
    kmeans_top_std = 0.60

    spectral_mod = 0.3901
    spectral_top_drop = 42.87
    spectral_top_std = 2.23

    # ------------------------------------------------------------
    # 6. Genereer eerlijke LaTeX-tabel
    # ------------------------------------------------------------
    latex_table = f"""
\\begin{{table}}[htbp]
\\centering
\\caption{{Comparison of clustering methods on the digits dataset (8x8, 1797 samples).}}
\\label{{tab:comparison_digits}}
\\begin{{tabular}}{{l c c}}
\\toprule
\\textbf{{Method}} & \\textbf{{Modularity $Q$}} & \\textbf{{Top Cluster Ablation Drop (\\%)}} \\\\
\\midrule
$k$-means (pixel space) & {kmeans_mod:.2f} & ${kmeans_top_drop:.1f} \\pm {kmeans_top_std:.1f}$ \\\\
Spectral clustering (co-activation) & {spectral_mod:.2f} & ${spectral_top_drop:.1f} \\pm {spectral_top_std:.1f}$ \\\\
\\textbf{{Apeiron (this work)}} & \\textbf{{{apeiron_mod:.2f}}} & \\textbf{{{apeiron_top_drop:.1f} \\pm {apeiron_top_std:.1f}}} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
    log("\n" + "=" * 60)
    log("LATEX TABLE READY (FAIR COMPARISON):")
    log("=" * 60)
    log(latex_table)

    with open("comparison_table_digits.tex", "w", encoding="utf-8") as f:
        f.write(latex_table)
    log("Table written to comparison_table_digits.tex")

except Exception as e:
    log("\n" + "!" * 60)
    log("ERROR OCCURRED:")
    log("!" * 60)
    traceback.print_exc(file=debug_log)
    traceback.print_exc(file=sys.stdout)

finally:
    log("\nScript finished.")
    debug_log.close()