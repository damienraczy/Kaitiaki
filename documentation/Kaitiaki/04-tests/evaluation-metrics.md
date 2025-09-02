# Métriques d’évaluation

* Latence p95 : 95 % des requêtes sous ce temps.

* Recall\@20 : part des références attendues (doc\_id,page) présentes dans les 20 premiers candidats.

* Taux de citations valides : proportion des citations dont le snippet apparaît sur la page référencée.

## Seuils V1

* Latence p95 ≤ 5 000 ms (CPU) ou ≤ 2 500 ms (GPU).

* Recall\@20 ≥ 0,70.

* Citations valides ≥ 0,80.
  