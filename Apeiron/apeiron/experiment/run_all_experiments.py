#!/usr/bin/env python3
"""
run_all_experiments.py – Reproduceerbare vergelijking van Apeiron en baselines.
Genereert een LaTeX-tabel met modulariteit Q en top-cluster ablatiedaling voor:
- MNIST (10k subset)
- Fashion-MNIST (5k subset)
- Kuzushiji-MNIST (5k subset)
- CIFAR-10 (3k subset, grayscale)
- CIFAR-10 met Gabor+CNN features (Omega, 3k subset)

Evaluatie van non‑anthropocentriciteit:
Berekent de Normalised Mutual Information (NMI) tussen menselijke labels en
een sample‑clustering die is afgeleid van de door Apeiron ontdekte
feature‑clusters.  Een lagere NMI wijst op minder overeenkomst met
menselijke categorieën.
"""

import sys, os, time, json, traceback
import numpy as np
import networkx as nx
import community as community_louvain
from sklearn.datasets import fetch_openml, load_digits
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, normalized_mutual_info_score
import torch, torch.nn as nn, torch.nn.functional as F
from torchvision import datasets, transforms
from scipy.ndimage import convolve

# ------------------------------------------------------------
# 1. Verbind met Apeiron (zonder hardware voor snelheid)
# ------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
apeiron_dir = os.path.join(script_dir, '..', 'apeiron')   # root van de package
if os.path.exists(apeiron_dir):
    sys.path.insert(0, os.path.join(script_dir, '..'))
    from apeiron.layers.layer01_foundational.irreducible_unit import UltimateObservable, ObservabilityType
    from apeiron.layers.layer01_foundational.decomposition import is_atomic_by_operator
else:
    pass

# ------------------------------------------------------------
# 2. Parameters
# ------------------------------------------------------------
DATASETS = {
    'digits': {'type': 'sklearn', 'subset': None},
    'mnist': {'type': 'openml', 'id': 'mnist_784', 'subset': 10000},
    'fashion': {'type': 'openml', 'id': 'Fashion-MNIST', 'subset': 5000},
    'kmnist': {'type': 'openml', 'id': 'Kuzushiji-MNIST', 'subset': 5000},
    'cifar10_gray': {'type': 'torchvision', 'subset': 3000},
    'cifar10_omega': {'type': 'torchvision_omega', 'subset': 3000},
}

N_RUNS_ABLATION = 3
LOUVAIN_RANDOM_STATE = 42
os.environ["OMP_NUM_THREADS"] = "4"

# ------------------------------------------------------------
# 3. Hulpfuncties
# ------------------------------------------------------------
def load_data(name, cfg):
    if cfg['type'] == 'sklearn':
        digits = load_digits()
        X = digits.data / 16.0
        y = digits.target
        return X, y
    elif cfg['type'] == 'openml':
        X, y = fetch_openml(cfg['id'], version=1, return_X_y=True, as_frame=False, parser='auto')
        X = X / 255.0
        y = y.astype(int)
        if cfg['subset']:
            X = X[:cfg['subset']]
            y = y[:cfg['subset']]
        return X, y
    elif cfg['type'] in ('torchvision', 'torchvision_omega'):
        transform = transforms.Compose([transforms.Grayscale(), transforms.ToTensor()])
        trainset = datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
        testset = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
        X_list, y_list = [], []
        for ds in (trainset, testset):
            for img, label in ds:
                X_list.append(img.numpy().squeeze())
                y_list.append(label)
        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list)
        if cfg['subset']:
            X = X[:cfg['subset']]
            y = y[:cfg['subset']]
        if cfg['type'] == 'torchvision_omega':
            X = extract_omega_features(X)
        else:
            X = X.reshape(X.shape[0], -1)
        return X, y

def extract_omega_features(images):
    def build_gabor_filters(kernel_size=15, n_orientations=8, n_frequencies=2):
        filters = []
        for freq_idx in range(n_frequencies):
            freq = 0.1 * (2 ** freq_idx)
            for theta in np.linspace(0, np.pi, n_orientations, endpoint=False):
                sigma = kernel_size / 4.0
                gamma, psi, lambd = 1.0, 0.0, 1.0 / freq
                kernel = np.zeros((kernel_size, kernel_size), dtype=np.float32)
                for y in range(kernel_size):
                    for x in range(kernel_size):
                        x_theta = (x - kernel_size//2) * np.cos(theta) + (y - kernel_size//2) * np.sin(theta)
                        y_theta = -(x - kernel_size//2) * np.sin(theta) + (y - kernel_size//2) * np.cos(theta)
                        gauss = np.exp(-(x_theta**2 + gamma**2 * y_theta**2) / (2 * sigma**2))
                        sinusoid = np.cos(2 * np.pi * x_theta / lambd + psi)
                        kernel[y, x] = gauss * sinusoid
                kernel -= kernel.mean()
                norm = np.linalg.norm(kernel)
                if norm > 1e-8:
                    kernel /= norm
                filters.append(kernel)
        return filters
    gabor_filters = build_gabor_filters(15, 8, 2)
    N, H, W = images.shape
    gabor_feats = []
    for img in images:
        feats = []
        for k in gabor_filters:
            filtered = convolve(img, k, mode='constant', cval=0.0)
            pooled = filtered.reshape(8, 4, 8, 4).mean(axis=(1,3))
            feats.append(pooled.flatten())
        gabor_feats.append(np.concatenate(feats))
    X_gabor = np.array(gabor_feats, dtype=np.float32)
    class RandCNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = nn.Conv2d(1, 32, 5, padding=2)
            for p in self.conv.parameters():
                p.requires_grad = False
        def forward(self, x):
            x = torch.relu(self.conv(x))
            x = F.adaptive_avg_pool2d(x, (4, 4))
            return x
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    cnn = RandCNN().to(device)
    X_tensor = torch.tensor(images).unsqueeze(1).to(device)
    with torch.no_grad():
        cnn_feats = cnn(X_tensor).cpu().numpy().reshape(N, -1)
    X_combined = np.concatenate([X_gabor, cnn_feats], axis=1)
    std = X_combined.std(axis=0)
    mask = std > 1e-8
    X_combined = X_combined[:, mask]
    return X_combined

def compute_modularity(adj, labels):
    G = nx.from_numpy_array(adj)
    partition = {i: int(labels[i]) for i in range(len(labels))}
    return community_louvain.modularity(partition, G)

def ablation_study(X, y, cluster_labels, n_runs=N_RUNS_ABLATION):
    n_clusters = len(np.unique(cluster_labels))
    drops = {c: [] for c in range(n_clusters)}
    for run in range(n_runs):
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=None
        )
        clf = LogisticRegression(max_iter=1000)
        clf.fit(X_train, y_train)
        baseline_acc = accuracy_score(y_test, clf.predict(X_test))
        for c in range(n_clusters):
            mask = (cluster_labels == c)
            X_test_abl = X_test.copy()
            X_test_abl[:, mask] = 0.0
            acc = accuracy_score(y_test, clf.predict(X_test_abl))
            drops[c].append(baseline_acc - acc)
    result = {}
    for c in range(n_clusters):
        result[c] = (np.mean(drops[c]) * 100, np.std(drops[c]) * 100)
    return result

def run_method(X, y, method='kmeans', k=10):
    corr = np.corrcoef(X.T)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(corr, 0)
    corr[corr < 0] = 0
    adj = corr
    if method == 'kmeans':
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X.T)
    elif method == 'spectral':
        labels = SpectralClustering(n_clusters=k, affinity='precomputed', random_state=42, assign_labels='kmeans').fit_predict(adj)
    elif method == 'apeiron':
        G = nx.from_numpy_array(adj)
        partition = community_louvain.best_partition(G, random_state=LOUVAIN_RANDOM_STATE)
        labels = np.array([partition[i] for i in range(X.shape[1])])
    else:
        raise ValueError("Onbekende methode")
    mod = compute_modularity(adj, labels)
    abl = ablation_study(X, y, labels)
    top_cluster = max(abl, key=lambda c: abl[c][0])
    top_drop, top_std = abl[top_cluster]
    return mod, top_drop, top_std, labels


def evaluate_sample_clusters(X, feature_labels, y, k=None):
    """
    Bouwt een sample-representatie op basis van de feature-clusters en
    clustert de samples.  Retourneert de genormaliseerde mutual information
    (NMI) met de menselijke labels.
    """
    # X : (n_samples, n_features)
    # feature_labels : (n_features,)   – clusterindeling van de features
    n_clusters_f = len(np.unique(feature_labels))
    if n_clusters_f == 1:
        # Slechts één cluster is onbetekenend; NMI niet zinvol
        return 0.0
    if k is None:
        k = len(np.unique(y))          # zelfde aantal als menselijke klassen

    # Maak per sample een vector met per cluster de gemiddelde intensiteit
    sample_repr = np.zeros((X.shape[0], n_clusters_f))
    for c in range(n_clusters_f):
        mask = (feature_labels == c)
        sample_repr[:, c] = X[:, mask].mean(axis=1)

    # Cluster de samples
    sample_labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(sample_repr)
    return normalized_mutual_info_score(y, sample_labels)


# ------------------------------------------------------------
# 4. Hoofdprogramma
# ------------------------------------------------------------
def main():
    results = {}
    nmi_lines = []   # voor nmi_results.txt
    for name, cfg in DATASETS.items():
        print(f"=== {name} ===")
        X, y = load_data(name, cfg)
        print(f"  Data: {X.shape}")
        # Apeiron
        try:
            ape_mod, ape_drop, ape_std, ape_labels = run_method(X, y, method='apeiron')
            ape_nmi = evaluate_sample_clusters(X, ape_labels, y)
        except Exception as e:
            print(f"  [!] Apeiron mislukt: {e}")
            ape_mod = ape_drop = ape_std = ape_labels = ape_nmi = None
        # Baselines (alleen voor datasets zonder Omega)
        if 'omega' not in name:
            try:
                km_mod, km_drop, km_std, km_labels = run_method(X, y, method='kmeans')
                km_nmi = evaluate_sample_clusters(X, km_labels, y)
            except Exception as e:
                print(f"  [!] k-means mislukt: {e}")
                km_mod = km_drop = km_std = km_labels = km_nmi = None
            try:
                sp_mod, sp_drop, sp_std, sp_labels = run_method(X, y, method='spectral')
                sp_nmi = evaluate_sample_clusters(X, sp_labels, y)
            except Exception as e:
                print(f"  [!] Spectral mislukt: {e}")
                sp_mod = sp_drop = sp_std = sp_labels = sp_nmi = None
        else:
            km_mod = km_drop = km_std = km_labels = km_nmi = None
            sp_mod = sp_drop = sp_std = sp_labels = sp_nmi = None

        # NMI-regels opslaan en tonen
        for meth, nmi_val in [("Apeiron", ape_nmi), ("k-means", km_nmi), ("Spectral", sp_nmi)]:
            if nmi_val is not None:
                line = f"{name}: {meth} NMI = {nmi_val:.3f}"
            else:
                line = f"{name}: {meth} NMI = N/A"
            print("  " + line)
            nmi_lines.append(line)

        results[name] = {
            'kmeans': (km_mod, km_drop, km_std) if km_mod is not None else (None, None, None),
            'spectral': (sp_mod, sp_drop, sp_std) if sp_mod is not None else (None, None, None),
            'apeiron': (ape_mod, ape_drop, ape_std) if ape_mod is not None else (None, None, None),
        }

    # NMI naar bestand
    with open('nmi_results.txt', 'w') as f:
        f.write("Normalised Mutual Information (NMI) tussen menselijke labels\n")
        f.write("en sample-clustering afgeleid uit feature-clusters.\n\n")
        f.write("\n".join(nmi_lines))
    print("✅ NMI-waarden opgeslagen in nmi_results.txt")

    # LaTeX-tabel (ongewijzigd)
    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{Clustering performance across datasets. Modularity $Q$ and top cluster ablation drop (\%).}")
    lines.append(r"\label{tab:all_experiments}")
    lines.append(r"\begin{tabular}{l c c c}")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Dataset} & \textbf{Method} & \textbf{Modularity $Q$} & \textbf{Top Ablation Drop (\%)} \\")
    lines.append(r"\midrule")
    for name in DATASETS:
        res = results[name]
        if res['kmeans'][0] is not None:
            lines.append(f"{name} & k-means & {res['kmeans'][0]:.2f} & ${res['kmeans'][1]:.1f} \\pm {res['kmeans'][2]:.1f}$ \\\\")
            lines.append(f"{name} & Spectral & {res['spectral'][0]:.2f} & ${res['spectral'][1]:.1f} \\pm {res['spectral'][2]:.1f}$ \\\\")
        if res['apeiron'][0] is not None:
            lines.append(f"{name} & Apeiron & {res['apeiron'][0]:.2f} & ${res['apeiron'][1]:.1f} \\pm {res['apeiron'][2]:.1f}$ \\\\")
        lines.append(r"\midrule" if name != list(DATASETS.keys())[-1] else r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    out_dir = "tables"
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "all_experiments.tex"), "w") as f:
        f.write("\n".join(lines))
    print("✅ Tabellen gegenereerd in tables/all_experiments.tex")

if __name__ == "__main__":
    main()