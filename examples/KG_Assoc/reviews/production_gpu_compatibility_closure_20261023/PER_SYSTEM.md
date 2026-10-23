# Per-system independent findings

All rows reproduce the original numerical receipt exactly. Each has100 thermo rows,100k every-step stress samples,116 correct lag/count rows and1000 chemistry sweeps.

| System / replica | Absolute interval | C / B | Bonds initial → final | G(0) | Numerical replay |
|---|---|---:|---:|---:|---|
| F03_N010_RP080_EE08_EA04 r001 | 8,000,000 → 8,100,000 | 1343 / 1359 | 1350 → 1334 | 65.26757 | PASS |
| F04_N010_RP020_EE08_EA04 r001 | 6,000,000 → 6,100,000 | 1453 / 1476 | 1596 → 1573 | 37.20279 | PASS |
| F04_N010_RP040_EE08_EA04 r001 | 8,000,000 → 8,100,000 | 1567 / 1563 | 1711 → 1715 | 46.70721 | PASS |
| F04_N010_RP060_EE08_EA04 r001 | 6,000,000 → 6,100,000 | 1736 / 1741 | 1770 → 1765 | 56.64788 | PASS |
| F04_N010_RP080_EE04_EA04 r001 | 2,000,000 → 2,100,000 | 23789 / 23810 | 913 → 892 | 65.67733 | PASS |
| F04_N010_RP080_EE06_EA04 r001 | 4,000,000 → 4,100,000 | 8395 / 8366 | 1484 → 1513 | 66.22072 | PASS |
| F04_N010_RP080_EE08_EA04 r001 | 8,000,000 → 8,100,000 | 1881 / 1874 | 1783 → 1790 | 66.24541 | PASS |
| F04_N010_RP080_EE08_EA06 r001 | 24,000,000 → 24,100,000 | 258 / 271 | 1805 → 1792 | 65.86688 | PASS |
| F04_N010_RP080_EE08_EA08 r001 | 48,000,000 → 48,100,000 | 35 / 45 | 1802 → 1792 | 66.55908 | PASS |
| F04_N010_RP080_EE08_EA10 r003 | 88,000,000 → 88,100,000 | 2 / 6 | 1804 → 1800 | 66.33099 | PASS |
| F04_N010_RP080_EE10_EA04 r001 | 12,000,000 → 12,100,000 | 323 / 319 | 1926 → 1930 | 66.87595 | PASS |
| F04_N010_RP080_EE12_EA04 r001 | 20,000,000 → 20,100,000 | 60 / 56 | 1971 → 1975 | 66.99719 | PASS |
| F04_N020_RP080_EE08_EA04 r001 | 6,000,000 → 6,100,000 | 1674 / 1653 | 1694 → 1715 | 65.68086 | PASS |
| F04_N040_RP080_EE08_EA04 r001 | 8,000,000 → 8,100,000 | 1647 / 1651 | 1605 → 1601 | 65.65668 | PASS |
| F06_N010_RP080_EE08_EA04 r001 | 6,000,000 → 6,100,000 | 2738 / 2736 | 2670 → 2672 | 65.86117 | PASS |

Exact parent/seed/executable/final-state/receipt identities and numeric ranges are in replay/PER_SYSTEM.csv.
Production initial GPU readback and its independent runtime oracle remain **not demonstrated** for every row.
