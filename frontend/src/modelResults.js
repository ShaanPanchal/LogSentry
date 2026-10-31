// Model comparison and temporal-robustness results shown in the "Choose a dataset to inspect" panel.
// load_model_info -> comparison_rows, folds_summary): results/{HDFS,BGL}_model_comparison.json and
// results/BGL_temporal_folds.json (HDFS has no temporal-folds file, so it has no robustness table, as in A2).
// These are historical training/test results, not results for an uploaded log. The A3 API does not serve them.
export const MODEL_RESULTS = {
  "HDFS": {
    "models": [
      {
        "model": "Logistic regression",
        "role": "baseline",
        "final": false,
        "accuracy": 0.9980177015771444,
        "precision": 0.9577553593947037,
        "recall": 0.9041666666666667,
        "f1": 0.9301898346601347,
        "prAuc": 0.9327958223679784,
        "fp": 67,
        "fn": 161,
        "fitSeconds": 0.92,
        "predictSeconds": 0.021,
        "profile": {
          "type": "Linear model (L2-regularised logistic regression)",
          "learningApproach": "Learns one weight per feature; the anomaly probability is a sigmoid of a weighted sum, fitted by convex optimisation. It is the only model that is linear in its inputs.",
          "scaling": "required - StandardScaler applied inside the model pipeline",
          "keyConfig": "C=1.0, max_iter=500, class_weight=balanced, n_iter_fitted=101",
          "nFeatures": 52,
          "suitability": "Fast, interpretable baseline; class weighting offsets the anomaly class imbalance. It cannot express feature interactions or thresholds (e.g. \"no completion event AND a long gap\") unless they are hand-crafted, and durations/counts are used on their raw, heavily skewed scale."
        }
      },
      {
        "model": "Random forest",
        "role": "compared",
        "final": false,
        "accuracy": 0.9987045505920812,
        "precision": 1.0,
        "recall": 0.9113095238095238,
        "f1": 0.9535970102771723,
        "prAuc": 0.9998566021143258,
        "fp": 0,
        "fn": 149,
        "fitSeconds": 7.13,
        "predictSeconds": 0.096,
        "profile": {
          "type": "Bagged ensemble of deep decision trees",
          "learningApproach": "Many trees are grown independently on bootstrap samples with random feature subsets and their votes are averaged: variance is reduced by averaging, not by correcting errors.",
          "scaling": "not required",
          "keyConfig": "n_estimators=80, max_depth=18, min_samples_leaf=2, max_features=sqrt, class_weight=balanced",
          "nFeatures": 52,
          "suitability": "Splits are threshold tests, so mixed binary/count/duration features, skew and correlated timing features need no transformation, and interactions between lifecycle and timing features are learned."
        }
      },
      {
        "model": "Histogram gradient boosting",
        "role": "final (deployed)",
        "final": true,
        "accuracy": 0.9998000312994488,
        "precision": 0.9993972272453285,
        "recall": 0.986904761904762,
        "f1": 0.9931117100928422,
        "prAuc": 0.9995926938209194,
        "fp": 1,
        "fn": 22,
        "fitSeconds": 1.63,
        "predictSeconds": 0.074,
        "profile": {
          "type": "Gradient-boosted decision trees (scikit-learn, histogram-based)",
          "learningApproach": "Shallow trees are added one after another, each fitted to the errors of the ensemble so far; features are pre-binned into histograms so training is fast on 575k sessions.",
          "scaling": "not required",
          "keyConfig": "max_iter=100, max_leaf_nodes=31, learning_rate=0.1, early_stopping=auto, n_iter_fitted=94",
          "nFeatures": 52,
          "suitability": "Boosting concentrates on hard, borderline sessions, which matters when the anomaly class is the minority; binning copes with the skewed feature scales. Not class-weighted: the threshold is tuned instead."
        }
      },
      {
        "model": "Extra trees",
        "role": "additional",
        "final": false,
        "accuracy": 0.9997739484254639,
        "precision": 1.0,
        "recall": 0.9845238095238096,
        "f1": 0.9922015596880623,
        "prAuc": 0.9998120927624847,
        "fp": 0,
        "fn": 26,
        "fitSeconds": 7.13,
        "predictSeconds": 0.136,
        "profile": {
          "type": "Extremely randomised trees ensemble",
          "learningApproach": "Like the random forest, but split thresholds are drawn at random rather than optimised and each tree uses the whole training set: extra randomisation lowers variance and trains faster.",
          "scaling": "not required",
          "keyConfig": "n_estimators=100, max_depth=18, min_samples_leaf=2, bootstrap=False, class_weight=balanced",
          "nFeatures": 52,
          "suitability": "Random thresholds give smoother decision boundaries on the correlated timing features and cheap training; class weighting offsets the rare anomaly class."
        }
      },
      {
        "model": "XGBoost",
        "role": "additional",
        "final": false,
        "accuracy": 0.9998695856300753,
        "precision": 0.9988016776512882,
        "recall": 0.9922619047619048,
        "f1": 0.9955210510600179,
        "prAuc": 0.9995796323244142,
        "fp": 2,
        "fn": 13,
        "fitSeconds": 1.72,
        "predictSeconds": 0.073,
        "profile": {
          "type": "Gradient-boosted decision trees (XGBoost library)",
          "learningApproach": "Boosting like the model above, but each tree is fitted using second-order (curvature) gradient information and an explicitly regularised objective that penalises complex trees.",
          "scaling": "not required",
          "keyConfig": "n_estimators=100, max_depth=6, learning_rate=0.1, tree_method=hist",
          "nFeatures": 52,
          "suitability": "Same suitability as other tree boosters for mixed, skewed tabular features; the added regularisation limits over-fitting to rare failure patterns. Not class-weighted."
        }
      }
    ],
    "profileNote": "Identical for all models: fit on the training period; choose the decision threshold that maximises F1 on the validation period; refit on train+validation; score once on the later test period. No shuffling, same 52 features.",
    "split": {
      "testSessions": 115018,
      "testAnomalies": 1680,
      "shared": true,
      "testSetSha1": "a671043618fbf46fd310daafa9478d36ada921bb"
    },
    "folds": null
  },
  "BGL": {
    "models": [
      {
        "model": "Logistic regression",
        "role": "baseline",
        "final": false,
        "accuracy": 0.938254570541566,
        "precision": 0.5864661654135338,
        "recall": 0.6933333333333334,
        "f1": 0.6354378818737271,
        "prAuc": 0.6024224569400466,
        "fp": 110,
        "fn": 69,
        "fitSeconds": 0.04,
        "predictSeconds": 0.001,
        "profile": {
          "type": "Linear model (L2-regularised logistic regression)",
          "learningApproach": "Learns one weight per feature; the anomaly probability is a sigmoid of a weighted sum, fitted by convex optimisation. It is the only model that is linear in its inputs.",
          "scaling": "required - StandardScaler applied inside the model pipeline",
          "keyConfig": "C=1.0, max_iter=500, class_weight=balanced, n_iter_fitted=68",
          "nFeatures": 52,
          "suitability": "Fast, interpretable baseline; class weighting offsets the anomaly class imbalance. It cannot express feature interactions or thresholds (e.g. \"no completion event AND a long gap\") unless they are hand-crafted, and durations/counts are used on their raw, heavily skewed scale."
        }
      },
      {
        "model": "Random forest",
        "role": "compared",
        "final": false,
        "accuracy": 0.9613659882718179,
        "precision": 0.834319526627219,
        "recall": 0.6266666666666667,
        "f1": 0.7157360406091371,
        "prAuc": 0.8759581641447215,
        "fp": 28,
        "fn": 84,
        "fitSeconds": 0.2,
        "predictSeconds": 0.013,
        "profile": {
          "type": "Bagged ensemble of deep decision trees",
          "learningApproach": "Many trees are grown independently on bootstrap samples with random feature subsets and their votes are averaged: variance is reduced by averaging, not by correcting errors.",
          "scaling": "not required",
          "keyConfig": "n_estimators=80, max_depth=18, min_samples_leaf=2, max_features=sqrt, class_weight=balanced",
          "nFeatures": 52,
          "suitability": "Splits are threshold tests, so mixed binary/count/duration features, skew and correlated timing features need no transformation, and interactions between lifecycle and timing features are learned."
        }
      },
      {
        "model": "Histogram gradient boosting",
        "role": "final (deployed)",
        "final": true,
        "accuracy": 0.9586064160055191,
        "precision": 0.8571428571428571,
        "recall": 0.56,
        "f1": 0.6774193548387096,
        "prAuc": 0.8803682213576344,
        "fp": 21,
        "fn": 99,
        "fitSeconds": 0.12,
        "predictSeconds": 0.002,
        "profile": {
          "type": "Gradient-boosted decision trees (scikit-learn, histogram-based)",
          "learningApproach": "Shallow trees are added one after another, each fitted to the errors of the ensemble so far; features are pre-binned into histograms so training is fast on 575k sessions.",
          "scaling": "not required",
          "keyConfig": "max_iter=100, max_leaf_nodes=31, learning_rate=0.1, early_stopping=auto, n_iter_fitted=59",
          "nFeatures": 52,
          "suitability": "Boosting concentrates on hard, borderline sessions, which matters when the anomaly class is the minority; binning copes with the skewed feature scales. Not class-weighted: the threshold is tuned instead."
        }
      },
      {
        "model": "Extra trees",
        "role": "additional",
        "final": false,
        "accuracy": 0.9486029665401863,
        "precision": 0.8275862068965517,
        "recall": 0.4266666666666667,
        "f1": 0.5630498533724341,
        "prAuc": 0.7949531552757757,
        "fp": 20,
        "fn": 129,
        "fitSeconds": 0.23,
        "predictSeconds": 0.013,
        "profile": {
          "type": "Extremely randomised trees ensemble",
          "learningApproach": "Like the random forest, but split thresholds are drawn at random rather than optimised and each tree uses the whole training set: extra randomisation lowers variance and trains faster.",
          "scaling": "not required",
          "keyConfig": "n_estimators=100, max_depth=18, min_samples_leaf=2, bootstrap=False, class_weight=balanced",
          "nFeatures": 52,
          "suitability": "Random thresholds give smoother decision boundaries on the correlated timing features and cheap training; class weighting offsets the rare anomaly class."
        }
      },
      {
        "model": "XGBoost",
        "role": "additional",
        "final": false,
        "accuracy": 0.9682649189375647,
        "precision": 0.8481675392670157,
        "recall": 0.72,
        "f1": 0.7788461538461539,
        "prAuc": 0.8965065044477846,
        "fp": 29,
        "fn": 63,
        "fitSeconds": 0.12,
        "predictSeconds": 0.002,
        "profile": {
          "type": "Gradient-boosted decision trees (XGBoost library)",
          "learningApproach": "Boosting like the model above, but each tree is fitted using second-order (curvature) gradient information and an explicitly regularised objective that penalises complex trees.",
          "scaling": "not required",
          "keyConfig": "n_estimators=100, max_depth=6, learning_rate=0.1, tree_method=hist",
          "nFeatures": 52,
          "suitability": "Same suitability as other tree boosters for mixed, skewed tabular features; the added regularisation limits over-fitting to rare failure patterns. Not class-weighted."
        }
      }
    ],
    "profileNote": "Identical for all models: fit on the training period; choose the decision threshold that maximises F1 on the validation period; refit on train+validation; score once on the later test period. No shuffling, same 52 features.",
    "split": {
      "testSessions": 2899,
      "testAnomalies": 225,
      "shared": true,
      "testSetSha1": "ce20f994a68c930b4264b8c0e990d29fb7c36c44"
    },
    "folds": {
      "n_folds": 4,
      "rows": [
        {
          "model": "Logistic regression",
          "mean_f1": 0.5976169956733349,
          "min_f1": 0.5294117647058824,
          "max_f1": 0.6609124537607891,
          "std_f1": 0.05284843743857294,
          "mean_precision": 0.557440610072189,
          "mean_recall": 0.7122049569654291,
          "total_fp": 495,
          "total_fn": 246
        },
        {
          "model": "Random forest",
          "mean_f1": 0.777206500373927,
          "min_f1": 0.7157360406091371,
          "max_f1": 0.8389830508474576,
          "std_f1": 0.05051298249646026,
          "mean_precision": 0.7945791199025127,
          "mean_recall": 0.7840558342375052,
          "total_fp": 191,
          "total_fn": 176
        },
        {
          "model": "Histogram gradient boosting",
          "mean_f1": 0.7758259409796521,
          "min_f1": 0.6774193548387096,
          "max_f1": 0.8631921824104235,
          "std_f1": 0.08702275423655156,
          "mean_precision": 0.7859290128898055,
          "mean_recall": 0.7866324984897075,
          "total_fp": 189,
          "total_fn": 192
        },
        {
          "model": "Extra trees",
          "mean_f1": 0.7199983501752653,
          "min_f1": 0.5630498533724341,
          "max_f1": 0.8383233532934131,
          "std_f1": 0.11679571188503646,
          "mean_precision": 0.724833080530232,
          "mean_recall": 0.7735334533552538,
          "total_fp": 231,
          "total_fn": 190
        },
        {
          "model": "XGBoost",
          "mean_f1": 0.7841586475219072,
          "min_f1": 0.6361904761904762,
          "max_f1": 0.8707692307692307,
          "std_f1": 0.09201779073707803,
          "mean_precision": 0.7598302397622136,
          "mean_recall": 0.819416405934573,
          "total_fp": 242,
          "total_fn": 152
        }
      ],
      "rates": "8.0%, 10.3%, 3.0%, 7.8%"
    }
  }
};
