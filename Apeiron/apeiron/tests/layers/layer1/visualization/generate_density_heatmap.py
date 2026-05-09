# generate_density_heatmap.py
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from datetime import datetime

# Tijdstempel voor unieke bestandsnaam
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Laad MNIST
X, y = fetch_openml('mnist_784', version=1, return_X_y=True, as_frame=False, parser='auto')
X = X / 255.0
y = y.astype(int)

# Kies een representatief cijfer (bijv. '8')
digit = 8
mask = (y == digit)
X_digit = X[mask][:500]  # subset voor snelheid

# Co-activatie matrix (correlatie)
corr = np.corrcoef(X_digit.T)
corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
np.fill_diagonal(corr, 0)
corr[corr < 0] = 0

# Maak een 28x28 heatmap van de gemiddelde invloed per pixel
influence = corr.mean(axis=1)  # gemiddelde connectiviteit per pixel
heatmap = influence.reshape(28, 28)

# Plot en opslaan met tijdstempel
plt.figure(figsize=(6, 5))
plt.imshow(heatmap, cmap='hot', interpolation='nearest')
plt.colorbar(label='Gemiddelde resonantie')
plt.title(f'DensityField heatmap for digit {digit}')
plt.tight_layout()

filename = f'density_heatmap_digit{digit}_{timestamp}.pdf'
plt.savefig(filename, bbox_inches='tight')
plt.close()
print(f"✅ Heatmap opgeslagen als: {filename}")