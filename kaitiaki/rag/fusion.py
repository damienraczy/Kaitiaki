# kaitiaki/rag/fusion.py
def rrf_merge(list_a, list_b, k=60):
    """Reciprocal Rank Fusion: chaque liste est une liste de tuples (id, score) ou (id, obj).
       On renvoie une liste d'ids ordonnés par score RRF.
    """
    ranks = {}
    for lst in [list_a, list_b]:
        for rank, (id_, _) in enumerate(lst, start=1):
            ranks[id_] = ranks.get(id_, 0.0) + 1.0 / (k + rank)
    return sorted(ranks.items(), key=lambda x: x[1], reverse=True)
