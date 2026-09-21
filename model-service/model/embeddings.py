"""
Embedding model for the pgvector cohort search in model/db.py. PCA fit on
the training population, reducing FEATURE_COLUMNS (10-dim) to EMBED_DIM.
Picked over a neural embedding for the same reason permutation importance
stood in for SHAP: simple and fast beats fancy under a deadline.
"""

import numpy as np
from sklearn.decomposition import PCA

EMBED_DIM = 8


class EmbeddingModel:
    def __init__(self, scaled_features: np.ndarray):
        n_components = min(EMBED_DIM, scaled_features.shape[1])
        self.pca = PCA(n_components=n_components, random_state=42)
        self.pca.fit(scaled_features)

    def embed(self, scaled_feature_row: np.ndarray) -> np.ndarray:
        return self.pca.transform(scaled_feature_row.reshape(1, -1))[0]

    def embed_batch(self, scaled_features: np.ndarray) -> np.ndarray:
        return self.pca.transform(scaled_features)
