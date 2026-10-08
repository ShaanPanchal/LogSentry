# HDFS anomaly clusters

KMeans (signed-log + standardised features, labels excluded). Clustered: development-period anomalies only (n=11,494); k=6 chosen by silhouette among k>=3.

## Cluster 0 - 2,487 sessions (21.6%)

Cluster 0 holds 21.6% of the clustered anomalies. Compared with the overall anomaly population, its members show: transition_change_ratio is above the anomaly average (1 vs 0.756): frequent switching between event kinds; event_hash_19 is below the anomaly average (0 vs 2.09): fewer events like "Deleting block <BLOCK> file <PATH>" / "writeBlock <BLOCK> received exception java.io.IOException: Could not read from stream"; event_hash_15 is below the anomaly average (1 vs 2.57): fewer events like "Receiving block <BLOCK> src: <PATH> dest: <PATH>" / "PacketResponder <N> for block <BLOCK> Interrupted."; event_entropy is below the anomaly average (1 vs 2.25): dominated by one event kind; n_event_buckets is below the anomaly average (2 vs 6.18): only a few kinds of event. The sessions nearest its centre are dominated by: "Receiving block <BLOCK> src: <PATH> dest: <PATH>" (1.0/session), "BLOCK* NameSystem.allocateBlock: <PATH> <BLOCK>" (1.0/session). Profile: write chain complete in 0% (anomaly avg 55%) of sessions; mean events 2.0 (anomaly avg 16.1); mean duration 0 (anomaly avg 17,417) s; share of failure-keyword messages 0.0% (anomaly avg 9.3%); mean hosts 1.0 (anomaly avg 3.1).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| transition_change_ratio | 1 | 0.7556 | 0.6162 | +1.60 |
| event_hash_19 | 0 | 2.092 | 2.682 | -1.56 |
| event_hash_15 | 1 | 2.572 | 2.986 | -1.56 |
| event_entropy | 1 | 2.247 | 2.833 | -1.45 |
| n_event_buckets | 2 | 6.183 | 7.79 | -1.35 |

Test-period sessions nearest this cluster: 464 anomalous, 78 normal.

Example session `blk_-5087939924532795057` (2 events):

    INFO  Receiving block blk_-5087939924532795057 src: /10.251.202.181:49239 dest: /10.251.202.181:50010
    INFO  BLOCK* NameSystem.allocateBlock: /user/root/rand/_temporary/_task_200811092030_0001_m_000028_0/part-00028. blk_-50879399

Example session `blk_8902542273035012990` (2 events):

    INFO  Receiving block blk_8902542273035012990 src: /10.251.70.37:44632 dest: /10.251.70.37:50010
    INFO  BLOCK* NameSystem.allocateBlock: /user/root/rand6/_temporary/_task_200811101024_0013_m_001552_0/part-01552. blk_89025422

## Cluster 1 - 4,565 sessions (39.7%)

Cluster 1 holds 39.7% of the clustered anomalies. Compared with the overall anomaly population, its members show: unacked_writes is below the anomaly average (0.000438 vs 0.912): few or no unacknowledged writes (acknowledgements keep up with writes); lifecycle_complete is above the anomaly average (1 vs 0.55): the full write chain completed; has_delete is above the anomaly average (0.987 vs 0.545): the block was deleted (lifecycle ran to the end); event_hash_27 is above the anomaly average (2.95 vs 1.65): more events like "BLOCK* NameSystem.delete: <BLOCK> is added to invalidSet of <IP>"; gap_max_s is above the anomaly average (1.96e+04 vs 1.07e+04): at least one long stall mid-session. The sessions nearest its centre are dominated by: "Receiving block <BLOCK> src: <PATH> dest: <PATH>" (3.0/session), "PacketResponder <N> for block <BLOCK> terminating" (3.0/session), "Received block <BLOCK> of size <N> from <PATH>" (3.0/session). Profile: write chain complete in 100% (anomaly avg 55%) of sessions; mean events 23.6 (anomaly avg 16.1); mean duration 28,819 (anomaly avg 17,417) s; share of failure-keyword messages 7.0% (anomaly avg 9.3%); mean hosts 4.1 (anomaly avg 3.1).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| unacked_writes | 0.0004381 | 0.9122 | 0.03396 | -1.16 |
| lifecycle_complete | 1 | 0.55 | 0.984 | +0.90 |
| has_delete | 0.9873 | 0.5449 | 0.8889 | +0.89 |
| event_hash_27 | 2.955 | 1.653 | 2.665 | +0.87 |
| gap_max_s | 1.958e+04 | 1.071e+04 | 1.642e+04 | +0.85 |

Test-period sessions nearest this cluster: 416 anomalous, 58,396 normal.

Example session `blk_8890233040985796680` (22 events):

    INFO  Receiving block blk_8890233040985796680 src: /10.251.199.150:35996 dest: /10.251.199.150:50010
    INFO  BLOCK* NameSystem.allocateBlock: /user/root/randtxt2/_temporary/_task_200811101024_0002_m_001656_0/part-01656. blk_88902
    INFO  Receiving block blk_8890233040985796680 src: /10.251.123.20:57174 dest: /10.251.123.20:50010
    INFO  Receiving block blk_8890233040985796680 src: /10.251.199.150:46287 dest: /10.251.199.150:50010
    INFO  PacketResponder 0 for block blk_8890233040985796680 terminating
    INFO  Received block blk_8890233040985796680 of size 28501363 from /10.251.123.20
    INFO  PacketResponder 2 for block blk_8890233040985796680 terminating
    INFO  Received block blk_8890233040985796680 of size 28501363 from /10.251.199.150

Example session `blk_7370836319212068210` (23 events):

    INFO  Receiving block blk_7370836319212068210 src: /10.251.75.49:45857 dest: /10.251.75.49:50010
    INFO  Receiving block blk_7370836319212068210 src: /10.251.123.20:49258 dest: /10.251.123.20:50010
    INFO  Receiving block blk_7370836319212068210 src: /10.251.123.20:49898 dest: /10.251.123.20:50010
    INFO  BLOCK* NameSystem.allocateBlock: /user/root/randtxt2/_temporary/_task_200811101024_0002_m_001982_0/part-01982. blk_73708
    INFO  PacketResponder 0 for block blk_7370836319212068210 terminating
    INFO  Received block blk_7370836319212068210 of size 67108864 from /10.251.75.49
    INFO  PacketResponder 1 for block blk_7370836319212068210 terminating
    INFO  Received block blk_7370836319212068210 of size 67108864 from /10.251.123.20

## Cluster 2 - 2,686 sessions (23.4%)

Cluster 2 holds 23.4% of the clustered anomalies. Compared with the overall anomaly population, its members show: keyword_error_ratio is above the anomaly average (0.252 vs 0.0934): many failure messages; events_per_min is above the anomaly average (3.75 vs 1.55): dense bursts of events; unacked_writes is above the anomaly average (1.99 vs 0.912): writes started but never acknowledged; lifecycle_complete is below the anomaly average (0.000372 vs 0.55): the write chain did not complete; has_delete is below the anomaly average (0 vs 0.545): no deletion event (lifecycle did not reach the end). The sessions nearest its centre are dominated by: "Receiving block <BLOCK> src: <PATH> dest: <PATH>" (2.0/session), "BLOCK* NameSystem.allocateBlock: <PATH> <BLOCK>" (1.0/session), "writeBlock <BLOCK> received exception java.io.IOException: Could not read from stream" (1.0/session). Profile: write chain complete in 0% (anomaly avg 55%) of sessions; mean events 4.1 (anomaly avg 16.1); mean duration 8 (anomaly avg 17,417) s; share of failure-keyword messages 25.2% (anomaly avg 9.3%); mean hosts 1.0 (anomaly avg 3.1).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| keyword_error_ratio | 0.2521 | 0.09336 | 0.04315 | +1.56 |
| events_per_min | 3.746 | 1.548 | 1.1 | +1.27 |
| unacked_writes | 1.987 | 0.9122 | 0.03396 | +1.17 |
| lifecycle_complete | 0.0003723 | 0.55 | 0.984 | -1.10 |
| has_delete | 0 | 0.5449 | 0.8889 | -1.09 |

Test-period sessions nearest this cluster: 654 anomalous, 54,376 normal.

Example session `blk_-6693753286275562803` (4 events):

    INFO  Receiving block blk_-6693753286275562803 src: /10.251.202.181:39671 dest: /10.251.202.181:50010
    INFO  Receiving block blk_-6693753286275562803 src: /10.251.202.181:37173 dest: /10.251.202.181:50010
    INFO  BLOCK* NameSystem.allocateBlock: /user/root/rand6/_temporary/_task_200811101024_0013_m_001305_0/part-01305. blk_-6693753
    INFO  writeBlock blk_-6693753286275562803 received exception java.io.IOException: Could not read from stream

Example session `blk_8580160985690428930` (4 events):

    INFO  Receiving block blk_8580160985690428930 src: /10.251.42.207:41297 dest: /10.251.42.207:50010
    INFO  Receiving block blk_8580160985690428930 src: /10.251.42.207:49326 dest: /10.251.42.207:50010
    INFO  BLOCK* NameSystem.allocateBlock: /user/root/rand6/_temporary/_task_200811101024_0013_m_000965_0/part-00965. blk_85801609
    INFO  writeBlock blk_8580160985690428930 received exception java.io.IOException: Could not read from stream

## Cluster 3 - 1,732 sessions (15.1%)

Cluster 3 holds 15.1% of the clustered anomalies. Compared with the overall anomaly population, its members show: event_hash_26 is above the anomaly average (1.51 vs 0.23): more events like "Received block <BLOCK> src: <PATH> dest: <PATH> of size <N>" / "writeBlock <BLOCK> received exception java.net.NoRouteToHostException: No route to host"; uncommitted_acks is below the anomaly average (-2.5 vs -0.478): more stored confirmations than acknowledgements; replica_deficit is below the anomaly average (-2.5 vs 0.867): more confirmations than expected (duplicate or re-replicated copies); event_hash_15 is above the anomaly average (4.51 vs 2.57): more events like "Receiving block <BLOCK> src: <PATH> dest: <PATH>" / "PacketResponder <N> for block <BLOCK> Interrupted."; n_hosts is above the anomaly average (6.29 vs 3.05): more hosts than usual (extra replicas or retries on other nodes). The sessions nearest its centre are dominated by: "BLOCK* NameSystem.addStoredBlock: blockMap updated: <IP> is added to <BLOCK> size <N>" (6.8/session), "Receiving block <BLOCK> src: <PATH> dest: <PATH>" (4.9/session), "Deleting block <BLOCK> file <PATH>" (4.9/session). Profile: write chain complete in 100% (anomaly avg 55%) of sessions; mean events 35.2 (anomaly avg 16.1); mean duration 39,279 (anomaly avg 17,417) s; share of failure-keyword messages 4.3% (anomaly avg 9.3%); mean hosts 6.3 (anomaly avg 3.1).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| event_hash_26 | 1.507 | 0.2295 | 0.009736 | +2.29 |
| uncommitted_acks | -2.496 | -0.478 | -0.01938 | -1.91 |
| replica_deficit | -2.496 | 0.8665 | 0.02832 | -1.52 |
| event_hash_15 | 4.508 | 2.572 | 2.986 | +1.44 |
| n_hosts | 6.287 | 3.05 | 3.973 | +1.27 |

Test-period sessions nearest this cluster: 146 anomalous, 488 normal.

Example session `blk_7221246348217161430` (31 events):

    INFO  BLOCK* NameSystem.allocateBlock: /user/root/rand/_temporary/_task_200811101024_0001_m_000173_0/part-00173. blk_722124634
    INFO  Receiving block blk_7221246348217161430 src: /10.251.39.160:42961 dest: /10.251.39.160:50010
    INFO  Receiving block blk_7221246348217161430 src: /10.251.39.160:53102 dest: /10.251.39.160:50010
    INFO  Receiving block blk_7221246348217161430 src: /10.251.109.236:53602 dest: /10.251.109.236:50010
    INFO  PacketResponder 0 for block blk_7221246348217161430 terminating
    INFO  Received block blk_7221246348217161430 of size 67108864 from /10.251.109.236
    INFO  BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.109.236:50010 is added to blk_7221246348217161430 size 671088
    INFO  PacketResponder 1 for block blk_7221246348217161430 terminating

Example session `blk_7342022561458178142` (38 events):

    INFO  Receiving block blk_7342022561458178142 src: /10.251.27.63:38521 dest: /10.251.27.63:50010
    INFO  Receiving block blk_7342022561458178142 src: /10.251.27.63:41931 dest: /10.251.27.63:50010
    INFO  BLOCK* NameSystem.allocateBlock: /user/root/randtxt2/_temporary/_task_200811101024_0002_m_001902_0/part-01902. blk_73420
    INFO  Receiving block blk_7342022561458178142 src: /10.251.90.134:44005 dest: /10.251.90.134:50010
    INFO  PacketResponder 1 for block blk_7342022561458178142 terminating
    INFO  Received block blk_7342022561458178142 of size 28493428 from /10.251.27.63
    INFO  PacketResponder 2 for block blk_7342022561458178142 terminating
    INFO  Received block blk_7342022561458178142 of size 28493428 from /10.251.27.63

## Cluster 4 - 16 sessions (0.1%)

Cluster 4 holds 0.1% of the clustered anomalies. Compared with the overall anomaly population, its members show: event_hash_24 is above the anomaly average (2.56 vs 0.00357): more events like "Changing block file offset of block <BLOCK> from <N> to <N> meta file offset to <N>" / "<IP>:Exception writing block <BLOCK> to mirror <IP>" (bucket shared by several event kinds); event_hash_18 is above the anomaly average (1.12 vs 0.00157): more events like "PacketResponder <BLOCK> <N> Exception java.net.SocketTimeoutException: <N> millis timeout while waiting for channel to be ready for read. ch : java.nio.channels.SocketChannel[connected local=<PATH> remote=<PATH>" / "Exception in receiveBlock for block <BLOCK> java.io.InterruptedIOException: Interruped while waiting for IO on channel java.nio.channels.SocketChannel[connected local=<PATH> remote=<PATH> <N> millis timeout left." (bucket shared by several event kinds); event_hash_07 is above the anomaly average (1.81 vs 0.00444): more events like "Exception in receiveBlock for block <BLOCK> java.io.IOException: Connection reset by peer"; event_hash_30 is above the anomaly average (0.25 vs 0.000348): more events like "writeBlock <BLOCK> received exception java.io.InterruptedIOException: Interruped while waiting for IO on channel java.nio.channels.SocketChannel[connected local=<PATH> remote=<PATH> <N> millis timeout left."; event_hash_03 is above the anomaly average (0.188 vs 0.000261): more events like "PacketResponder <BLOCK> <N> Exception java.io.IOException: Connection reset by peer". The sessions nearest its centre are dominated by: "Receiving block <BLOCK> src: <PATH> dest: <PATH>" (6.8/session), "PacketResponder <N> for block <BLOCK> terminating" (3.7/session), "BLOCK* NameSystem.addStoredBlock: blockMap updated: <IP> is added to <BLOCK> size <N>" (3.1/session). Profile: write chain complete in 100% (anomaly avg 55%) of sessions; mean events 39.9 (anomaly avg 16.1); mean duration 15,734 (anomaly avg 17,417) s; share of failure-keyword messages 22.2% (anomaly avg 9.3%); mean hosts 5.2 (anomaly avg 3.1).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| event_hash_24 | 2.562 | 0.003567 | 0.0001266 | +26.55 |
| event_hash_18 | 1.125 | 0.001566 | 5.556e-05 | +23.28 |
| event_hash_07 | 1.812 | 0.004437 | 0.0001574 | +20.66 |
| event_hash_30 | 0.25 | 0.000348 | 1.235e-05 | +13.38 |
| event_hash_03 | 0.1875 | 0.000261 | 9.26e-06 | +11.59 |

Test-period sessions nearest this cluster: 0 anomalous, 0 normal.

Example session `blk_-4380884313697280861` (36 events):

    INFO  Receiving block blk_-4380884313697280861 src: /10.251.193.224:46827 dest: /10.251.193.224:50010
    INFO  Receiving block blk_-4380884313697280861 src: /10.251.193.224:58661 dest: /10.251.193.224:50010
    INFO  Receiving block blk_-4380884313697280861 src: /10.251.107.50:40367 dest: /10.251.107.50:50010
    INFO  BLOCK* NameSystem.allocateBlock: /user/root/rand4/_temporary/_task_200811101024_0009_m_001708_1/part-01708. blk_-4380884
    INFO  PacketResponder 1 for block blk_-4380884313697280861 terminating
    INFO  PacketResponder blk_-4380884313697280861 1 Exception java.net.SocketTimeoutException: 60000 millis timeout while waiting
    INFO  PacketResponder 2 for block blk_-4380884313697280861 terminating
    INFO  10.251.107.50:50010:Exception writing block blk_-4380884313697280861 to mirror 10.251.30.85:50010

Example session `blk_-3126359724254586349` (34 events):

    INFO  Receiving block blk_-3126359724254586349 src: /10.250.17.177:58651 dest: /10.250.17.177:50010
    INFO  Receiving block blk_-3126359724254586349 src: /10.250.17.177:48401 dest: /10.250.17.177:50010
    INFO  BLOCK* NameSystem.allocateBlock: /user/root/rand4/_temporary/_task_200811101024_0009_m_001807_0/part-01807. blk_-3126359
    INFO  Receiving block blk_-3126359724254586349 src: /10.251.30.85:54392 dest: /10.251.30.85:50010
    INFO  PacketResponder 2 for block blk_-3126359724254586349 terminating
    INFO  PacketResponder blk_-3126359724254586349 2 Exception java.net.SocketTimeoutException: 120000 millis timeout while waitin
    INFO  Exception in receiveBlock for block blk_-3126359724254586349 java.io.IOException: Connection reset by peer
    INFO  writeBlock blk_-3126359724254586349 received exception java.io.IOException: Connection reset by peer

## Cluster 5 - 8 sessions (0.1%)

Cluster 5 holds 0.1% of the clustered anomalies. Compared with the overall anomaly population, its members show: event_hash_20 is above the anomaly average (1 vs 0.000783): more events like "<IP>:Failed to transfer <BLOCK> to <IP> got java.io.IOException: Connection reset by peer" / "PacketResponder <BLOCK> <N> Exception java.io.InterruptedIOException: Interruped while waiting for IO on channel java.nio.channels.SocketChannel[closed]. <N> millis timeout left." (bucket shared by several event kinds); event_hash_13 is above the anomaly average (1 vs 0.00087): more events like "writeBlock <BLOCK> received exception java.io.IOException: Block <BLOCK> is valid, and cannot be written to." / "writeBlock <BLOCK> received exception java.net.SocketTimeoutException: <N> millis timeout while waiting for channel to be ready for write. ch : java.nio.channels.SocketChannel[connected local=<PATH> remote=<PATH>" (bucket shared by several event kinds); event_hash_10 is above the anomaly average (1.38 vs 0.253): more events like "Verification succeeded for <BLOCK>" / "PacketResponder <BLOCK> <N> Exception java.io.EOFException"; n_event_buckets is above the anomaly average (11.1 vs 6.18): a wider variety of event kinds; event_hash_15 is above the anomaly average (4 vs 2.57): more events like "Receiving block <BLOCK> src: <PATH> dest: <PATH>" / "PacketResponder <N> for block <BLOCK> Interrupted.". The sessions nearest its centre are dominated by: "Receiving block <BLOCK> src: <PATH> dest: <PATH>" (4.0/session), "PacketResponder <N> for block <BLOCK> terminating" (3.0/session), "Received block <BLOCK> of size <N> from <PATH>" (3.0/session). Profile: write chain complete in 100% (anomaly avg 55%) of sessions; mean events 28.1 (anomaly avg 16.1); mean duration 41,503 (anomaly avg 17,417) s; share of failure-keyword messages 12.2% (anomaly avg 9.3%); mean hosts 4.0 (anomaly avg 3.1).

| feature | cluster mean | anomaly mean | all-sessions mean | z |
|---|---|---|---|---|
| event_hash_20 | 1 | 0.000783 | 2.778e-05 | +35.72 |
| event_hash_13 | 1 | 0.00087 | 3.087e-05 | +33.89 |
| event_hash_10 | 1.375 | 0.2533 | 0.3244 | +1.46 |
| n_event_buckets | 11.12 | 6.183 | 7.79 | +1.21 |
| event_hash_15 | 4 | 2.572 | 2.986 | +1.16 |

Test-period sessions nearest this cluster: 0 anomalous, 0 normal.

Example session `blk_-8122638974387556519` (27 events):

    INFO  BLOCK* NameSystem.allocateBlock: /user/root/randtxt2/_temporary/_task_200811101024_0002_m_000430_0/part-00430. blk_-8122
    INFO  Receiving block blk_-8122638974387556519 src: /10.250.7.96:36923 dest: /10.250.7.96:50010
    INFO  Receiving block blk_-8122638974387556519 src: /10.250.10.176:47593 dest: /10.250.10.176:50010
    INFO  Receiving block blk_-8122638974387556519 src: /10.250.10.176:34232 dest: /10.250.10.176:50010
    INFO  PacketResponder 0 for block blk_-8122638974387556519 terminating
    INFO  Received block blk_-8122638974387556519 of size 28497677 from /10.250.7.96
    INFO  BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.195.52:50010 is added to blk_-8122638974387556519 size 284976
    INFO  PacketResponder 2 for block blk_-8122638974387556519 terminating

Example session `blk_7162246307091465257` (27 events):

    INFO  BLOCK* NameSystem.allocateBlock: /user/root/rand/_temporary/_task_200811101024_0001_m_000112_0/part-00112. blk_716224630
    INFO  Receiving block blk_7162246307091465257 src: /10.251.214.67:55715 dest: /10.251.214.67:50010
    INFO  Receiving block blk_7162246307091465257 src: /10.251.214.67:40621 dest: /10.251.214.67:50010
    INFO  Receiving block blk_7162246307091465257 src: /10.251.123.132:49772 dest: /10.251.123.132:50010
    INFO  BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.214.67:50010 is added to blk_7162246307091465257 size 3536846
    INFO  BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.123.132:50010 is added to blk_7162246307091465257 size 353684
    INFO  PacketResponder 1 for block blk_7162246307091465257 terminating
    INFO  Received block blk_7162246307091465257 of size 3536846 from /10.251.214.67
