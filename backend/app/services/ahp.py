import numpy as np


# Random Index theo Saaty
RI_TABLE = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}


def build_pairwise_matrix(criteria_ids, pairwise_items):
    n = len(criteria_ids)
    index_map = {criterion_id: idx for idx, criterion_id in enumerate(criteria_ids)}

    matrix = np.ones((n, n), dtype=float)

    for item in pairwise_items:
        c1 = item["criterion_1_id"]
        c2 = item["criterion_2_id"]
        value = float(item["comparison_value"])

        i = index_map[c1]
        j = index_map[c2]

        matrix[i, j] = value
        matrix[j, i] = 1.0 / value

    return matrix


def calculate_ahp_weights(matrix):
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    max_index = np.argmax(eigenvalues.real)
    lambda_max = eigenvalues[max_index].real

    principal_vector = eigenvectors[:, max_index].real
    weights = principal_vector / principal_vector.sum()

    n = matrix.shape[0]
    ci = 0.0 if n <= 1 else (lambda_max - n) / (n - 1)
    ri = RI_TABLE.get(n, 1.49)
    cr = 0.0 if ri == 0 else ci / ri

    return {
        "weights": weights.tolist(),
        "lambda_max": float(lambda_max),
        "ci": float(ci),
        "cr": float(cr),
        "is_consistent": bool(cr < 0.1),
    }