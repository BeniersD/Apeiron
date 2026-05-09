# -*- coding: utf-8 -*-
"""
Apeiron Layer 1 Omega – Phase 1 (Optimized)
Gabor + CNN features met drastische dimensiereductie.
"""

import sys, traceback, numpy as np, networkx as nx, community as community_louvain
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import torch, torch.nn as nn, torch.nn.functional as F
from torchvision import datasets, transforms
from scipy.ndimage import convolve
import sys
from pathlib import Path

# Voeg de project-root (D:\GitHub\Apeiron\Apeiron) toe aan sys.path
# Het script staat in: apeiron/layers/layer01_foundational/tests/
# Dus 4x parent om bij de project-root te komen.
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apeiron.hardware import get_best_backend

debug_log = open("apeiron_omega_phase1_v2_log.txt", "w", encoding="utf-8")

def log(msg):
    print(msg, flush=True)
    debug_log.write(msg + "\n")
    debug_log.flush()

# ------------------------------------------------------------
# 1. Gabor filters (kleiner aantal features door sterkere pooling)
# ------------------------------------------------------------
def build_gabor_filters(kernel_size=15, n_orientations=8, n_frequencies=2):
    filters = []
    for freq_idx in range(n_frequencies):
        freq = 0.1 * (2 ** freq_idx)  # 0.1, 0.2
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
    log(f"Built {len(filters)} Gabor filters (size {kernel_size})")
    return filters

def apply_gabor_bank(image_batch, filters, pool_size=8):
    """Apply Gabor filters with strong pooling."""
    N, H, W = image_batch.shape
    features = []
    for img in image_batch:
        img_features = []
        for k in filters:
            filtered = convolve(img, k, mode='constant', cval=0.0)
            # Sterke pooling: gemiddelde over blokken van pool_size x pool_size
            h_pool, w_pool = H // pool_size, W // pool_size
            pooled = filtered.reshape(h_pool, pool_size, w_pool, pool_size).mean(axis=(1,3))
            img_features.append(pooled.flatten())
        features.append(np.concatenate(img_features))
    return np.array(features, dtype=np.float32)

# ------------------------------------------------------------
# 2. Random CNN features (veel kleiner)
# ------------------------------------------------------------
class RandomCNNFeatures(nn.Module):
    def __init__(self, in_channels=1, out_channels=32, kernel_size=5, target_spatial=4):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride=1, padding=kernel_size//2)
        for p in self.conv.parameters():
            p.requires_grad = False
        self.target_spatial = target_spatial

    def forward(self, x):
        x = torch.relu(self.conv(x))
        x = F.adaptive_avg_pool2d(x, (self.target_spatial, self.target_spatial))
        return x

# ------------------------------------------------------------
# 3. Helper om constante features te verwijderen
# ------------------------------------------------------------
def remove_constant_features(X, tol=1e-8):
    std = X.std(axis=0)
    mask = std > tol
    log(f"  Removed {np.sum(~mask)} constant features, {np.sum(mask)} remaining")
    return X[:, mask]

# ------------------------------------------------------------
# 4. Hoofdprogramma
# ------------------------------------------------------------
log("=" * 60)
log("APEIRON LAYER 1 OMEGA – PHASE 1 (OPTIMIZED)")
log("=" * 60)

try:
    log("Step 1: Loading CIFAR-10...")
    log("Detecting best hardware backend...")
    backend = get_best_backend()
    log(f"Using backend: {backend.name} - {backend.get_info()}")
    transform = transforms.Compose([transforms.Grayscale(), transforms.ToTensor()])
    trainset = datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
    testset = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)

    X_list, y_list = [], []
    for dataset in (trainset, testset):
        for img, label in dataset:
            X_list.append(img.numpy().squeeze())
            y_list.append(label)
    X_images = np.array(X_list, dtype=np.float32)
    y = np.array(y_list)

    n_samples = 3000
    X_images = X_images[:n_samples]
    y = y[:n_samples]
    log(f"  Loaded {n_samples} images, shape {X_images.shape}")

    # --- Gabor features (sterk gepooled) ---
    log("Step 2: Extracting Gabor features...")
    gabor_filters = build_gabor_filters(kernel_size=15, n_orientations=8, n_frequencies=2)  # 16 filters
    X_gabor = apply_gabor_bank(X_images, gabor_filters, pool_size=8)  # 32/8 = 4 → 4x4=16 waarden per filter
    log(f"  Gabor features shape: {X_gabor.shape}")  # (3000, 16*16=256)

    # --- CNN features (32 kanalen, 4x4 ruimtelijk) ---
    log("Step 3: Extracting Random CNN features...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    cnn_extractor = RandomCNNFeatures(in_channels=1, out_channels=32, kernel_size=5, target_spatial=4).to(device)
    X_tensor = torch.tensor(X_images).unsqueeze(1).to(device)
    with torch.no_grad():
        cnn_features = cnn_extractor(X_tensor)  # (N, 32, 4, 4)
    X_cnn = cnn_features.cpu().numpy().reshape(n_samples, -1)  # (3000, 512)
    log(f"  CNN features shape: {X_cnn.shape}")

    # --- Combineer en verwijder constante features ---
    X_combined = np.concatenate([X_gabor, X_cnn], axis=1)
    log(f"  Combined before cleanup: {X_combined.shape[1]} features")
    X_combined = remove_constant_features(X_combined)
    n_features = X_combined.shape[1]
    log(f"  Final feature count: {n_features}")

    # --- Correlatie met drempel (sparse) ---
    log("Step 4: Computing sparse co-activation matrix...")
    threshold = 0.2

    if backend.name == "CUDA":
        try:
            import torch
            X_tensor = torch.tensor(X_combined, device='cuda', dtype=torch.float32)
            corr = torch.corrcoef(X_tensor.T)
            corr = torch.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
            corr.fill_diagonal_(0)
            corr[corr < threshold] = 0
            adj_matrix = corr.cpu().numpy()
            log("  Used CUDA for correlation matrix.")
        except Exception as e:
            log(f"  CUDA failed ({e}), falling back to CPU.")
            corr = np.corrcoef(X_combined.T)
            corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
            np.fill_diagonal(corr, 0)
            corr[corr < threshold] = 0
            adj_matrix = corr
    else:
        corr = np.corrcoef(X_combined.T)
        corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
        np.fill_diagonal(corr, 0)
        corr[corr < threshold] = 0
        adj_matrix = corr

    log(f"  Adjacency matrix shape: {adj_matrix.shape}, sparsity: {100 * (adj_matrix == 0).mean():.2f}%")

    # --- Louvain clustering ---
    log("Step 5: Running Louvain community detection...")
    G = nx.from_numpy_array(adj_matrix)
    partition = community_louvain.best_partition(G, random_state=42)
    cluster_labels = np.array([partition[i] for i in range(n_features)])
    n_clusters = len(np.unique(cluster_labels))
    log(f"  Found {n_clusters} clusters")
    Q = community_louvain.modularity(partition, G)
    log(f"  Apeiron modularity Q = {Q:.4f}")

    # --- Ablatie (optioneel) ---
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
            result[c] = (np.mean(drops[c]) * 100, np.std(drops[c]) * 100)
        return result

    log("Step 6: Ablation study...")
    abl = ablation_study(X_combined, y, cluster_labels, n_runs=3)
    top_cluster = max(abl, key=lambda c: abl[c][0])
    top_drop, top_std = abl[top_cluster]
    log(f"  Top cluster ablation drop = {top_drop:.2f}% +/- {top_std:.2f}%")

    # --- Eindoordeel ---
    log("\n" + "=" * 60)
    log("PHASE 1 RESULTS")
    log("=" * 60)
    log(f"Modularity Q:   {Q:.4f}  (target > 0.40)")
    if Q > 0.40:
        log("✅ Phase 1 SUCCESS! Q > 0.40 achieved.")
    else:
        log("⚠️ Still below target. Consider further tuning (more samples, different pooling).")

except Exception as e:
    log("\n" + "!" * 60)
    log("ERROR:")
    traceback.print_exc(file=debug_log)
    traceback.print_exc(file=sys.stdout)
finally:
    debug_log.close()