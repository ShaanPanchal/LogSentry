# BGL anomaly clusters

KMeans (signed-log + standardised features, labels excluded). Clustered: development-period anomalies only (n=829); k=7 chosen by silhouette among k>=3.

## Cluster 0 - 104 sessions (12.5%)

Cluster 0 holds 12.5% of the clustered anomalies. Compared with the overall anomaly population, its members show: gap_mean_s is above the anomaly average (19.5 vs 3.5): long pauses between events (slow progress); gap_std_s is above the anomaly average (27.6 vs 5.93): irregular timing (bursts and stalls); gap_max_s is above the anomaly average (93.4 vs 32.9): at least one long stall mid-session; events_per_min is below the anomaly average (6.47 vs 157): sparse events spread over time; n_events is below the anomaly average (20.1 vs 585): very few events (the session stops early). The sessions nearest its centre are dominated by: "Lustre mount FAILED : bglio<N> : point <PATH>" (5.2/session), "CE sym <N>, at <HEX>, mask <HEX>" (1.2/session), "<N> ddr errors(s) detected and corrected on rank <N>, symbol <N>, bit <N>" (0.8/session). Profile: mean events 20.1 (anomaly avg 584.6); mean duration 134 (anomaly avg 99) s; share of failure-keyword messages 56.7% (anomaly avg 56.2%); mean hosts 10.6 (anomaly avg 281.4).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| gap_mean_s | 19.51 | 3.502 | 14.11 | +1.87 |
| gap_std_s | 27.56 | 5.934 | 9.151 | +1.63 |
| gap_max_s | 93.39 | 32.92 | 39.79 | +1.21 |
| events_per_min | 6.467 | 156.9 | 89.76 | -1.12 |
| n_events | 20.13 | 584.6 | 355.2 | -0.88 |

Test-period sessions nearest this cluster: 27 anomalous, 690 normal.

Example session `window_3747162` (3 events):

    FATAL kernel panic
    FATAL kernel panic
    INFO  shutdown complete

Example session `window_3749425` (3 events):

    FATAL kernel panic
    FATAL kernel panic
    INFO  shutdown complete

## Cluster 1 - 91 sessions (11.0%)

Cluster 1 holds 11.0% of the clustered anomalies. Compared with the overall anomaly population, its members show: event_hash_18 is above the anomaly average (1.76e+03 vs 205): more events like "data TLB error interrupt" / "total of <N> ddr error(s) detected and corrected" (bucket shared by several event kinds); n_events is above the anomaly average (2.15e+03 vs 585): more events than a typical anomaly (repeated or retried operations); events_per_min is above the anomaly average (434 vs 157): dense bursts of events; duration_s is above the anomaly average (273 vs 99.4): long-running sessions; event_entropy is below the anomaly average (0.0671 vs 1.47): dominated by one event kind. The sessions nearest its centre are dominated by: "data TLB error interrupt" (199.9/session), "ddr: excessive soft failures, consider replacing the card" (0.1/session). Profile: mean events 2150.8 (anomaly avg 584.6); mean duration 273 (anomaly avg 99) s; share of failure-keyword messages 89.5% (anomaly avg 56.2%); mean hosts 400.7 (anomaly avg 281.4).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| event_hash_18 | 1762 | 205.2 | 20.7 | +2.45 |
| n_events | 2151 | 584.6 | 355.2 | +1.44 |
| events_per_min | 434 | 156.9 | 89.76 | +1.20 |
| duration_s | 273.2 | 99.45 | 79.4 | +1.06 |
| event_entropy | 0.06713 | 1.469 | 0.9276 | -1.03 |

Test-period sessions nearest this cluster: 0 anomalous, 2 normal.

Example session `window_3728456` (2093 events):

    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt

Example session `window_3728504` (1951 events):

    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt
    FATAL data TLB error interrupt

## Cluster 2 - 153 sessions (18.5%)

Cluster 2 holds 18.5% of the clustered anomalies. Compared with the overall anomaly population, its members show: duration_s is below the anomaly average (1.88 vs 99.4): sessions that finish almost instantly; n_events is below the anomaly average (6.73 vs 585): very few events (the session stops early); events_per_min is below the anomaly average (6.37 vs 157): sparse events spread over time; gap_max_s is below the anomaly average (1.26 vs 32.9): no long stalls; n_hosts is below the anomaly average (4.99 vs 281): fewer hosts than usual. The sessions nearest its centre are dominated by: "Lustre mount FAILED : bglio<N> : point <PATH>" (0.8/session), "MailboxMonitor::serviceMailboxes() lib_ido_error: <N> socket closed" (0.5/session), "kernel panic" (0.2/session). Profile: mean events 6.7 (anomaly avg 584.6); mean duration 2 (anomaly avg 99) s; share of failure-keyword messages 65.2% (anomaly avg 56.2%); mean hosts 5.0 (anomaly avg 281.4).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| duration_s | 1.876 | 99.45 | 79.4 | -1.71 |
| n_events | 6.725 | 584.6 | 355.2 | -1.32 |
| events_per_min | 6.37 | 156.9 | 89.76 | -1.17 |
| gap_max_s | 1.261 | 32.92 | 39.79 | -0.94 |
| n_hosts | 4.993 | 281.4 | 189.8 | -0.79 |

Test-period sessions nearest this cluster: 31 anomalous, 1,382 normal.

Example session `window_3752866` (4 events):

    FATAL Lustre mount FAILED : bglio819 : point /p/gb1
    FATAL Lustre mount FAILED : bglio820 : point /p/gb1
    FATAL Lustre mount FAILED : bglio817 : point /p/gb1
    FATAL Lustre mount FAILED : bglio818 : point /p/gb1

Example session `window_3752865` (4 events):

    FATAL Lustre mount FAILED : bglio827 : point /p/gb1
    FATAL Lustre mount FAILED : bglio828 : point /p/gb1
    FATAL Lustre mount FAILED : bglio825 : point /p/gb1
    FATAL Lustre mount FAILED : bglio826 : point /p/gb1

## Cluster 3 - 33 sessions (4.0%)

Cluster 3 holds 4.0% of the clustered anomalies. Compared with the overall anomaly population, its members show: event_hash_15 is above the anomaly average (4.18 vs 0.314): more events like "program interrupt: imprecise exception......<N>" / "iar <N> dear <N>c<N>dc" (bucket shared by several event kinds); event_hash_29 is above the anomaly average (105 vs 5.13): more events like "machine check enable..............<N>" / "iar <N>c dear <N>f<N>c" (bucket shared by several event kinds); event_hash_03 is above the anomaly average (26.1 vs 1.75): more events like "Node card is not fully functional" / "store operation.............................<N>" (bucket shared by several event kinds); event_hash_27 is above the anomaly average (3.42 vs 0.859): more events like "ciod: generated <N> core files for program IMB-MPI<N>KB_perf" / "iar <N>c dear <N>f<N>ec" (bucket shared by several event kinds); event_hash_31 is above the anomaly average (8.03 vs 0.666): more events like "data store interrupt caused by icbi.........<N>" / "disable store gathering..................<N>" (bucket shared by several event kinds). The sessions nearest its centre are dominated by: "CE sym <N>, at <HEX>, mask <HEX>" (18.9/session), "<N> ddr errors(s) detected and corrected on rank <N>, symbol <N>, bit <N>" (7.6/session), "total of <N> ddr error(s) detected and corrected" (5.7/session). Profile: mean events 800.3 (anomaly avg 584.6); mean duration 99 (anomaly avg 99) s; share of failure-keyword messages 33.7% (anomaly avg 56.2%); mean hosts 335.9 (anomaly avg 281.4).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| event_hash_15 | 4.182 | 0.3136 | 2.804 | +3.04 |
| event_hash_29 | 104.7 | 5.128 | 2.444 | +2.79 |
| event_hash_03 | 26.09 | 1.754 | 5.098 | +2.77 |
| event_hash_27 | 3.424 | 0.8589 | 0.9012 | +2.68 |
| event_hash_31 | 8.03 | 0.6659 | 2.346 | +2.67 |

Test-period sessions nearest this cluster: 56 anomalous, 16 normal.

Example session `window_3760937` (134 events):

    FATAL floating point unavailable interrupt
    FATAL floating point unavailable interrupt
    FATAL instruction address: 0x00003720
    FATAL instruction address: 0x00003720
    FATAL exception syndrome register: 0x00800000
    FATAL exception syndrome register: 0x00800000
    FATAL machine check: i-fetch......................0
    FATAL machine check: i-fetch......................0

Example session `window_3760632` (175 events):

    INFO  1 L3 EDRAM error(s) (dcr 0x0157) detected and corrected
    INFO  1 L3 EDRAM error(s) (dcr 0x0157) detected and corrected
    INFO  1 ddr errors(s) detected and corrected on rank 0, symbol 18, bit 3
    INFO  1 ddr errors(s) detected and corrected on rank 0, symbol 5, bit 5
    INFO  1 ddr errors(s) detected and corrected on rank 0, symbol 34, bit 5
    INFO  1 ddr errors(s) detected and corrected on rank 0, symbol 26, bit 3
    INFO  1 ddr errors(s) detected and corrected on rank 0, symbol 16, bit 5
    INFO  1 ddr errors(s) detected and corrected on rank 0, symbol 30, bit 7

## Cluster 4 - 27 sessions (3.3%)

Cluster 4 holds 3.3% of the clustered anomalies. Compared with the overall anomaly population, its members show: warning_ratio is above the anomaly average (0.464 vs 0.0161): a high share of warnings; n_threads is above the anomaly average (2.89 vs 1.25): more threads/components involved; gap_mean_s is above the anomaly average (20 vs 3.5): long pauses between events (slow progress); gap_std_s is above the anomaly average (24.9 vs 5.93): irregular timing (bursts and stalls); transition_change_ratio is above the anomaly average (0.903 vs 0.353): frequent switching between event kinds. The sessions nearest its centre are dominated by: "Ido packet timeout" (1.1/session), "MailboxMonitor::serviceMailboxes() lib_ido_error: <N> BGLERR_IDO_PKT_TIMEOUT connection lost to node<PATH> card" (1.0/session), "PrepareForService is being done on this part (mLctn(R<N>-M<N>-N<N>), mCardSernum(<N>c<N>b<N>), mLp(FF:F<N>:<N>F:<N>:CD:<N>:<N>:<N>D:<N>:E<N>:<N>:AC), mIp(<IP>), mType(<N>)) by gooding<N>" (0.1/session). Profile: mean events 22.4 (anomaly avg 584.6); mean duration 137 (anomaly avg 99) s; share of failure-keyword messages 37.2% (anomaly avg 56.2%); mean hosts 9.7 (anomaly avg 281.4).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| warning_ratio | 0.4641 | 0.01613 | 0.02566 | +4.95 |
| n_threads | 2.889 | 1.255 | 1.079 | +2.77 |
| gap_mean_s | 19.96 | 3.502 | 14.11 | +2.09 |
| gap_std_s | 24.88 | 5.934 | 9.151 | +1.74 |
| transition_change_ratio | 0.9027 | 0.353 | 0.3473 | +1.37 |

Test-period sessions nearest this cluster: 4 anomalous, 72 normal.

Example session `window_3745182` (4 events):

    WARNING PrepareForService is being done on this part (mLctn(R31-M1-N6), mCardSernum(203231503833343000000000594c31304b3433343230
    ERROR Ido packet timeout
    FATAL MailboxMonitor::serviceMailboxes() lib_ido_error: -1033 BGLERR_IDO_PKT_TIMEOUT connection lost to node/link/service card
    WARNING PrepareForService shutting down NodeCard(mLctn(R31-M1-N6), mCardSernum(203231503833343000000000594c31304b34333432303230)

Example session `window_3760018` (4 events):

    ERROR Ido packet timeout
    FATAL MailboxMonitor::serviceMailboxes() lib_ido_error: -1033 BGLERR_IDO_PKT_TIMEOUT connection lost to node/link/service card
    WARNING PrepareForService is being done on this part (mLctn(R40-M1-N6), mCardSernum(203231503833343000000000594c31304b3530313030
    WARNING PrepareForService shutting down NodeCard(mLctn(R40-M1-N6), mCardSernum(203231503833343000000000594c31304b35303130303231)

## Cluster 5 - 241 sessions (29.1%)

Cluster 5 holds 29.1% of the clustered anomalies. Compared with the overall anomaly population, its members show: n_event_buckets is above the anomaly average (20.1 vs 9.01): a wider variety of event kinds; event_hash_16 is above the anomaly average (4.26 vs 1.72): more events like "<N> L<N> EDRAM error(s) (dcr <HEX>) detected and corrected" / "ciod: cpu <N> at treeaddr <N> sent unrecognized message <HEX>" (bucket shared by several event kinds); event_entropy is above the anomaly average (3 vs 1.47): a more varied mix of events; event_hash_11 is above the anomaly average on the log scale used for clustering (typical value 2.34 vs 0.617; the raw means, 2.98 vs 6.32, point the other way because a few very large values skew the raw average): more events like "floating pt ex mode <N> enable......<N>" / "total of <N> ddr error(s) detected and corrected over <N> seconds" (bucket shared by several event kinds); event_hash_14 is above the anomaly average (20.6 vs 9.36): more events like "<N> ddr errors(s) detected and corrected on rank <N>, symbol <N>, bit <N>" / "debug wait enable.................<N>" (bucket shared by several event kinds). The sessions nearest its centre are dominated by: "CE sym <N>, at <HEX>, mask <HEX>" (11.1/session), "<N> ddr errors(s) detected and corrected on rank <N>, symbol <N>, bit <N>" (7.7/session), "total of <N> ddr error(s) detected and corrected" (6.3/session). Profile: mean events 383.4 (anomaly avg 584.6); mean duration 86 (anomaly avg 99) s; share of failure-keyword messages 33.7% (anomaly avg 56.2%); mean hosts 177.8 (anomaly avg 281.4).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| n_event_buckets | 20.08 | 9.011 | 3.838 | +1.17 |
| event_hash_16 | 4.261 | 1.715 | 1.441 | +1.03 |
| event_entropy | 3.003 | 1.469 | 0.9276 | +1.00 |
| event_hash_11 | 2.975 | 6.316 | 4.397 | +0.91 |
| event_hash_14 | 20.58 | 9.363 | 4.847 | +0.88 |

Test-period sessions nearest this cluster: 37 anomalous, 226 normal.

Example session `window_3757252` (46 events):

    FATAL machine check interrupt
    FATAL instruction address: 0x0012a1ec
    FATAL machine check status register: 0x81000000
    FATAL summary...........................1
    FATAL instruction plb error.............0
    FATAL data read plb error...............0
    FATAL data write plb error..............0
    FATAL tlb error.........................0

Example session `window_3767578` (87 events):

    FATAL machine check interrupt
    FATAL instruction address: 0x00017600
    FATAL machine check status register: 0x81000000
    FATAL summary...........................1
    FATAL instruction plb error.............0
    FATAL data read plb error...............0
    FATAL data write plb error..............0
    FATAL tlb error.........................0

## Cluster 6 - 180 sessions (21.7%)

Cluster 6 holds 21.7% of the clustered anomalies. Compared with the overall anomaly population, its members show: n_hosts is above the anomaly average (782 vs 281): more hosts than usual; events_per_min is above the anomaly average (294 vs 157): dense bursts of events; transition_change_ratio is below the anomaly average (0.0395 vs 0.353): the same event kind repeated; event_entropy is below the anomaly average (0.269 vs 1.47): dominated by one event kind; n_events is above the anomaly average (924 vs 585): more events than a typical anomaly (repeated or retried operations). The sessions nearest its centre are dominated by: "Lustre mount FAILED : bglio<N> : point <PATH>" (98.8/session), "ciod: Error reading message prefix after LOAD_MESSAGE on CioStream socket to <IP>: Link has been severed" (44.0/session), "ciod: Error reading message prefix after LOAD_MESSAGE on CioStream socket to <IP>: Connection reset by peer" (0.1/session). Profile: mean events 924.3 (anomaly avg 584.6); mean duration 88 (anomaly avg 99) s; share of failure-keyword messages 68.6% (anomaly avg 56.2%); mean hosts 782.1 (anomaly avg 281.4).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| n_hosts | 782.1 | 281.4 | 189.8 | +1.25 |
| events_per_min | 294.5 | 156.9 | 89.76 | +0.84 |
| transition_change_ratio | 0.03945 | 0.353 | 0.3473 | -0.84 |
| event_entropy | 0.2686 | 1.469 | 0.9276 | -0.80 |
| n_events | 924.3 | 584.6 | 355.2 | +0.72 |

Test-period sessions nearest this cluster: 70 anomalous, 286 normal.

Example session `window_3749904` (113 events):

    FATAL ciod: Error reading message prefix after LOAD_MESSAGE on CioStream socket to 172.16.96.116:39516: Link has been severed
    FATAL ciod: Error reading message prefix after LOAD_MESSAGE on CioStream socket to 172.16.96.116:39517: Link has been severed
    FATAL ciod: Error reading message prefix after LOAD_MESSAGE on CioStream socket to 172.16.96.116:39736: Link has been severed
    FATAL ciod: Error reading message prefix after LOAD_MESSAGE on CioStream socket to 172.16.96.116:39737: Link has been severed
    FATAL ciod: Error reading message prefix after LOAD_MESSAGE on CioStream socket to 172.16.96.116:39486: Link has been severed
    FATAL ciod: Error reading message prefix after LOAD_MESSAGE on CioStream socket to 172.16.96.116:39352: Link has been severed
    FATAL ciod: Error reading message prefix after LOAD_MESSAGE on CioStream socket to 172.16.96.116:39353: Link has been severed
    FATAL ciod: Error reading message prefix after LOAD_MESSAGE on CioStream socket to 172.16.96.116:39738: Link has been severed

Example session `window_3755465` (50 events):

    FATAL Lustre mount FAILED : bglio143 : point /p/gb1
    FATAL Lustre mount FAILED : bglio144 : point /p/gb1
    FATAL Lustre mount FAILED : bglio141 : point /p/gb1
    FATAL Lustre mount FAILED : bglio142 : point /p/gb1
    FATAL Lustre mount FAILED : bglio135 : point /p/gb1
    FATAL Lustre mount FAILED : bglio136 : point /p/gb1
    FATAL Lustre mount FAILED : bglio133 : point /p/gb1
    FATAL Lustre mount FAILED : bglio134 : point /p/gb1
