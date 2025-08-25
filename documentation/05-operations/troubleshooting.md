# Dépannage

## Problèmes de performance

* Réduire `rerank_top_k` et `max_tokens`.
* Vérifier que le LLM local répond dans les délais.

## Résultats médiocres

* Augmenter top\_k\_dense/BM25.
* Ajuster chunking et overlap.
* Qualité OCR insuffisante.

## Erreurs de citations

* Vérifier que les snippets proviennent des passages réellement fournis au LLM.

* Augmenter la longueur minimale des snippets.
  