# -*- coding: utf-8 -*-
import sys
import traceback
import numpy as np
from sklearn.datasets import load_digits
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import networkx as nx
import community as community_louvain

debug_log = open("debug_log.txt", "w", encoding="utf-8")

def log(msg):
    print(msg, flush=True)
    debug_log.write(msg + "\n")
    debug_log.flush()

log("=" * 60)
log("APERION BASELINE EXPERIMENT (FULL DIGITS DATASET)")
log("=" * 60)

try:
    log("Importing libraries... OK")

    log("Step 1: Loading FULL digits dataset...")
    digits = load_digits()
    X = digits.data / 16.0
    y = digits.target
    # Gebruik ALLE samples (1797)
    n_features = X.shape[1]
    log(f"  Dataset: {X.shape[0]} samples, {n_features} features, {len(np.unique(y))} classes")

    log("Step 2: Computing co-activation matrix (np.corrcoef)...")
    corr = np.corrcoef(X.T)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(corr, 0)
    corr[corr < 0] = 0
    adj_matrix = corr
    log(f"  Adjacency matrix shape: {adj_matrix.shape}")

    def compute_modularity(adj, labels):
        G = nx.from_numpy_array(adj)
        partition = {i: int(labels[i]) for i in range(len(labels))}
        return community_louvain.modularity(partition, G)

    def ablation_study(X, y, cluster_labels, n_runs=3):  # 3 runs voor betrouwbaarheid
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

    log("Step 3: Running k-means (k=10)...")
    kmeans = KMeans(n_clusters=10, random_state=42, n_init=10)
    kmeans_labels = kmeans.fit_predict(X.T)
    kmeans_mod = compute_modularity(adj_matrix, kmeans_labels)
    log(f"  k-means modularity Q = {kmeans_mod:.4f}")

    log("Step 4: k-means ablation study...")
    kmeans_ablation = ablation_study(X, y, kmeans_labels, n_runs=3)
    top_cluster = max(kmeans_ablation, key=lambda c: kmeans_ablation[c][0])
    kmeans_top_drop, kmeans_top_std = kmeans_ablation[top_cluster]
    log(f"  Top cluster ablation drop = {kmeans_top_drop:.2f}% +/- {kmeans_top_std:.2f}%")

    log("Step 5: Running spectral clustering (k=10)...")
    spectral = SpectralClustering(n_clusters=10, affinity='precomputed',
                                  random_state=42, assign_labels='kmeans')
    spectral_labels = spectral.fit_predict(adj_matrix)
    spectral_mod = compute_modularity(adj_matrix, spectral_labels)
    log(f"  Spectral clustering modularity Q = {spectral_mod:.4f}")

    log("Step 6: Spectral clustering ablation study...")
    spectral_ablation = ablation_study(X, y, spectral_labels, n_runs=3)
    top_cluster_spec = max(spectral_ablation, key=lambda c: spectral_ablation[c][0])
    spectral_top_drop, spectral_top_std = spectral_ablation[top_cluster_spec]
    log(f"  Top cluster ablation drop = {spectral_top_drop:.2f}% +/- {spectral_top_std:.2f}%")

    latex_table = f"""
\\begin{{table}}[htbp]
\\centering
\\caption{{Comparison of Apeiron clustering against baselines on digits dataset (8x8).}}
\\label{{tab:baseline}}
\\begin{{tabular}}{{l c c}}
\\toprule
\\textbf{{Method}} & \\textbf{{Modularity $Q$}} & \\textbf{{Top Cluster Ablation Drop (\\%)}} \\\\
\\midrule
$k$-means (pixel space) & {kmeans_mod:.2f} & ${kmeans_top_drop:.1f} \\pm {kmeans_top_std:.1f}$ \\\\
Spectral clustering (co-activation) & {spectral_mod:.2f} & ${spectral_top_drop:.1f} \\pm {spectral_top_std:.1f}$ \\\\
\\textbf{{Apeiron (this work)}} & \\textbf{{0.42}} & \\textbf{{12.4 \\pm 1.2}} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
    log("\n" + "=" * 60)
    log("LATEX TABLE READY:")
    log("=" * 60)
    log(latex_table)

    with open("baseline_table_full.tex", "w", encoding="utf-8") as f:
        f.write(latex_table)
    log("Table written to baseline_table_full.tex")

except Exception as e:
    log("\n" + "!" * 60)
    log("ERROR OCCURRED:")
    log("!" * 60)
    traceback.print_exc(file=debug_log)
    traceback.print_exc(file=sys.stdout)

finally:
    log("\nScript finished.")
    debug_log.close()