"""Figures for the model comparison, final-model errors and clustering.

Reads results/<SOURCE>_evaluation.json, _cluster_analysis.json (written by
train.py) and writes figures/<SOURCE>_*.png.  Safe to re-run at any time.
"""
import argparse
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from processing import ROOT  # noqa: E402


def load(source, name):
    return json.loads((ROOT / 'results' / f'{source}_{name}.json').read_text())


def model_comparison(source, ev, out):
    names = [t['model'] for t in ev['temporal_test']]
    fig, ax = plt.subplots(figsize=(11, 4))
    width = .2
    for i, (key, label) in enumerate([('precision', 'precision'), ('recall', 'recall'),
                                      ('f1', 'F1'), ('average_precision', 'PR-AUC')]):
        ax.bar(np.arange(len(names)) + (i - 1.5) * width, [t[key] for t in ev['temporal_test']], width, label=label)
    ax.set_xticks(range(len(names))); ax.set_xticklabels(names, fontsize=8)
    ax.set_ylim(0, 1.18); ax.set_title(f'{source}: models on the temporal test period'); ax.legend(fontsize=8, ncol=4, loc='upper center')
    fig.tight_layout(); fig.savefig(out / f'{source}_model_comparison.png', dpi=130); plt.close(fig)


def confusion(source, ev, out):
    final = next(t for t in ev['temporal_test'] if t['model'] == ev['selected_model'])
    m = np.array([[final['tn'], final['fp']], [final['fn'], final['tp']]])
    fig, ax = plt.subplots(figsize=(4.2, 3.8))
    ax.imshow(np.log10(m + 1), cmap='Blues')
    for (i, j), v in np.ndenumerate(m):
        ax.text(j, i, f'{v:,}', ha='center', va='center', fontsize=12)
    ax.set_xticks([0, 1]); ax.set_xticklabels(['normal', 'anomaly']); ax.set_yticks([0, 1]); ax.set_yticklabels(['normal', 'anomaly'])
    ax.set_xlabel('predicted'); ax.set_ylabel('actual'); ax.set_title(f"{ev['selected_model']}\n(colour is log-scaled)", fontsize=10)
    fig.tight_layout(); fig.savefig(out / f'{source}_confusion_matrix.png', dpi=130); plt.close(fig)


def clusters(source, cl, out):
    ks = [s['k'] for s in cl['sweep']]
    fig, ax = plt.subplots(figsize=(5, 3.4))
    ax.plot(ks, [s['silhouette'] for s in cl['sweep']], 'o-')
    ax.axvline(cl['selected_k'], color='grey', ls='--'); ax.set_xlabel('k'); ax.set_ylabel('silhouette')
    ax.set_title('K-means within the anomaly class')
    fig.tight_layout(); fig.savefig(out / f'{source}_cluster_silhouette.png', dpi=130); plt.close(fig)

    feats = sorted({f['feature'] for c in cl['clusters'] for f in c['top_features']})
    grid = np.zeros((len(cl['clusters']), len(feats)))
    for i, c in enumerate(cl['clusters']):
        for f in c['top_features']:
            grid[i, feats.index(f['feature'])] = f['z']
    fig, ax = plt.subplots(figsize=(max(6, len(feats) * .6), 1 + len(grid) * .6))
    lim = 4  # colour scale clipped so the two tiny clusters (z up to ~35) don't hide the large ones
    im = ax.imshow(grid, cmap='coolwarm', vmin=-lim, vmax=lim, aspect='auto')
    for (i, j), v in np.ndenumerate(grid):
        if v:
            ax.text(j, i, f'{v:+.1f}', ha='center', va='center', fontsize=7)
    ax.set_xticks(range(len(feats))); ax.set_xticklabels(feats, rotation=60, ha='right', fontsize=8)
    ax.set_yticks(range(len(grid))); ax.set_yticklabels([f"cluster {c['cluster']} (n={c['sessions']:,})" for c in cl['clusters']], fontsize=8)
    fig.colorbar(im, label='z (clipped at +/-4)'); ax.set_title('Most distinctive features per cluster')
    fig.tight_layout(); fig.savefig(out / f'{source}_cluster_signatures.png', dpi=130); plt.close(fig)


def run(source):
    out = ROOT / 'figures'
    out.mkdir(exist_ok=True)
    ev = load(source, 'evaluation')
    model_comparison(source, ev, out)
    confusion(source, ev, out)
    clusters(source, load(source, 'cluster_analysis'), out)
    print('Figures written to', out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Regenerate result figures.')
    parser.add_argument('--source', choices=['HDFS', 'BGL'], default='HDFS')
    run(parser.parse_args().source)
