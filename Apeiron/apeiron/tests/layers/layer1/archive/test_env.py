# test_env.py
print("Testing imports...")
import numpy as np
import sklearn
import networkx as nx
import community as community_louvain
print("Imports OK")

print("Testing digits dataset...")
from sklearn.datasets import load_digits
digits = load_digits()
X = digits.data / 16.0
print(f"Data shape: {X.shape}")

print("Testing correlation matrix...")
corr = np.corrcoef(X.T)
print(f"Correlation shape: {corr.shape}")

print("Testing k-means...")
from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=10, n_init=10, random_state=42)
kmeans.fit_predict(X.T)
print("k-means OK")

print("All tests passed!")