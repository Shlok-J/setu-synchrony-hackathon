"""
A learned embedding model for pgvector-based cohort similarity search
(see model/db.py). PCA fit on the training population's standardized
features, reducing FEATURE_COLUMNS (10-dim) to EMBED_DIM.

Chosen over a neural embedding (autoencoder/contrastive) for the same
reason permutation importance stood in for SHAP in explain.py: a simple,
fast, well-understood technique wins over a more sophisticated one when
correctness and time matter more than novelty under a deadline. A learned
neural embedding is the natural production upgrade path -- see DESIGN.md.
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
