# BGL: five-model comparison

Same temporal test set for every model: 2,899 sessions (225 anomalous), 52 features, test-id hash `ce20f994a68c`.

Identical for all models: fit on the training period; choose the decision threshold that maximises F1 on the validation period; refit on train+validation; score once on the later test period. No shuffling, same 52 features.

| Model | Role | Accuracy | Precision | Recall | F1 | PR-AUC | FP | FN | Fit (s) | Predict (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| Logistic regression | baseline | 0.9383 | 0.5865 | 0.6933 | 0.6354 | 0.6024 | 110 | 69 | 0.0 | 0.00 |
| Random forest | compared | 0.9614 | 0.8343 | 0.6267 | 0.7157 | 0.8760 | 28 | 84 | 0.2 | 0.01 |
| Histogram gradient boosting | final (deployed) | 0.9586 | 0.8571 | 0.5600 | 0.6774 | 0.8804 | 21 | 99 | 0.1 | 0.00 |
| Extra trees | additional | 0.9486 | 0.8276 | 0.4267 | 0.5630 | 0.7950 | 20 | 129 | 0.2 | 0.01 |
| XGBoost | additional | 0.9683 | 0.8482 | 0.7200 | 0.7788 | 0.8965 | 29 | 63 | 0.1 | 0.00 |

Fit time is the refit on train+validation; predict time is scoring the whole test set. Timings depend on the machine (models used at most 2 CPU threads).

## Logistic regression

* **Type:** Linear model (L2-regularised logistic regression)
* **Learning approach:** Learns one weight per feature; the anomaly probability is a sigmoid of a weighted sum, fitted by convex optimisation. It is the only model that is linear in its inputs.
* **Feature scaling:** required - StandardScaler applied inside the model pipeline
* **Key configuration:** C=1.0, max_iter=500, class_weight=balanced, n_iter_fitted=68
* **Suitability for the 52 BGL session features:** Fast, interpretable baseline; class weighting offsets the anomaly class imbalance. It cannot express feature interactions or thresholds (e.g. "no completion event AND a long gap") unless they are hand-crafted, and durations/counts are used on their raw, heavily skewed scale.

## Random forest

* **Type:** Bagged ensemble of deep decision trees
* **Learning approach:** Many trees are grown independently on bootstrap samples with random feature subsets and their votes are averaged: variance is reduced by averaging, not by correcting errors.
* **Feature scaling:** not required
* **Key configuration:** n_estimators=80, max_depth=18, min_samples_leaf=2, max_features=sqrt, class_weight=balanced
* **Suitability for the 52 BGL session features:** Splits are threshold tests, so mixed binary/count/duration features, skew and correlated timing features need no transformation, and interactions between lifecycle and timing features are learned.

## Histogram gradient boosting

* **Type:** Gradient-boosted decision trees (scikit-learn, histogram-based)
* **Learning approach:** Shallow trees are added one after another, each fitted to the errors of the ensemble so far; features are pre-binned into histograms so training is fast on 575k sessions.
* **Feature scaling:** not required
* **Key configuration:** max_iter=100, max_leaf_nodes=31, learning_rate=0.1, early_stopping=auto, n_iter_fitted=59
* **Suitability for the 52 BGL session features:** Boosting concentrates on hard, borderline sessions, which matters when the anomaly class is the minority; binning copes with the skewed feature scales. Not class-weighted: the threshold is tuned instead.

## Extra trees

* **Type:** Extremely randomised trees ensemble
* **Learning approach:** Like the random forest, but split thresholds are drawn at random rather than optimised and each tree uses the whole training set: extra randomisation lowers variance and trains faster.
* **Feature scaling:** not required
* **Key configuration:** n_estimators=100, max_depth=18, min_samples_leaf=2, bootstrap=False, class_weight=balanced
* **Suitability for the 52 BGL session features:** Random thresholds give smoother decision boundaries on the correlated timing features and cheap training; class weighting offsets the rare anomaly class.

## XGBoost

* **Type:** Gradient-boosted decision trees (XGBoost library)
* **Learning approach:** Boosting like the model above, but each tree is fitted using second-order (curvature) gradient information and an explicitly regularised objective that penalises complex trees.
* **Feature scaling:** not required
* **Key configuration:** n_estimators=100, max_depth=6, learning_rate=0.1, tree_method=hist
* **Suitability for the 52 BGL session features:** Same suitability as other tree boosters for mixed, skewed tabular features; the added regularisation limits over-fitting to rare failure patterns. Not class-weighted.
