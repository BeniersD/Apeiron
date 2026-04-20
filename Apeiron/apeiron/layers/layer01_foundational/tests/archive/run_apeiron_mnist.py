from sklearn.metrics import normalized_mutual_info_score

# Stel: cluster_labels is een array van lengte 784 met cluster-ID's per pixel
# We maken een proxy ground truth door pixels te clusteren met k-means op de gemiddelde plaatjes per digit
from sklearn.cluster import KMeans

# Bereken gemiddeld plaatje per digit (0-9)
mean_images = []
for d in range(10):
    mean_images.append(X_train[y_train == d].mean(axis=0))
mean_images = np.array(mean_images)  # shape (10, 784)

# Cluster de pixels op basis van hun waarden over de 10 gemiddelde digits
# (transpose: 784 pixels, elk met 10 features)
kmeans_pixels = KMeans(n_clusters=10, random_state=42)
ground_truth_labels = kmeans_pixels.fit_predict(mean_images.T)

nmi = normalized_mutual_info_score(ground_truth_labels, cluster_labels)