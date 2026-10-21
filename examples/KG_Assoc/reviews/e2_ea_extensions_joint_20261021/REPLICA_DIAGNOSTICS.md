# Per-replica diagnostics

All counts and dynamical estimates retain separate 8M--24M and extension segments. Residence intervals are censored at 24M; original-edge tracking is a structural identity ledger, not a segment-crossing lifetime estimate.

## EA08_R001

Native/replayed step interval: 24000000 to 40000000; receipt: `independently_validated_recovery`. Extension accepted C/B and distinct G/L: 6253/6257 and 5645/5671.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1790.10725 | 92.76725 | 37.52975 | 31.84875 | 3.31983 | 0.99837 | 7.02043 | 15.85758 |
| preparation | 12--16 | 1790.77850 | 90.70025 | 36.07350 | 31.64950 | 3.32888 | 0.99856 | 7.03713 | 15.89748 |
| preparation | 16--20 | 1797.26350 | 99.34375 | 34.22425 | 38.88800 | 3.32767 | 0.99790 | 7.05574 | 15.94825 |
| preparation | 20--24 | 1794.54225 | 87.46325 | 41.28550 | 33.71825 | 3.33184 | 0.99761 | 7.03856 | 15.90986 |
| extension | 24--28 | 1790.13550 | 87.70225 | 32.24325 | 30.40625 | 3.34038 | 0.99759 | 7.05905 | 15.96960 |
| extension | 28--32 | 1797.25275 | 99.38425 | 36.10375 | 30.66175 | 3.32493 | 0.99802 | 7.02897 | 15.87941 |
| extension | 32--36 | 1794.23550 | 105.39675 | 38.60450 | 32.40875 | 3.30104 | 0.99844 | 7.04613 | 15.92246 |
| extension | 36--40 | 1801.04250 | 103.64875 | 44.58500 | 28.36525 | 3.30562 | 0.99798 | 7.00915 | 15.82807 |

Final exact graph:

```json
{"component_sizes": [998, 1, 1], "distinct_degree": {"0": 2, "1": 35, "2": 137, "3": 315, "4": 511}, "giant": 998, "inter": 1688, "intra": 105, "intra_loops": {"0": 895, "1": 105}, "isolated_stars": [615, 858], "mean_degree": 3.298, "multiplicity": {"0": 497851, "1": 1610, "2": 39, "3": 0, "4": 0}}
```

Final L1/L2: 39/32; bound fraction 0.89650.

Original 8M bonds never broken: 2/1783; distinct edges never lost: 2/1643. Current original-edge overlap (includes returns): 23.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1801.04250 | 3341.7073121555704 | 5.984964609931379 | {'5': 3.465540023755319, '10': 2.442659297659921, '20': 1.9319314544612771} |
| intra | 103.64875 | 3216.271346670483 | 6.21838080319442 | {'5': 0.7152490824880515, '10': 0.5859489276663398, '20': 0.43241182170776915} |
| L1 | 44.58500 | 5153.316117143345 | 3.8809961479884274 | {'5': 2.185327671368758, '10': 1.489058194146742, '20': 1.0465263971826033} |
| L2 | 28.36525 | 5165.204444595425 | 3.8720635774498446 | {'5': 1.6820566559274985, '10': 1.1792196955096101, '20': 0.8513347473078287} |
| mean_degree | 3.30562 | 1302.8270607395777 | 15.351231642860236 | {'5': 0.003839886554313854, '10': 0.003235682329724106, '20': 0.0029331934164696775} |
| mean_rg2 | 7.00915 | 103.36808899277842 | 193.48330993520887 | {'5': 0.003222664486461863, '10': 0.003671354190054263, '20': 0.0031340748266165397} |
| mean_center_terminal_r2 | 15.82807 | 194.5510116425915 | 102.80080186240244 | {'5': 0.014248685072184568, '10': 0.011882267496548561, '20': 0.01025372086179949} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 64 visited identities, 14 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 3080400, 'end_step': 27080400, 'left_censored': True, 'right_censored': False, 'star': 921, 'start_step': 24000000}`.

Extension satellite: 15 visited identities, 0 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 1006400, 'end_step': 39497200, 'left_censored': False, 'right_censored': False, 'star': 235, 'start_step': 38490800}`.

Exact event-integrated exposure:

```json
{"bond_steps": 28730632600, "final_bonds": 1793, "free_sticker_steps": 6538734800}
{"absent_interstar_pair_steps": 7965456095700, "distinct_neighbor_edge_steps": 26543904300, "distinct_neighbor_incidence_steps": 53087808600, "final_edges": 1649, "initial_edges": 1675, "neighbor_gains": 5645, "neighbor_losses": 5671, "original_edges_never_lost": 58, "original_neighbor_first_loss_survival_steps": 7365133700, "star_steps": 16000000000}
```

## EA08_R002

Native/replayed step interval: 24000000 to 40000000; receipt: `validated`. Extension accepted C/B and distinct G/L: 6263/6247 and 5675/5703.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1792.81625 | 85.63525 | 37.60425 | 38.07750 | 3.33965 | 0.99850 | 6.98414 | 15.75604 |
| preparation | 12--16 | 1793.94975 | 75.83925 | 42.11100 | 42.33375 | 3.35322 | 0.99892 | 7.00399 | 15.80408 |
| preparation | 16--20 | 1801.41775 | 74.01875 | 34.70600 | 28.48550 | 3.38539 | 0.99932 | 7.04426 | 15.91557 |
| preparation | 20--24 | 1791.73525 | 70.58575 | 37.61125 | 29.77300 | 3.36761 | 0.99885 | 7.05829 | 15.95338 |
| extension | 24--28 | 1796.07750 | 78.45775 | 36.82625 | 33.16000 | 3.36159 | 0.99829 | 7.07660 | 16.01193 |
| extension | 28--32 | 1794.50025 | 79.69350 | 37.88000 | 25.93450 | 3.35385 | 0.99777 | 7.09188 | 16.06554 |
| extension | 32--36 | 1801.47025 | 85.21550 | 40.78175 | 24.44575 | 3.35171 | 0.99936 | 7.05069 | 15.94403 |
| extension | 36--40 | 1792.59925 | 97.11700 | 38.90625 | 31.83925 | 3.31321 | 0.99879 | 6.99074 | 15.75590 |

Final exact graph:

```json
{"component_sizes": [1000], "distinct_degree": {"1": 30, "2": 151, "3": 308, "4": 511}, "giant": 1000, "inter": 1687, "intra": 106, "intra_loops": {"0": 894, "1": 106}, "isolated_stars": [], "mean_degree": 3.3, "multiplicity": {"0": 497850, "1": 1613, "2": 37, "3": 0, "4": 0}}
```

Final L1/L2: 37/36; bound fraction 0.89650.

Original 8M bonds never broken: 2/1787; distinct edges never lost: 2/1665. Current original-edge overlap (includes returns): 29.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1792.59925 | 1677.5351836181899 | 11.922253670330194 | {'5': 2.1099761402679396, '10': 1.7604813124225147, '20': 1.438703056072594} |
| intra | 97.11700 | 5463.580589787834 | 3.6606030919325487 | {'5': 3.8720171906901446, '10': 2.6340439125673916, '20': 1.8360435653012728} |
| L1 | 38.90625 | 1419.9110172220853 | 14.085389688100323 | {'5': 0.5892064313549198, '10': 0.56673924167606, '20': 0.460398550885963} |
| L2 | 31.83925 | 1961.3941543386168 | 10.196828595496662 | {'5': 0.9256192690572084, '10': 0.6867342250342076, '20': 0.539308191721482} |
| mean_degree | 3.31321 | 2814.1868375888384 | 7.106848675738872 | {'5': 0.00707573712591131, '10': 0.005379297633314017, '20': 0.0038826726060523734} |
| mean_rg2 | 6.99074 | 197.62686804344457 | 101.20081443381156 | {'5': 0.006106945402826602, '10': 0.0044939204886845895, '20': 0.0039989607330126326} |
| mean_center_terminal_r2 | 15.75590 | 280.23629281260344 | 71.3683434763897 | {'5': 0.019201821735291225, '10': 0.01473516612907367, '20': 0.011281595229162993} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 63 visited identities, 13 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 3389900, 'end_step': 29784100, 'left_censored': False, 'right_censored': False, 'star': 513, 'start_step': 26394200}`.

Extension satellite: 13 visited identities, 2 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 225900, 'end_step': 32823700, 'left_censored': False, 'right_censored': False, 'star': 24, 'start_step': 32597800}`.

Exact event-integrated exposure:

```json
{"bond_steps": 28738552000, "final_bonds": 1793, "free_sticker_steps": 6522896000}
{"absent_interstar_pair_steps": 7965239290400, "distinct_neighbor_edge_steps": 26760709600, "distinct_neighbor_incidence_steps": 53521419200, "final_edges": 1650, "initial_edges": 1678, "neighbor_gains": 5675, "neighbor_losses": 5703, "original_edges_never_lost": 65, "original_neighbor_first_loss_survival_steps": 7976783800, "star_steps": 16000000000}
```

## EA08_R003

Native/replayed step interval: 24000000 to 40000000; receipt: `validated`. Extension accepted C/B and distinct G/L: 6437/6437 and 5885/5867.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1792.77225 | 87.20450 | 41.93525 | 38.55875 | 3.32939 | 0.99750 | 7.02431 | 15.86388 |
| preparation | 12--16 | 1795.09950 | 92.98550 | 38.39175 | 34.68525 | 3.32798 | 0.99834 | 7.00759 | 15.81018 |
| preparation | 16--20 | 1791.78075 | 104.65400 | 39.74550 | 31.44375 | 3.29499 | 0.99840 | 6.98439 | 15.74474 |
| preparation | 20--24 | 1792.18350 | 104.56075 | 34.90875 | 34.50125 | 3.30543 | 0.99644 | 6.99399 | 15.77937 |
| extension | 24--28 | 1797.49375 | 99.86675 | 35.71875 | 39.48950 | 3.32495 | 0.99793 | 6.99060 | 15.77125 |
| extension | 28--32 | 1788.46100 | 92.47175 | 32.61900 | 30.60925 | 3.32674 | 0.99910 | 7.03491 | 15.89060 |
| extension | 32--36 | 1797.88750 | 99.06325 | 31.66850 | 32.69275 | 3.33499 | 0.99803 | 7.05253 | 15.93624 |
| extension | 36--40 | 1790.18325 | 93.21425 | 30.50175 | 27.97250 | 3.33293 | 0.99843 | 7.02601 | 15.87320 |

Final exact graph:

```json
{"component_sizes": [999, 1], "distinct_degree": {"0": 1, "1": 23, "2": 132, "3": 329, "4": 515}, "giant": 999, "inter": 1699, "intra": 92, "intra_loops": {"0": 908, "1": 92}, "isolated_stars": [507], "mean_degree": 3.334, "multiplicity": {"0": 497833, "1": 1635, "2": 32, "3": 0, "4": 0}}
```

Final L1/L2: 32/21; bound fraction 0.89550.

Original 8M bonds never broken: 2/1803; distinct edges never lost: 3/1674. Current original-edge overlap (includes returns): 21.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1790.18325 | 2092.0083480824132 | 9.560191295762513 | {'5': 3.5228680964521026, '10': 2.6395486001397988, '20': 2.040908829902423} |
| intra | 93.21425 | 4876.761802682281 | 4.101081990307533 | {'5': 1.2526655080267832, '10': 0.9917723368069686, '20': 0.713909019984892} |
| L1 | 30.50175 | 3175.081874668351 | 6.299050162947082 | {'5': 1.1517111318598952, '10': 0.811427843885908, '20': 0.5779027730782911} |
| L2 | 27.97250 | 3181.8830252524026 | 6.285586189458836 | {'5': 1.1275085226950614, '10': 0.9078946188236213, '20': 0.6588887674674208} |
| mean_degree | 3.33293 | 3953.7955229573527 | 5.058430534374331 | {'5': 0.010923976822796671, '10': 0.007650265552762053, '20': 0.005521556915971788} |
| mean_rg2 | 7.02601 | 250.39504391128224 | 79.87378538964302 | {'5': 0.005265376392580783, '10': 0.005648315155782196, '20': 0.004529389289601521} |
| mean_center_terminal_r2 | 15.87320 | 269.7036849223499 | 74.15545696291905 | {'5': 0.015313462377711886, '10': 0.0158564601121974, '20': 0.012660255211958387} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 57 visited identities, 8 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 2032900, 'end_step': 29046900, 'left_censored': False, 'right_censored': False, 'star': 134, 'start_step': 27014000}`.

Extension satellite: 17 visited identities, 6 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 934300, 'end_step': 24934300, 'left_censored': True, 'right_censored': False, 'star': 909, 'start_step': 24000000}`.

Exact event-integrated exposure:

```json
{"bond_steps": 28696085400, "final_bonds": 1791, "free_sticker_steps": 6607829200}
{"absent_interstar_pair_steps": 7965360780200, "distinct_neighbor_edge_steps": 26639219800, "distinct_neighbor_incidence_steps": 53278439600, "final_edges": 1667, "initial_edges": 1649, "neighbor_gains": 5885, "neighbor_losses": 5867, "original_edges_never_lost": 45, "original_neighbor_first_loss_survival_steps": 7409189100, "star_steps": 16000000000}
```

## EA10_R001

Native/replayed step interval: 24000000 to 56000000; receipt: `validated`. Extension accepted C/B and distinct G/L: 1710/1712 and 1578/1555.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1791.54500 | 102.93175 | 41.30250 | 30.26450 | 3.29462 | 0.99574 | 7.00512 | 15.81311 |
| preparation | 12--16 | 1796.74150 | 99.87350 | 45.26000 | 29.78900 | 3.30322 | 0.99582 | 7.02368 | 15.85974 |
| preparation | 16--20 | 1797.47600 | 97.07675 | 45.33900 | 33.51600 | 3.31012 | 0.99521 | 7.03054 | 15.87584 |
| preparation | 20--24 | 1781.80950 | 95.14925 | 43.10575 | 32.91100 | 3.28711 | 0.99639 | 7.06186 | 15.96256 |
| extension | 24--28 | 1793.62875 | 96.13350 | 45.28300 | 32.96975 | 3.30442 | 0.99766 | 7.06380 | 15.95740 |
| extension | 28--32 | 1808.26150 | 97.38950 | 43.84650 | 36.25900 | 3.33405 | 0.99737 | 7.04176 | 15.90420 |
| extension | 32--36 | 1805.04175 | 95.08600 | 42.13800 | 37.69250 | 3.33564 | 0.99755 | 7.04517 | 15.91832 |
| extension | 36--40 | 1790.93225 | 92.07025 | 38.16250 | 36.34475 | 3.32140 | 0.99682 | 7.02640 | 15.86671 |
| extension | 40--44 | 1796.40650 | 86.57325 | 36.60225 | 37.86725 | 3.34646 | 0.99764 | 7.02945 | 15.88350 |
| extension | 44--48 | 1783.00850 | 87.82525 | 34.69325 | 35.89175 | 3.32098 | 0.99669 | 7.02631 | 15.86711 |
| extension | 48--52 | 1797.38825 | 90.73550 | 35.56925 | 35.78850 | 3.34217 | 0.99659 | 7.00400 | 15.79770 |
| extension | 52--56 | 1789.87475 | 87.10250 | 31.54200 | 33.90900 | 3.34246 | 0.99890 | 6.98488 | 15.75758 |

Final exact graph:

```json
{"component_sizes": [999, 1], "distinct_degree": {"0": 1, "1": 28, "2": 134, "3": 324, "4": 513}, "giant": 999, "inter": 1688, "intra": 87, "intra_loops": {"0": 913, "1": 87}, "isolated_stars": [62], "mean_degree": 3.32, "multiplicity": {"0": 497840, "1": 1632, "2": 28, "3": 0, "4": 0}}
```

Final L1/L2: 28/35; bound fraction 0.88750.

Original 8M bonds never broken: 428/1783; distinct edges never lost: 410/1643. Current original-edge overlap (includes returns): 451.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1789.87475 | 6427.248982385505 | 3.1117512414427893 | {'5': 3.9746881245577037, '10': 2.724118752765136, '20': 1.9138144081430146} |
| intra | 87.10250 | 3562.3547871049095 | 5.6142639336195375 | {'5': 0.5563287865552164, '10': 0.46438714093594985, '20': 0.3320364794479826} |
| L1 | 31.54200 | 5651.913981054926 | 3.5386242725985393 | {'5': 1.282019074058572, '10': 0.8694666149107995, '20': 0.6052177076756847} |
| L2 | 33.90900 | 2123.1071260282547 | 9.420155843673541 | {'5': 0.38030136076538074, '10': 0.2869618635134483, '20': 0.22959220140799294} |
| mean_degree | 3.34246 | 5472.861677713258 | 3.6543953013547856 | {'5': 0.00573793698771607, '10': 0.004051769260321842, '20': 0.0028965150998543484} |
| mean_rg2 | 6.98488 | 255.43259217599592 | 78.29854377478884 | {'5': 0.007454716770299121, '10': 0.005442198794057476, '20': 0.0045512222878915645} |
| mean_center_terminal_r2 | 15.75758 | 437.13337016387607 | 45.75262692139527 | {'5': 0.021475093990591724, '10': 0.015569546832232505, '20': 0.01287972125556515} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 25 visited identities, 2 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 14472300, 'end_step': 38472300, 'left_censored': True, 'right_censored': False, 'star': 950, 'start_step': 24000000}`.

Extension satellite: 8 visited identities, 6 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 5449100, 'end_step': 50587800, 'left_censored': False, 'right_censored': False, 'star': 225, 'start_step': 45138700}`.

Exact event-integrated exposure:

```json
{"bond_steps": 57458140500, "final_bonds": 1775, "free_sticker_steps": 13083719000}
{"absent_interstar_pair_steps": 15930704881700, "distinct_neighbor_edge_steps": 53295118300, "distinct_neighbor_incidence_steps": 106590236600, "final_edges": 1660, "initial_edges": 1637, "neighbor_gains": 1578, "neighbor_losses": 1555, "original_edges_never_lost": 641, "original_neighbor_first_loss_survival_steps": 34414051300, "star_steps": 32000000000}
```

## EA10_R002

Native/replayed step interval: 24000000 to 56000000; receipt: `validated`. Extension accepted C/B and distinct G/L: 1719/1723 and 1573/1569.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1795.18275 | 92.31050 | 37.26825 | 39.16525 | 3.33121 | 0.99901 | 6.98181 | 15.74784 |
| preparation | 12--16 | 1791.84325 | 95.86525 | 37.09250 | 36.42250 | 3.31777 | 0.99818 | 7.00985 | 15.81888 |
| preparation | 16--20 | 1799.88875 | 101.97150 | 42.83500 | 38.52975 | 3.31210 | 0.99735 | 7.02006 | 15.85172 |
| preparation | 20--24 | 1795.76425 | 98.52150 | 38.90850 | 33.46500 | 3.31867 | 0.99802 | 7.02921 | 15.87100 |
| extension | 24--28 | 1785.03900 | 94.34700 | 29.39650 | 33.35925 | 3.32278 | 0.99877 | 7.03423 | 15.89184 |
| extension | 28--32 | 1800.84025 | 91.03225 | 25.80250 | 35.74050 | 3.36801 | 0.99784 | 7.06104 | 15.97231 |
| extension | 32--36 | 1810.03350 | 87.01450 | 26.02525 | 36.21725 | 3.39399 | 0.99829 | 7.04966 | 15.93866 |
| extension | 36--40 | 1814.58025 | 84.66825 | 25.20900 | 38.68250 | 3.40941 | 0.99936 | 7.06730 | 15.99186 |
| extension | 40--44 | 1802.17675 | 89.35000 | 24.96775 | 35.23700 | 3.37572 | 0.99854 | 7.07998 | 16.01432 |
| extension | 44--48 | 1792.45800 | 91.13075 | 24.27825 | 32.34325 | 3.35410 | 0.99795 | 7.09477 | 16.06744 |
| extension | 48--52 | 1798.77300 | 93.18150 | 28.79775 | 28.56500 | 3.35463 | 0.99633 | 7.09321 | 16.07359 |
| extension | 52--56 | 1789.86875 | 92.53800 | 28.88700 | 23.78875 | 3.33689 | 0.99815 | 7.08336 | 16.03516 |

Final exact graph:

```json
{"component_sizes": [998, 1, 1], "distinct_degree": {"0": 2, "1": 25, "2": 132, "3": 311, "4": 530}, "giant": 998, "inter": 1702, "intra": 90, "intra_loops": {"0": 911, "1": 88, "2": 1}, "isolated_stars": [637, 787], "mean_degree": 3.342, "multiplicity": {"0": 497829, "1": 1640, "2": 31, "3": 0, "4": 0}}
```

Final L1/L2: 31/25; bound fraction 0.89600.

Original 8M bonds never broken: 458/1787; distinct edges never lost: 448/1665. Current original-edge overlap (includes returns): 478.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1789.86875 | 1917.3246523439498 | 10.431201609779434 | {'5': 1.1154970164684157, '10': 0.8971835754490578, '20': 0.6914585913506539} |
| intra | 92.53800 | 3566.261117136626 | 5.608114308819352 | {'5': 0.6897999710060876, '10': 0.4950370075952798, '20': 0.36233860290879144} |
| L1 | 28.88700 | 4728.416135886654 | 4.229746161343237 | {'5': 0.6372918287566537, '10': 0.45142164325605816, '20': 0.31794310149690885} |
| L2 | 23.78875 | 2381.4534767528353 | 8.398232506003202 | {'5': 0.25009779337291277, '10': 0.21774706593252252, '20': 0.16591408485306955} |
| mean_degree | 3.33689 | 2001.8220246480953 | 9.990898168640063 | {'5': 0.0022827679196537154, '10': 0.0017925562520229542, '20': 0.001348205800899457} |
| mean_rg2 | 7.08336 | 494.62337994776567 | 40.43480516855488 | {'5': 0.006184801792802912, '10': 0.006059899903158345, '20': 0.004832306982982554} |
| mean_center_terminal_r2 | 16.03516 | 409.46021997758834 | 48.84479376554502 | {'5': 0.01739258837555423, '10': 0.01569997796409888, '20': 0.012498536132707789} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 18 visited identities, 4 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 13534100, 'end_step': 51016700, 'left_censored': False, 'right_censored': False, 'star': 767, 'start_step': 37482600}`.

Extension satellite: 6 visited identities, 2 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 1736400, 'end_step': 50179800, 'left_censored': False, 'right_censored': False, 'star': 44, 'start_step': 48443400}`.

Exact event-integrated exposure:

```json
{"bond_steps": 57575113100, "final_bonds": 1792, "free_sticker_steps": 12849773800}
{"absent_interstar_pair_steps": 15930168941200, "distinct_neighbor_edge_steps": 53831058800, "distinct_neighbor_incidence_steps": 107662117600, "final_edges": 1671, "initial_edges": 1667, "neighbor_gains": 1573, "neighbor_losses": 1569, "original_edges_never_lost": 673, "original_neighbor_first_loss_survival_steps": 34680271600, "star_steps": 32000000000}
```

## EA10_R003

Native/replayed step interval: 24000000 to 56000000; receipt: `validated`. Extension accepted C/B and distinct G/L: 1753/1728 and 1585/1571.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1802.75375 | 84.89950 | 44.71650 | 35.26775 | 3.34906 | 0.99947 | 7.01130 | 15.81520 |
| preparation | 12--16 | 1786.61175 | 84.33725 | 36.99725 | 35.13400 | 3.33255 | 0.99713 | 7.01898 | 15.82934 |
| preparation | 16--20 | 1782.83225 | 81.72375 | 36.93975 | 32.15475 | 3.32994 | 0.99629 | 7.01086 | 15.81735 |
| preparation | 20--24 | 1786.04200 | 78.33475 | 40.90275 | 32.44925 | 3.33361 | 0.99752 | 7.01994 | 15.84009 |
| extension | 24--28 | 1785.23125 | 73.94050 | 43.41775 | 36.16500 | 3.33575 | 0.99862 | 7.03513 | 15.89093 |
| extension | 28--32 | 1793.78100 | 79.46950 | 41.00725 | 34.81725 | 3.34661 | 0.99945 | 7.03499 | 15.88686 |
| extension | 32--36 | 1781.91725 | 85.36175 | 36.73625 | 33.19100 | 3.31964 | 0.99781 | 7.01952 | 15.83426 |
| extension | 36--40 | 1781.25750 | 87.13375 | 38.63150 | 32.41700 | 3.31135 | 0.99729 | 6.98738 | 15.75032 |
| extension | 40--44 | 1800.43475 | 83.01000 | 42.92925 | 30.68725 | 3.35099 | 0.99878 | 6.97873 | 15.72897 |
| extension | 44--48 | 1788.06050 | 85.08600 | 40.58900 | 28.77075 | 3.32677 | 0.99943 | 6.99347 | 15.77592 |
| extension | 48--52 | 1791.79825 | 91.80825 | 42.46800 | 31.23575 | 3.31704 | 0.99987 | 7.03204 | 15.87805 |
| extension | 52--56 | 1801.32875 | 91.65275 | 41.41875 | 33.43800 | 3.33851 | 0.99900 | 7.02519 | 15.86154 |

Final exact graph:

```json
{"component_sizes": [999, 1], "distinct_degree": {"0": 1, "1": 20, "2": 131, "3": 336, "4": 512}, "giant": 999, "inter": 1709, "intra": 90, "intra_loops": {"0": 910, "1": 90}, "isolated_stars": [494], "mean_degree": 3.338, "multiplicity": {"0": 497831, "1": 1630, "2": 38, "3": 1, "4": 0}}
```

Final L1/L2: 41/34; bound fraction 0.89950.

Original 8M bonds never broken: 432/1803; distinct edges never lost: 421/1674. Current original-edge overlap (includes returns): 452.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1801.32875 | 6091.785885976962 | 3.2831094812506736 | {'5': 3.86667363505117, '10': 2.739885217841143, '20': 1.9261760889539388} |
| intra | 91.65275 | 3474.3983296143733 | 5.756392359945619 | {'5': 0.5429906191639048, '10': 0.47348449024228895, '20': 0.33131466101768436} |
| L1 | 41.41875 | 5992.5873493061945 | 3.3374565666223535 | {'5': 0.5258641697244635, '10': 0.37485131311553965, '20': 0.2631214135897604} |
| L2 | 33.43800 | 5554.108733842826 | 3.6009377846951556 | {'5': 0.9398775352406287, '10': 0.6299153161779409, '20': 0.4421583426782763} |
| mean_degree | 3.33851 | 6109.57114180525 | 3.2735521914375187 | {'5': 0.007692966731047283, '10': 0.005408781874055484, '20': 0.0038015048595744917} |
| mean_rg2 | 7.02519 | 142.44341618110667 | 140.40662977761937 | {'5': 0.002993592360252671, '10': 0.0023791367120603556, '20': 0.0036711336880742547} |
| mean_center_terminal_r2 | 15.86154 | 121.01394066056166 | 165.27021507463382 | {'5': 0.009215284604129969, '10': 0.008383801089661433, '20': 0.009854775165376905} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 22 visited identities, 2 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 4480700, 'end_step': 56000000, 'left_censored': False, 'right_censored': True, 'star': 494, 'start_step': 51519300}`.

Extension satellite: 5 visited identities, 2 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 2038400, 'end_step': 35710600, 'left_censored': False, 'right_censored': False, 'star': 11, 'start_step': 33672200}`.

Exact event-integrated exposure:

```json
{"bond_steps": 57295204600, "final_bonds": 1799, "free_sticker_steps": 13409590800}
{"absent_interstar_pair_steps": 15930706713700, "distinct_neighbor_edge_steps": 53293286300, "distinct_neighbor_incidence_steps": 106586572600, "final_edges": 1669, "initial_edges": 1655, "neighbor_gains": 1585, "neighbor_losses": 1571, "original_edges_never_lost": 654, "original_neighbor_first_loss_survival_steps": 34251829300, "star_steps": 32000000000}
```

