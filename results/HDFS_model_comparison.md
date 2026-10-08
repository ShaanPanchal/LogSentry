# HDFS: five-model comparison

Same temporal test set for every model: 115,018 sessions (1,680 anomalous), 52 features, test-id hash `a671043618fb`.

Identical for all models: fit on the training period; choose the decision threshold that maximises F1 on the validation period; refit on train+validation; score once on the later test period. No shuffling, same 52 features.

| Model | Role | Accuracy | Precision | Recall | F1 | PR-AUC | FP | FN | Fit (s) | Predict (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| Logistic regression | baseline | 0.9980 | 0.9578 | 0.9042 | 0.9302 | 0.9328 | 67 | 161 | 0.8 | 0.01 |
| Random forest | compared | 0.9987 | 1.0000 | 0.9113 | 0.9536 | 0.9999 | 0 | 149 | 5.4 | 0.07 |
| Histogram gradient boosting | final (deployed) | 0.9998 | 0.9994 | 0.9869 | 0.9931 | 0.9996 | 1 | 22 | 1.6 | 0.06 |
| Extra trees | additional | 0.9998 | 1.0000 | 0.9845 | 0.9922 | 0.9998 | 0 | 26 | 5.0 | 0.10 |
| XGBoost | additional | 0.9999 | 0.9988 | 0.9923 | 0.9955 | 0.9996 | 2 | 13 | 1.4 | 0.07 |

Fit time is the refit on train+validation; predict time is scoring the whole test set. Timings depend on the machine (models used at most 2 CPU threads).

## Logistic regression

* **Type:** Linear model (L2-regularised logistic regression)
* **Learning approach:** Learns one weight per feature; the anomaly probability is a sigmoid of a weighted sum, fitted by convex optimisation. It is the only model that is linear in its inputs.
* **Feature scaling:** required - StandardScaler applied inside the model pipeline
* **Key configuration:** C=1.0, max_iter=500, class_weight=balanced, n_iter_fitted=101
* **Suitability for the 52 HDFS session features:** Fast, interpretable baseline; class weighting offsets the ~3% anomaly rate. It cannot express feature interactions or thresholds (e.g. "write chain incomplete AND long gap") unless they are hand-crafted, and durations/counts are used on their raw, heavily skewed scale.

## Random forest

* **Type:** Bagged ensemble of deep decision trees
* **Learning approach:** Many trees are grown independently on bootstrap samples with random feature subsets and their votes are averaged: variance is reduced by averaging, not by correcting errors.
* **Feature scaling:** not required
* **Key configuration:** n_estimators=80, max_depth=18, min_samples_leaf=2, max_features=sqrt, class_weight=balanced
* **Suitability for the 52 HDFS session features:** Splits are threshold tests, so mixed binary/count/duration features, skew and correlated timing features need no transformation, and interactions between lifecycle and timing features are learned.

## Histogram gradient boosting

* **Type:** Gradient-boosted decision trees (scikit-learn, histogram-based)
* **Learning approach:** Shallow trees are added one after another, each fitted to the errors of the ensemble so far; features are pre-binned into histograms so training is fast on 575k sessions.
* **Feature scaling:** not required
* **Key configuration:** max_iter=100, max_leaf_nodes=31, learning_rate=0.1, early_stopping=auto, n_iter_fitted=94
* **Suitability for the 52 HDFS session features:** Boosting concentrates on hard, borderline sessions, which matters when anomalies are rare; binning copes with the skewed feature scales. Not class-weighted: the threshold is tuned instead.

## Extra trees

* **Type:** Extremely randomised trees ensemble
* **Learning approach:** Like the random forest, but split thresholds are drawn at random rather than optimised and each tree uses the whole training set: extra randomisation lowers variance and trains faster.
* **Feature scaling:** not required
* **Key configuration:** n_estimators=100, max_depth=18, min_samples_leaf=2, bootstrap=False, class_weight=balanced
* **Suitability for the 52 HDFS session features:** Random thresholds give smoother decision boundaries on the correlated timing features and cheap training; class weighting offsets the rare anomaly class.

## XGBoost

* **Type:** Gradient-boosted decision trees (XGBoost library)
* **Learning approach:** Boosting like the model above, but each tree is fitted using second-order (curvature) gradient information and an explicitly regularised objective that penalises complex trees.
* **Feature scaling:** not required
* **Key configuration:** n_estimators=100, max_depth=6, learning_rate=0.1, tree_method=hist
* **Suitability for the 52 HDFS session features:** Same suitability as other tree boosters for mixed, skewed tabular features; the added regularisation limits over-fitting to rare failure patterns. Not class-weighted.
