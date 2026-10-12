// Small display helpers.

export const formatScore = (score) => score.toFixed(4);

export const formatThreshold = (threshold) => threshold.toFixed(2);

export const formatPercent = (part, whole) => (whole ? `${((100 * part) / whole).toFixed(1)}%` : '0.0%');

// The API gives Unix seconds. Shown in UTC so the same log reads the same everywhere.
export const formatTime = (unixSeconds) => `${new Date(unixSeconds * 1000).toISOString().slice(0, 19).replace('T', ' ')} UTC`;

export const formatShortTime = (unixSeconds) => new Date(unixSeconds * 1000).toISOString().slice(0, 16).replace('T', ' ');

export const formatFeature = (value) => String(Number(value.toPrecision(4)));

export const formatBytes = (bytes) => `${(bytes / (1024 * 1024)).toFixed(1)} MiB`;
