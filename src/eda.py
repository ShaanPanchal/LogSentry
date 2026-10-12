"""Exploratory data analysis of the processed session table.

Checks data quality (missing values, duplicates, constant columns), compares normal and
anomalous sessions, and looks at correlated features. The findings explain some choices:

* very few anomalies, so class weights are used and models are judged by PR-AUC and F1
* counts and durations are very skewed, so a signed log is used before clustering
* some timing features are strongly correlated, but tree models cope, so none are dropped
* the write chain features separate the classes well, so they are kept

Writes results/<SOURCE>_eda_summary.json and figures/<SOURCE>_eda*.png.
"""
import argparse
import json

import mkl_setup  # noqa: F401  (Windows MKL fix, must come before numpy)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from features import STRUCTURAL_COLS  # noqa: E402
from processing import COLS, ROOT  # noqa: E402
from train import load_dataset  # noqa: E402

BOX_FEATURES = ['n_events', 'n_event_buckets', 'duration_s', 'gap_max_s',
                'n_hosts', 'n_threads', 'unacked_writes', 'keyword_error_ratio']
LOG_FEATURES = {'duration_s', 'gap_max_s', 'gap_mean_s'}
COLORS = {0: '#2a78d6', 1: '#eb6a35'}


def summarise(df):
    y = df.label
    X = df[COLS]
    # Skew and correlation are only checked for the structural columns, not the 32 event count columns.
    skew = X[STRUCTURAL_COLS].skew()
    corr = X[STRUCTURAL_COLS].corr().abs()
    pairs = [(a, b, float(corr.loc[a, b])) for i, a in enumerate(STRUCTURAL_COLS)
             for b in STRUCTURAL_COLS[i + 1:] if corr.loc[a, b] > .9]
    return {
        'n_sessions': int(len(df)), 'n_features': len(COLS),
        'missing_values_total': int(df[COLS].isna().sum().sum()),
        'duplicate_session_ids': int(df.session_id.duplicated().sum()),
        'class_balance': {'normal': int((y == 0).sum()), 'anomaly': int((y == 1).sum()),
                          'anomaly_rate': float((y == 1).mean()),
                          'imbalance_ratio': float((y == 0).sum() / max((y == 1).sum(), 1))},
        'constant_columns': [c for c in COLS if X[c].nunique() <= 1],
        'most_skewed': {k: float(v) for k, v in skew.abs().sort_values(ascending=False).head(6).items()},
        'highly_correlated_pairs(|r|>0.9)': [{'a': a, 'b': b, 'r': round(r, 3)} for a, b, r in sorted(pairs, key=lambda p: -p[2])],
        'class_means': {c: {'normal': float(X.loc[y == 0, c].mean()), 'anomaly': float(X.loc[y == 1, c].mean())}
                        for c in STRUCTURAL_COLS},
    }


def figures(df, source):
    out = ROOT / 'figures'
    out.mkdir(exist_ok=True)
    y = df.label.to_numpy()

    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    ax[0].bar(['normal', 'anomaly'], [(y == 0).sum(), (y == 1).sum()], color=[COLORS[0], COLORS[1]])
    ax[0].set_yscale('log'); ax[0].set_title('Class balance (log scale)'); ax[0].set_ylabel('sessions')
    ax[1].hist(df.n_events.clip(upper=60), bins=60, color=COLORS[0]); ax[1].set_yscale('log')
    ax[1].set_title('Events per session (clipped at 60)'); ax[1].set_xlabel('events')
    ax[2].hist(np.log10(df.duration_s + 1), bins=50, color=COLORS[0])
    ax[2].set_title('Session duration'); ax[2].set_xlabel('log10(seconds + 1)')
    fig.tight_layout(); fig.savefig(out / f'{source}_eda1_overview.png', dpi=130); plt.close(fig)

    fig, axes = plt.subplots(2, 4, figsize=(13, 6))
    for ax, f in zip(axes.ravel(), BOX_FEATURES):
        data = [df.loc[y == 0, f], df.loc[y == 1, f]]
        if f in LOG_FEATURES:
            data = [np.log10(d + 1) for d in data]
        bp = ax.boxplot(data, tick_labels=['normal', 'anomaly'], patch_artist=True, showfliers=False)
        for patch, c in zip(bp['boxes'], (COLORS[0], COLORS[1])):
            patch.set_facecolor(c)
        ax.set_title(f + (' (log10)' if f in LOG_FEATURES else ''), fontsize=10)
    fig.suptitle('Structural features by class (outliers hidden)')
    fig.tight_layout(); fig.savefig(out / f'{source}_eda2_by_class.png', dpi=130); plt.close(fig)

    corr = df[STRUCTURAL_COLS].corr().fillna(0)
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr))); ax.set_xticklabels(corr.columns, rotation=60, ha='right', fontsize=7)
    ax.set_yticks(range(len(corr))); ax.set_yticklabels(corr.columns, fontsize=7)
    fig.colorbar(im, label='Pearson correlation'); ax.set_title('Redundancy among structural features')
    fig.tight_layout(); fig.savefig(out / f'{source}_eda3_correlation.png', dpi=130); plt.close(fig)


def run(source):
    df = load_dataset(source)
    (ROOT / 'results').mkdir(exist_ok=True)
    summary = summarise(df)
    (ROOT / 'results' / f'{source}_eda_summary.json').write_text(json.dumps(summary, indent=2))
    figures(df, source)
    print(f"EDA: {summary['n_sessions']:,} sessions, anomaly rate {summary['class_balance']['anomaly_rate']:.3%}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Exploratory analysis of the processed dataset.')
    parser.add_argument('--source', choices=['HDFS', 'BGL'], default='HDFS')
    run(parser.parse_args().source)
