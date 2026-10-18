# Nine-replica diagnostics

IAT estimates are descriptive under local stationarity; unresolved flags are not an automatic acceptance threshold. Bond count = 2000 × bound fraction; free stickers = 4000 × (1 − bound fraction), including exact affine transformations of their statistics.

## Ea6 r001

Parent family r001; 8M → 24M; 32 validated 500k windows.
Accepted creations/breaks 46111/46089; neighbor gains/losses 41810/41768.
Initial → final bonds 1783 → 1805; intra 100 → 79; inter 1683 → 1726.
Never-broken original bonds 0/1783; never-lost original neighbor edges 0/1643.
Stars with a reaction/gained neighbor/lost neighbor: 1000/1000/1000 of 1000.
Initial isolated IDs [143, 526, 595, 950]; final isolated IDs [484].
Isolation visits (including zero-duration episodes) by 350 stars (zero-duration visits remain separately archived); 128 stars return after a nonzero gap.

| Observable | 8–12M | 12–16M | 16–20M | 20–24M |
|---|---:|---:|---:|---:|
| bonds | 1794.6 | 1794.8 | 1791.2 | 1792.6 |
| intra | 88.092 | 90.734 | 97.89 | 91.415 |
| inter | 1706.5 | 1704.1 | 1693.3 | 1701.2 |
| L1 | 39.117 | 36.227 | 40.602 | 37.613 |
| L2 | 32.188 | 36.276 | 30.154 | 34.636 |
| mean_degree | 3.3351 | 3.3359 | 3.306 | 3.3283 |
| largest_cluster_fraction | 0.99773 | 0.99793 | 0.99772 | 0.99769 |
| isolated_stars | 2.1473 | 1.9212 | 2.0398 | 2.143 |
| mean_rg2 | 7.0492 | 7.0278 | 7.0137 | 7.0139 |
| mean_center_terminal_r2 | 15.929 | 15.874 | 15.837 | 15.821 |

| Last-quarter observable | Mean | IAT steps | ESS | SEM | 5/10/20-block SEM | Unresolved |
|---|---:|---:|---:|---:|---|---|
| bound_fraction | 0.896311 | 91536 | 21.85 | 0.0009654 | 0.001106/0.0007564/0.0006013 | False |
| intra | 91.4153 | 200362 | 9.98 | 1.701 | 1.992/1.46/1.126 | True |
| L1 | 37.6133 | 322729 | 6.2 | 2.177 | 1.941/1.556/1.137 | True |
| L2 | 34.6362 | 230458 | 8.68 | 1.862 | 1.702/1.473/1.081 | True |
| mean_degree | 3.32827 | 198267 | 10.09 | 0.00785 | 0.008123/0.005639/0.004506 | False |
| largest_cluster_fraction | 0.997686 | 62044 | 32.24 | 0.00026 | 0.0002622/0.0002105/0.0002262 | False |
| mean_rg2 | 7.01387 | 70279 | 28.46 | 0.008909 | 0.009503/0.007223/0.005713 | False |
| mean_center_terminal_r2 | 15.8208 | 71228 | 28.08 | 0.02639 | 0.02886/0.0214/0.01706 | False |

Initial/final full graph distributions (degree counts, intra-loop counts, inter-edge multiplicities and component sizes):

```json
{
  "initial": {
    "component_sizes": [
      996,
      1,
      1,
      1,
      1
    ],
    "distinct_degree": {
      "0": 4,
      "1": 33,
      "2": 142,
      "3": 315,
      "4": 506
    },
    "giant": 996,
    "inter": 1683,
    "intra": 100,
    "intra_loops": {
      "0": 903,
      "1": 94,
      "2": 3
    },
    "isolated_stars": [
      143,
      526,
      595,
      950
    ],
    "mean_degree": 3.286,
    "multiplicity": {
      "0": 497857,
      "1": 1603,
      "2": 40,
      "3": 0,
      "4": 0
    }
  },
  "final": {
    "component_sizes": [
      999,
      1
    ],
    "distinct_degree": {
      "0": 1,
      "1": 18,
      "2": 132,
      "3": 308,
      "4": 541
    },
    "giant": 999,
    "inter": 1726,
    "intra": 79,
    "intra_loops": {
      "0": 921,
      "1": 79
    },
    "isolated_stars": [
      484
    ],
    "mean_degree": 3.37,
    "multiplicity": {
      "0": 497815,
      "1": 1644,
      "2": 41,
      "3": 0,
      "4": 0
    }
  }
}
```

All identity-specific residence episodes, including left/right censoring and zero-duration same-sweep excursions, are in the replay archive. Largest component is a graph quantity, not a periodic-wrapping test.

## Ea6 r002

Parent family r002; 8M → 24M; 32 validated 500k windows.
Accepted creations/breaks 46090/46087; neighbor gains/losses 41814/41833.
Initial → final bonds 1787 → 1790; intra 85 → 107; inter 1702 → 1683.
Never-broken original bonds 0/1787; never-lost original neighbor edges 0/1665.
Stars with a reaction/gained neighbor/lost neighbor: 1000/1000/1000 of 1000.
Initial isolated IDs [272]; final isolated IDs [383].
Isolation visits (including zero-duration episodes) by 351 stars (zero-duration visits remain separately archived); 133 stars return after a nonzero gap.

| Observable | 8–12M | 12–16M | 16–20M | 20–24M |
|---|---:|---:|---:|---:|
| bonds | 1792.1 | 1794.6 | 1794 | 1791.6 |
| intra | 96.233 | 95.284 | 85.182 | 98.95 |
| inter | 1695.9 | 1699.3 | 1708.8 | 1692.7 |
| L1 | 38.119 | 36.292 | 37.711 | 41.852 |
| L2 | 33.391 | 32.181 | 33.064 | 29.814 |
| mean_degree | 3.3161 | 3.3269 | 3.3426 | 3.3023 |
| largest_cluster_fraction | 0.99742 | 0.99821 | 0.99824 | 0.9977 |
| isolated_stars | 2.189 | 1.6692 | 1.5077 | 2.0473 |
| mean_rg2 | 7.0186 | 7.057 | 7.0222 | 7.0189 |
| mean_center_terminal_r2 | 15.84 | 15.955 | 15.861 | 15.85 |

| Last-quarter observable | Mean | IAT steps | ESS | SEM | 5/10/20-block SEM | Unresolved |
|---|---:|---:|---:|---:|---|---|
| bound_fraction | 0.895812 | 30706 | 65.13 | 0.0005635 | 0.000436/0.0005188/0.0005392 | False |
| intra | 98.95 | 399629 | 5.0 | 3.009 | 2.959/2.024/1.428 | True |
| L1 | 41.8518 | 198451 | 10.08 | 2.086 | 1.735/1.786/1.41 | False |
| L2 | 29.8137 | 252644 | 7.92 | 1.662 | 1.438/1.277/0.9283 | True |
| mean_degree | 3.30234 | 164186 | 12.18 | 0.006873 | 0.007362/0.005295/0.004114 | False |
| largest_cluster_fraction | 0.997702 | 83889 | 23.84 | 0.0002989 | 0.0002032/0.0002807/0.0002174 | False |
| mean_rg2 | 7.01892 | 42735 | 46.8 | 0.007176 | 0.007572/0.006109/0.005124 | False |
| mean_center_terminal_r2 | 15.8505 | 21446 | 93.26 | 0.01412 | 0.01609/0.01446/0.01236 | False |

Initial/final full graph distributions (degree counts, intra-loop counts, inter-edge multiplicities and component sizes):

```json
{
  "initial": {
    "component_sizes": [
      999,
      1
    ],
    "distinct_degree": {
      "0": 1,
      "1": 23,
      "2": 131,
      "3": 335,
      "4": 510
    },
    "giant": 999,
    "inter": 1702,
    "intra": 85,
    "intra_loops": {
      "0": 915,
      "1": 85
    },
    "isolated_stars": [
      272
    ],
    "mean_degree": 3.33,
    "multiplicity": {
      "0": 497835,
      "1": 1628,
      "2": 37,
      "3": 0,
      "4": 0
    }
  },
  "final": {
    "component_sizes": [
      999,
      1
    ],
    "distinct_degree": {
      "0": 1,
      "1": 29,
      "2": 149,
      "3": 319,
      "4": 502
    },
    "giant": 999,
    "inter": 1683,
    "intra": 107,
    "intra_loops": {
      "0": 893,
      "1": 107
    },
    "isolated_stars": [
      383
    ],
    "mean_degree": 3.292,
    "multiplicity": {
      "0": 497854,
      "1": 1609,
      "2": 37,
      "3": 0,
      "4": 0
    }
  }
}
```

All identity-specific residence episodes, including left/right censoring and zero-duration same-sweep excursions, are in the replay archive. Largest component is a graph quantity, not a periodic-wrapping test.

## Ea6 r003

Parent family r003; 8M → 24M; 32 validated 500k windows.
Accepted creations/breaks 45688/45690; neighbor gains/losses 41432/41438.
Initial → final bonds 1803 → 1801; intra 84 → 88; inter 1719 → 1713.
Never-broken original bonds 0/1803; never-lost original neighbor edges 0/1674.
Stars with a reaction/gained neighbor/lost neighbor: 1000/1000/1000 of 1000.
Initial isolated IDs []; final isolated IDs [].
Isolation visits (including zero-duration episodes) by 335 stars (zero-duration visits remain separately archived); 108 stars return after a nonzero gap.

| Observable | 8–12M | 12–16M | 16–20M | 20–24M |
|---|---:|---:|---:|---:|
| bonds | 1792.9 | 1791.8 | 1793.8 | 1794.5 |
| intra | 86.43 | 80.558 | 92.206 | 89.885 |
| inter | 1706.5 | 1711.3 | 1701.6 | 1704.6 |
| L1 | 38.48 | 37.857 | 40.712 | 40.065 |
| L2 | 30.814 | 34.239 | 30.755 | 33.154 |
| mean_degree | 3.3369 | 3.3471 | 3.3218 | 3.3295 |
| largest_cluster_fraction | 0.99888 | 0.99861 | 0.99832 | 0.9979 |
| isolated_stars | 0.9255 | 1.3758 | 1.6358 | 1.8193 |
| mean_rg2 | 7.0297 | 7.0097 | 7.0253 | 7.0247 |
| mean_center_terminal_r2 | 15.889 | 15.838 | 15.868 | 15.852 |

| Last-quarter observable | Mean | IAT steps | ESS | SEM | 5/10/20-block SEM | Unresolved |
|---|---:|---:|---:|---:|---|---|
| bound_fraction | 0.897259 | 58220 | 34.35 | 0.0009045 | 0.0007564/0.0006625/0.0007165 | False |
| intra | 89.8847 | 282522 | 7.08 | 2.334 | 1.958/1.777/1.295 | True |
| L1 | 40.065 | 168818 | 11.85 | 1.34 | 1.208/1.078/0.9105 | False |
| L2 | 33.154 | 164033 | 12.19 | 1.391 | 1.214/1.161/0.9327 | False |
| mean_degree | 3.32947 | 55229 | 36.21 | 0.003352 | 0.003978/0.002692/0.002747 | False |
| largest_cluster_fraction | 0.997899 | 42979 | 46.53 | 0.0002037 | 0.0001098/0.0001384/0.0001816 | False |
| mean_rg2 | 7.02471 | 89301 | 22.4 | 0.01097 | 0.01114/0.008693/0.006276 | False |
| mean_center_terminal_r2 | 15.8518 | 154969 | 12.91 | 0.04222 | 0.03728/0.02667/0.01926 | False |

Initial/final full graph distributions (degree counts, intra-loop counts, inter-edge multiplicities and component sizes):

```json
{
  "initial": {
    "component_sizes": [
      1000
    ],
    "distinct_degree": {
      "1": 25,
      "2": 132,
      "3": 313,
      "4": 530
    },
    "giant": 1000,
    "inter": 1719,
    "intra": 84,
    "intra_loops": {
      "0": 916,
      "1": 84
    },
    "isolated_stars": [],
    "mean_degree": 3.348,
    "multiplicity": {
      "0": 497826,
      "1": 1631,
      "2": 41,
      "3": 2,
      "4": 0
    }
  },
  "final": {
    "component_sizes": [
      1000
    ],
    "distinct_degree": {
      "1": 23,
      "2": 126,
      "3": 343,
      "4": 508
    },
    "giant": 1000,
    "inter": 1713,
    "intra": 88,
    "intra_loops": {
      "0": 912,
      "1": 88
    },
    "isolated_stars": [],
    "mean_degree": 3.336,
    "multiplicity": {
      "0": 497832,
      "1": 1624,
      "2": 43,
      "3": 1,
      "4": 0
    }
  }
}
```

All identity-specific residence episodes, including left/right censoring and zero-duration same-sweep excursions, are in the replay archive. Largest component is a graph quantity, not a periodic-wrapping test.

## Ea8 r001

Parent family r001; 8M → 24M; 32 validated 500k windows.
Accepted creations/breaks 6401/6387; neighbor gains/losses 5784/5752.
Initial → final bonds 1783 → 1797; intra 100 → 82; inter 1683 → 1715.
Never-broken original bonds 47/1783; never-lost original neighbor edges 48/1643.
Stars with a reaction/gained neighbor/lost neighbor: 1000/1000/1000 of 1000.
Initial isolated IDs [143, 526, 595, 950]; final isolated IDs [502, 867, 921].
Isolation visits (including zero-duration episodes) by 59 stars (zero-duration visits remain separately archived); 10 stars return after a nonzero gap.

| Observable | 8–12M | 12–16M | 16–20M | 20–24M |
|---|---:|---:|---:|---:|
| bonds | 1790.1 | 1790.8 | 1797.3 | 1794.5 |
| intra | 92.767 | 90.7 | 99.344 | 87.463 |
| inter | 1697.3 | 1700.1 | 1697.9 | 1707.1 |
| L1 | 37.53 | 36.074 | 34.224 | 41.285 |
| L2 | 31.849 | 31.649 | 38.888 | 33.718 |
| mean_degree | 3.3198 | 3.3289 | 3.3277 | 3.3318 |
| largest_cluster_fraction | 0.99837 | 0.99856 | 0.9979 | 0.99761 |
| isolated_stars | 1.2125 | 1.1925 | 1.7495 | 2.3785 |
| mean_rg2 | 7.0204 | 7.0371 | 7.0557 | 7.0386 |
| mean_center_terminal_r2 | 15.858 | 15.897 | 15.948 | 15.91 |

| Last-quarter observable | Mean | IAT steps | ESS | SEM | 5/10/20-block SEM | Unresolved |
|---|---:|---:|---:|---:|---|---|
| bound_fraction | 0.897271 | 241573 | 8.28 | 0.002303 | 0.002545/0.001851/0.001424 | True |
| intra | 87.4633 | 647472 | 3.09 | 3.381 | 2.771/1.923/1.342 | True |
| L1 | 41.2855 | 458639 | 4.36 | 2.173 | 1.883/1.35/1.005 | True |
| L2 | 33.7182 | 609123 | 3.28 | 2.742 | 2.162/1.551/1.1 | True |
| mean_degree | 3.33184 | 266035 | 7.52 | 0.009886 | 0.0114/0.007859/0.005884 | True |
| largest_cluster_fraction | 0.997613 | 223635 | 8.94 | 0.0003248 | 0.0002668/0.0002645/0.0002 | True |
| mean_rg2 | 7.03856 | 9991 | 200.19 | 0.003029 | 0.003672/0.003278/0.002898 | False |
| mean_center_terminal_r2 | 15.9099 | 8691 | 230.11 | 0.008137 | 0.006591/0.007347/0.008076 | False |

Initial/final full graph distributions (degree counts, intra-loop counts, inter-edge multiplicities and component sizes):

```json
{
  "initial": {
    "component_sizes": [
      996,
      1,
      1,
      1,
      1
    ],
    "distinct_degree": {
      "0": 4,
      "1": 33,
      "2": 142,
      "3": 315,
      "4": 506
    },
    "giant": 996,
    "inter": 1683,
    "intra": 100,
    "intra_loops": {
      "0": 903,
      "1": 94,
      "2": 3
    },
    "isolated_stars": [
      143,
      526,
      595,
      950
    ],
    "mean_degree": 3.286,
    "multiplicity": {
      "0": 497857,
      "1": 1603,
      "2": 40,
      "3": 0,
      "4": 0
    }
  },
  "final": {
    "component_sizes": [
      997,
      1,
      1,
      1
    ],
    "distinct_degree": {
      "0": 3,
      "1": 25,
      "2": 124,
      "3": 315,
      "4": 533
    },
    "giant": 997,
    "inter": 1715,
    "intra": 82,
    "intra_loops": {
      "0": 920,
      "1": 78,
      "2": 2
    },
    "isolated_stars": [
      502,
      867,
      921
    ],
    "mean_degree": 3.35,
    "multiplicity": {
      "0": 497825,
      "1": 1635,
      "2": 40,
      "3": 0,
      "4": 0
    }
  }
}
```

All identity-specific residence episodes, including left/right censoring and zero-duration same-sweep excursions, are in the replay archive. Largest component is a graph quantity, not a periodic-wrapping test.

## Ea8 r002

Parent family r002; 8M → 24M; 32 validated 500k windows.
Accepted creations/breaks 6379/6389; neighbor gains/losses 5828/5815.
Initial → final bonds 1787 → 1777; intra 85 → 64; inter 1702 → 1713.
Never-broken original bonds 59/1787; never-lost original neighbor edges 65/1665.
Stars with a reaction/gained neighbor/lost neighbor: 1000/1000/1000 of 1000.
Initial isolated IDs [272]; final isolated IDs [685, 764].
Isolation visits (including zero-duration episodes) by 56 stars (zero-duration visits remain separately archived); 7 stars return after a nonzero gap.

| Observable | 8–12M | 12–16M | 16–20M | 20–24M |
|---|---:|---:|---:|---:|
| bonds | 1792.8 | 1793.9 | 1801.4 | 1791.7 |
| intra | 85.635 | 75.839 | 74.019 | 70.586 |
| inter | 1707.2 | 1718.1 | 1727.4 | 1721.1 |
| L1 | 37.604 | 42.111 | 34.706 | 37.611 |
| L2 | 38.078 | 42.334 | 28.485 | 29.773 |
| mean_degree | 3.3396 | 3.3532 | 3.3854 | 3.3676 |
| largest_cluster_fraction | 0.9985 | 0.99892 | 0.99932 | 0.99885 |
| isolated_stars | 1.3525 | 1.0393 | 0.475 | 0.7445 |
| mean_rg2 | 6.9841 | 7.004 | 7.0443 | 7.0583 |
| mean_center_terminal_r2 | 15.756 | 15.804 | 15.916 | 15.953 |

| Last-quarter observable | Mean | IAT steps | ESS | SEM | 5/10/20-block SEM | Unresolved |
|---|---:|---:|---:|---:|---|---|
| bound_fraction | 0.895868 | 161455 | 12.39 | 0.001584 | 0.001683/0.001476/0.001155 | False |
| intra | 70.5858 | 238909 | 8.37 | 1.005 | 1.143/0.8244/0.6324 | True |
| L1 | 37.6112 | 158724 | 12.6 | 0.7463 | 0.445/0.721/0.5624 | False |
| L2 | 29.773 | 326306 | 6.13 | 1.491 | 1.397/1.129/0.8123 | True |
| mean_degree | 3.36761 | 127218 | 15.72 | 0.004385 | 0.004395/0.004297/0.003415 | False |
| largest_cluster_fraction | 0.99885 | 264544 | 7.56 | 0.0004581 | 0.0004599/0.0003405/0.0002526 | True |
| mean_rg2 | 7.05829 | 21125 | 94.68 | 0.004734 | 0.003095/0.004359/0.00405 | False |
| mean_center_terminal_r2 | 15.9534 | 14211 | 140.74 | 0.01129 | 0.01026/0.01031/0.009555 | False |

Initial/final full graph distributions (degree counts, intra-loop counts, inter-edge multiplicities and component sizes):

```json
{
  "initial": {
    "component_sizes": [
      999,
      1
    ],
    "distinct_degree": {
      "0": 1,
      "1": 23,
      "2": 131,
      "3": 335,
      "4": 510
    },
    "giant": 999,
    "inter": 1702,
    "intra": 85,
    "intra_loops": {
      "0": 915,
      "1": 85
    },
    "isolated_stars": [
      272
    ],
    "mean_degree": 3.33,
    "multiplicity": {
      "0": 497835,
      "1": 1628,
      "2": 37,
      "3": 0,
      "4": 0
    }
  },
  "final": {
    "component_sizes": [
      998,
      1,
      1
    ],
    "distinct_degree": {
      "0": 2,
      "1": 13,
      "2": 133,
      "3": 331,
      "4": 521
    },
    "giant": 998,
    "inter": 1713,
    "intra": 64,
    "intra_loops": {
      "0": 936,
      "1": 64
    },
    "isolated_stars": [
      685,
      764
    ],
    "mean_degree": 3.356,
    "multiplicity": {
      "0": 497822,
      "1": 1643,
      "2": 35,
      "3": 0,
      "4": 0
    }
  }
}
```

All identity-specific residence episodes, including left/right censoring and zero-duration same-sweep excursions, are in the replay archive. Largest component is a graph quantity, not a periodic-wrapping test.

## Ea8 r003

Parent family r003; 8M → 24M; 32 validated 500k windows.
Accepted creations/breaks 6329/6341; neighbor gains/losses 5693/5718.
Initial → final bonds 1803 → 1791; intra 84 → 105; inter 1719 → 1686.
Never-broken original bonds 61/1803; never-lost original neighbor edges 68/1674.
Stars with a reaction/gained neighbor/lost neighbor: 1000/1000/1000 of 1000.
Initial isolated IDs []; final isolated IDs [581, 666].
Isolation visits (including zero-duration episodes) by 54 stars (zero-duration visits remain separately archived); 10 stars return after a nonzero gap.

| Observable | 8–12M | 12–16M | 16–20M | 20–24M |
|---|---:|---:|---:|---:|
| bonds | 1792.8 | 1795.1 | 1791.8 | 1792.2 |
| intra | 87.204 | 92.986 | 104.65 | 104.56 |
| inter | 1705.6 | 1702.1 | 1687.1 | 1687.6 |
| L1 | 41.935 | 38.392 | 39.745 | 34.909 |
| L2 | 38.559 | 34.685 | 31.444 | 34.501 |
| mean_degree | 3.3294 | 3.328 | 3.295 | 3.3054 |
| largest_cluster_fraction | 0.9975 | 0.99834 | 0.9984 | 0.99644 |
| isolated_stars | 2.4888 | 1.662 | 1.1562 | 1.7792 |
| mean_rg2 | 7.0243 | 7.0076 | 6.9844 | 6.994 |
| mean_center_terminal_r2 | 15.864 | 15.81 | 15.745 | 15.779 |

| Last-quarter observable | Mean | IAT steps | ESS | SEM | 5/10/20-block SEM | Unresolved |
|---|---:|---:|---:|---:|---|---|
| bound_fraction | 0.896092 | 235720 | 8.48 | 0.0014 | 0.001391/0.001051/0.0008184 | True |
| intra | 104.561 | 122891 | 16.27 | 0.4455 | 0.4015/0.4503/0.3414 | False |
| L1 | 34.9087 | 172179 | 11.62 | 0.6512 | 0.583/0.5563/0.4545 | False |
| L2 | 34.5012 | 593355 | 3.37 | 2.99 | 2.542/1.766/1.239 | True |
| mean_degree | 3.30543 | 226710 | 8.82 | 0.005566 | 0.005212/0.004331/0.003332 | True |
| largest_cluster_fraction | 0.996437 | 72671 | 27.52 | 0.0001433 | 0.00017/0.0001388/0.0001409 | False |
| mean_rg2 | 6.99399 | 59614 | 33.55 | 0.007936 | 0.009022/0.006136/0.005163 | False |
| mean_center_terminal_r2 | 15.7794 | 56422 | 35.45 | 0.02226 | 0.02435/0.01734/0.0141 | False |

Initial/final full graph distributions (degree counts, intra-loop counts, inter-edge multiplicities and component sizes):

```json
{
  "initial": {
    "component_sizes": [
      1000
    ],
    "distinct_degree": {
      "1": 25,
      "2": 132,
      "3": 313,
      "4": 530
    },
    "giant": 1000,
    "inter": 1719,
    "intra": 84,
    "intra_loops": {
      "0": 916,
      "1": 84
    },
    "isolated_stars": [],
    "mean_degree": 3.348,
    "multiplicity": {
      "0": 497826,
      "1": 1631,
      "2": 41,
      "3": 2,
      "4": 0
    }
  },
  "final": {
    "component_sizes": [
      996,
      2,
      1,
      1
    ],
    "distinct_degree": {
      "0": 2,
      "1": 22,
      "2": 147,
      "3": 334,
      "4": 495
    },
    "giant": 996,
    "inter": 1686,
    "intra": 105,
    "intra_loops": {
      "0": 896,
      "1": 103,
      "2": 1
    },
    "isolated_stars": [
      581,
      666
    ],
    "mean_degree": 3.298,
    "multiplicity": {
      "0": 497851,
      "1": 1612,
      "2": 37,
      "3": 0,
      "4": 0
    }
  }
}
```

All identity-specific residence episodes, including left/right censoring and zero-duration same-sweep excursions, are in the replay archive. Largest component is a graph quantity, not a periodic-wrapping test.

## Ea10 r001

Parent family r001; 8M → 24M; 32 validated 500k windows.
Accepted creations/breaks 807/813; neighbor gains/losses 733/739.
Initial → final bonds 1783 → 1777; intra 100 → 95; inter 1683 → 1682.
Never-broken original bonds 1133/1783; never-lost original neighbor edges 1048/1643.
Stars with a reaction/gained neighbor/lost neighbor: 881/779/790 of 1000.
Initial isolated IDs [143, 526, 595, 950]; final isolated IDs [526, 651, 950].
Isolation visits (including zero-duration episodes) by 16 stars (zero-duration visits remain separately archived); 0 stars return after a nonzero gap.

| Observable | 8–12M | 12–16M | 16–20M | 20–24M |
|---|---:|---:|---:|---:|
| bonds | 1791.5 | 1796.7 | 1797.5 | 1781.8 |
| intra | 102.93 | 99.874 | 97.077 | 95.149 |
| inter | 1688.6 | 1696.9 | 1700.4 | 1686.7 |
| L1 | 41.303 | 45.26 | 45.339 | 43.106 |
| L2 | 30.265 | 29.789 | 33.516 | 32.911 |
| mean_degree | 3.2946 | 3.3032 | 3.3101 | 3.2871 |
| largest_cluster_fraction | 0.99574 | 0.99582 | 0.99521 | 0.99639 |
| isolated_stars | 4.2637 | 4.1825 | 4.7862 | 3.6063 |
| mean_rg2 | 7.0051 | 7.0237 | 7.0305 | 7.0619 |
| mean_center_terminal_r2 | 15.813 | 15.86 | 15.876 | 15.963 |

| Last-quarter observable | Mean | IAT steps | ESS | SEM | 5/10/20-block SEM | Unresolved |
|---|---:|---:|---:|---:|---|---|
| bound_fraction | 0.890905 | 371623 | 5.38 | 0.0009596 | 0.0009056/0.0006525/0.0004738 | True |
| intra | 95.1492 | 183908 | 10.87 | 0.3186 | 0.2726/0.2943/0.224 | False |
| L1 | 43.1058 | 518517 | 3.86 | 0.9622 | 0.8943/0.6019/0.4263 | True |
| L2 | 32.911 | 478527 | 4.18 | 0.7285 | 0.5823/0.4678/0.3327 | True |
| mean_degree | 3.28711 | 335776 | 5.96 | 0.00313 | 0.002809/0.002238/0.0016 | True |
| largest_cluster_fraction | 0.996394 | 512147 | 3.91 | 0.0004102 | 0.0003809/0.0002567/0.0001791 | True |
| mean_rg2 | 7.06186 | 35476 | 56.38 | 0.006501 | 0.006761/0.004913/0.004937 | False |
| mean_center_terminal_r2 | 15.9626 | 24991 | 80.03 | 0.01526 | 0.01633/0.01298/0.01137 | False |

Initial/final full graph distributions (degree counts, intra-loop counts, inter-edge multiplicities and component sizes):

```json
{
  "initial": {
    "component_sizes": [
      996,
      1,
      1,
      1,
      1
    ],
    "distinct_degree": {
      "0": 4,
      "1": 33,
      "2": 142,
      "3": 315,
      "4": 506
    },
    "giant": 996,
    "inter": 1683,
    "intra": 100,
    "intra_loops": {
      "0": 903,
      "1": 94,
      "2": 3
    },
    "isolated_stars": [
      143,
      526,
      595,
      950
    ],
    "mean_degree": 3.286,
    "multiplicity": {
      "0": 497857,
      "1": 1603,
      "2": 40,
      "3": 0,
      "4": 0
    }
  },
  "final": {
    "component_sizes": [
      997,
      1,
      1,
      1
    ],
    "distinct_degree": {
      "0": 3,
      "1": 20,
      "2": 149,
      "3": 356,
      "4": 472
    },
    "giant": 997,
    "inter": 1682,
    "intra": 95,
    "intra_loops": {
      "0": 907,
      "1": 91,
      "2": 2
    },
    "isolated_stars": [
      526,
      651,
      950
    ],
    "mean_degree": 3.274,
    "multiplicity": {
      "0": 497863,
      "1": 1592,
      "2": 45,
      "3": 0,
      "4": 0
    }
  }
}
```

All identity-specific residence episodes, including left/right censoring and zero-duration same-sweep excursions, are in the replay archive. Largest component is a graph quantity, not a periodic-wrapping test.

## Ea10 r002

Parent family r002; 8M → 24M; 32 validated 500k windows.
Accepted creations/breaks 846/837; neighbor gains/losses 771/769.
Initial → final bonds 1787 → 1796; intra 85 → 98; inter 1702 → 1698.
Never-broken original bonds 1123/1787; never-lost original neighbor edges 1053/1665.
Stars with a reaction/gained neighbor/lost neighbor: 887/795/811 of 1000.
Initial isolated IDs [272]; final isolated IDs [].
Isolation visits (including zero-duration episodes) by 13 stars (zero-duration visits remain separately archived); 0 stars return after a nonzero gap.

| Observable | 8–12M | 12–16M | 16–20M | 20–24M |
|---|---:|---:|---:|---:|
| bonds | 1795.2 | 1791.8 | 1799.9 | 1795.8 |
| intra | 92.311 | 95.865 | 101.97 | 98.522 |
| inter | 1702.9 | 1696 | 1697.9 | 1697.2 |
| L1 | 37.268 | 37.093 | 42.835 | 38.908 |
| L2 | 39.165 | 36.422 | 38.53 | 33.465 |
| mean_degree | 3.3312 | 3.3178 | 3.3121 | 3.3187 |
| largest_cluster_fraction | 0.99901 | 0.99818 | 0.99735 | 0.99802 |
| isolated_stars | 0.9935 | 1.8225 | 2.6528 | 0.6535 |
| mean_rg2 | 6.9818 | 7.0098 | 7.0201 | 7.0292 |
| mean_center_terminal_r2 | 15.748 | 15.819 | 15.852 | 15.871 |

| Last-quarter observable | Mean | IAT steps | ESS | SEM | 5/10/20-block SEM | Unresolved |
|---|---:|---:|---:|---:|---|---|
| bound_fraction | 0.897882 | 491751 | 4.07 | 0.001787 | 0.001535/0.001141/0.0008031 | True |
| intra | 98.5215 | 215128 | 9.3 | 0.3846 | 0.4329/0.3226/0.251 | True |
| L1 | 38.9085 | 646225 | 3.09 | 1.819 | 1.525/1.044/0.7267 | True |
| L2 | 33.465 | 486411 | 4.11 | 1.242 | 1.168/0.8004/0.5688 | True |
| mean_degree | 3.31867 | 425630 | 4.7 | 0.005794 | 0.005263/0.003908/0.002786 | True |
| largest_cluster_fraction | 0.998022 | 461700 | 4.33 | 0.0005686 | 0.0004504/0.0003723/0.0002651 | True |
| mean_rg2 | 7.02921 | 10647 | 187.85 | 0.003122 | 0.002793/0.002676/0.002493 | False |
| mean_center_terminal_r2 | 15.871 | 9306 | 214.91 | 0.008767 | 0.007719/0.007829/0.007528 | False |

Initial/final full graph distributions (degree counts, intra-loop counts, inter-edge multiplicities and component sizes):

```json
{
  "initial": {
    "component_sizes": [
      999,
      1
    ],
    "distinct_degree": {
      "0": 1,
      "1": 23,
      "2": 131,
      "3": 335,
      "4": 510
    },
    "giant": 999,
    "inter": 1702,
    "intra": 85,
    "intra_loops": {
      "0": 915,
      "1": 85
    },
    "isolated_stars": [
      272
    ],
    "mean_degree": 3.33,
    "multiplicity": {
      "0": 497835,
      "1": 1628,
      "2": 37,
      "3": 0,
      "4": 0
    }
  },
  "final": {
    "component_sizes": [
      998,
      2
    ],
    "distinct_degree": {
      "1": 25,
      "2": 144,
      "3": 303,
      "4": 528
    },
    "giant": 998,
    "inter": 1698,
    "intra": 98,
    "intra_loops": {
      "0": 902,
      "1": 98
    },
    "isolated_stars": [],
    "mean_degree": 3.334,
    "multiplicity": {
      "0": 497833,
      "1": 1637,
      "2": 29,
      "3": 1,
      "4": 0
    }
  }
}
```

All identity-specific residence episodes, including left/right censoring and zero-duration same-sweep excursions, are in the replay archive. Largest component is a graph quantity, not a periodic-wrapping test.

## Ea10 r003

Parent family r003; 8M → 24M; 32 validated 500k windows.
Accepted creations/breaks 864/893; neighbor gains/losses 787/806.
Initial → final bonds 1803 → 1774; intra 84 → 77; inter 1719 → 1697.
Never-broken original bonds 1098/1803; never-lost original neighbor edges 1039/1674.
Stars with a reaction/gained neighbor/lost neighbor: 896/807/807 of 1000.
Initial isolated IDs []; final isolated IDs [334, 550, 787].
Isolation visits (including zero-duration episodes) by 12 stars (zero-duration visits remain separately archived); 2 stars return after a nonzero gap.

| Observable | 8–12M | 12–16M | 16–20M | 20–24M |
|---|---:|---:|---:|---:|
| bonds | 1802.8 | 1786.6 | 1782.8 | 1786 |
| intra | 84.9 | 84.337 | 81.724 | 78.335 |
| inter | 1717.9 | 1702.3 | 1701.1 | 1707.7 |
| L1 | 44.717 | 36.997 | 36.94 | 40.903 |
| L2 | 35.268 | 35.134 | 32.155 | 32.449 |
| mean_degree | 3.3491 | 3.3326 | 3.3299 | 3.3336 |
| largest_cluster_fraction | 0.99947 | 0.99713 | 0.99629 | 0.99752 |
| isolated_stars | 0.5295 | 2.867 | 2.739 | 2.484 |
| mean_rg2 | 7.0113 | 7.019 | 7.0109 | 7.0199 |
| mean_center_terminal_r2 | 15.815 | 15.829 | 15.817 | 15.84 |

| Last-quarter observable | Mean | IAT steps | ESS | SEM | 5/10/20-block SEM | Unresolved |
|---|---:|---:|---:|---:|---|---|
| bound_fraction | 0.893021 | 375971 | 5.32 | 0.001139 | 0.001167/0.0008056/0.0005672 | True |
| intra | 78.3347 | 282901 | 7.07 | 0.423 | 0.4362/0.3283/0.237 | True |
| L1 | 40.9027 | 123653 | 16.17 | 0.1917 | 0.1629/0.1977/0.151 | False |
| L2 | 32.4492 | 608095 | 3.29 | 1.6 | 1.382/0.9477/0.6569 | True |
| mean_degree | 3.33361 | 364443 | 5.49 | 0.004192 | 0.004406/0.002997/0.002114 | True |
| largest_cluster_fraction | 0.997516 | 310373 | 6.44 | 0.0003081 | 0.0002598/0.0002307/0.0001685 | True |
| mean_rg2 | 7.01994 | 19657 | 101.74 | 0.004284 | 0.004375/0.004258/0.003141 | False |
| mean_center_terminal_r2 | 15.8401 | 12584 | 158.93 | 0.009986 | 0.01095/0.01223/0.008863 | False |

Initial/final full graph distributions (degree counts, intra-loop counts, inter-edge multiplicities and component sizes):

```json
{
  "initial": {
    "component_sizes": [
      1000
    ],
    "distinct_degree": {
      "1": 25,
      "2": 132,
      "3": 313,
      "4": 530
    },
    "giant": 1000,
    "inter": 1719,
    "intra": 84,
    "intra_loops": {
      "0": 916,
      "1": 84
    },
    "isolated_stars": [],
    "mean_degree": 3.348,
    "multiplicity": {
      "0": 497826,
      "1": 1631,
      "2": 41,
      "3": 2,
      "4": 0
    }
  },
  "final": {
    "component_sizes": [
      997,
      1,
      1,
      1
    ],
    "distinct_degree": {
      "0": 3,
      "1": 26,
      "2": 124,
      "3": 352,
      "4": 495
    },
    "giant": 997,
    "inter": 1697,
    "intra": 77,
    "intra_loops": {
      "0": 923,
      "1": 77
    },
    "isolated_stars": [
      334,
      550,
      787
    ],
    "mean_degree": 3.31,
    "multiplicity": {
      "0": 497845,
      "1": 1613,
      "2": 42,
      "3": 0,
      "4": 0
    }
  }
}
```

All identity-specific residence episodes, including left/right censoring and zero-duration same-sweep excursions, are in the replay archive. Largest component is a graph quantity, not a periodic-wrapping test.
