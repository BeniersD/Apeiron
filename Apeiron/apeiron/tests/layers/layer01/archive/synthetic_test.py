import numpy as np
import networkx as nx
import community as community_louvain

# Genereer twee klassen: pixels 0-31 actief in klasse 0, pixels 32-63 actief in klasse 1
n_samples = 200
X = np.zeros((n_samples, 64))
X[:100, :32] = np.random.rand(100, 32) > 0.5   # klasse 0
X[100:, 32:] = np.random.rand(100, 32) > 0.5  # klasse 1
y = np.array([0]*100 + [1]*100)

# Correlatiematrix
corr = np.corrcoef(X.T)
corr = np.nan_to_num(corr, 0)
np.fill_diagonal(corr, 0)
corr[corr < 0] = 0

G = nx.from_numpy_array(corr)
partition = community_louvain.best_partition(G, random_state=42)
labels = np.array([partition[i] for i in range(64)])

# Ideale clustering: twee groepen pixels
print(f"Gevonden clusters: {len(np.unique(labels))}")
print("Cluster 0 pixels:", np.where(labels == 0)[0])
print("Cluster 1 pixels:", np.where(labels == 1)[0])