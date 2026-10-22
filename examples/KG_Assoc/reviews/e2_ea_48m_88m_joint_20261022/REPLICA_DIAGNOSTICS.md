# Per-replica diagnostics

All counts and dynamical estimates retain separate preparation and both extension segments. Residence intervals are censored at every fresh-GJ boundary; original-edge tracking is a structural identity ledger, not a segment-crossing lifetime estimate.

## EA08_R001

Native/replayed step interval: 40000000 to 48000000; receipt: `validated`. Extension accepted C/B and distinct G/L: 3176/3167 and 2874/2855.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1790.10725 | 92.76725 | 37.52975 | 31.84875 | 3.31983 | 0.99837 | 7.02043 | 15.85758 |
| preparation | 12--16 | 1790.77850 | 90.70025 | 36.07350 | 31.64950 | 3.32888 | 0.99856 | 7.03713 | 15.89748 |
| preparation | 16--20 | 1797.26350 | 99.34375 | 34.22425 | 38.88800 | 3.32767 | 0.99790 | 7.05574 | 15.94825 |
| preparation | 20--24 | 1794.54225 | 87.46325 | 41.28550 | 33.71825 | 3.33184 | 0.99761 | 7.03856 | 15.90986 |
| previous_extension | 24--28 | 1790.13550 | 87.70225 | 32.24325 | 30.40625 | 3.34038 | 0.99759 | 7.05905 | 15.96960 |
| previous_extension | 28--32 | 1797.25275 | 99.38425 | 36.10375 | 30.66175 | 3.32493 | 0.99802 | 7.02897 | 15.87941 |
| previous_extension | 32--36 | 1794.23550 | 105.39675 | 38.60450 | 32.40875 | 3.30104 | 0.99844 | 7.04613 | 15.92246 |
| previous_extension | 36--40 | 1801.04250 | 103.64875 | 44.58500 | 28.36525 | 3.30562 | 0.99798 | 7.00915 | 15.82807 |
| extension | 40--44 | 1795.16725 | 94.57375 | 43.26500 | 27.09750 | 3.31577 | 0.99858 | 7.03450 | 15.89400 |
| extension | 44--48 | 1792.36700 | 79.85700 | 43.86800 | 33.06225 | 3.33916 | 0.99822 | 7.03782 | 15.90338 |

Final exact graph:

```json
{"component_sizes": [998, 1, 1], "distinct_degree": {"0": 2, "1": 29, "2": 127, "3": 315, "4": 527}, "giant": 998, "inter": 1714, "intra": 88, "intra_loops": {"0": 913, "1": 86, "2": 1}, "isolated_stars": [66, 646], "mean_degree": 3.336, "multiplicity": {"0": 497832, "1": 1622, "2": 46, "3": 0, "4": 0}}
```

Final L1/L2: 46/40; bound fraction 0.90100.

Original 8M bonds never broken: 0/1783; distinct edges never lost: 0/1643. Current original-edge overlap (includes returns): 8.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1792.36700 | 1275.635382426819 | 15.678461318587143 | {'5': 1.88963404195096, '10': 1.7270687594881793, '20': 1.3002408380150614} |
| intra | 79.85700 | 3347.9921865281576 | 5.97372959246355 | {'5': 1.8385726291066125, '10': 1.2563749550901506, '20': 0.9045692054057672} |
| L1 | 43.86800 | 3767.561896497484 | 5.308472839847172 | {'5': 1.2425937213144114, '10': 0.973482708286764, '20': 0.692107897733629} |
| L2 | 33.06225 | 6034.746152073307 | 3.314141058465031 | {'5': 3.157247649258765, '10': 2.170357959787074, '20': 1.5228720042890567} |
| mean_degree | 3.33916 | 2392.5288407292383 | 8.359355866282488 | {'5': 0.007697511935684148, '10': 0.005904144224845614, '20': 0.004304118154988925} |
| mean_rg2 | 7.03782 | 190.05400743408995 | 105.23324538124211 | {'5': 0.00578067708399774, '10': 0.004651060786463621, '20': 0.004484840043372626} |
| mean_center_terminal_r2 | 15.90338 | 144.75569270920124 | 138.16382365132864 | {'5': 0.014589531503987578, '10': 0.01178891026500202, '20': 0.011155593687837046} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 35 visited identities, 4 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 2576200, 'end_step': 44656200, 'left_censored': False, 'right_censored': False, 'star': 235, 'start_step': 42080000}`.

Extension satellite: 2 visited identities, 0 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 106600, 'end_step': 47206000, 'left_censored': False, 'right_censored': False, 'star': 151, 'start_step': 47099400}`.

Exact event-integrated exposure:

```json
{"bond_steps": 14350118600, "final_bonds": 1802, "free_sticker_steps": 3299762800}
{"absent_interstar_pair_steps": 3982690182400, "distinct_neighbor_edge_steps": 13309817600, "distinct_neighbor_incidence_steps": 26619635200, "final_edges": 1668, "initial_edges": 1649, "neighbor_gains": 2874, "neighbor_losses": 2855, "original_edges_never_lost": 308, "original_neighbor_first_loss_survival_steps": 6277189000, "star_steps": 8000000000}
```

## EA08_R002

Native/replayed step interval: 40000000 to 48000000; receipt: `validated`. Extension accepted C/B and distinct G/L: 3107/3104 and 2804/2788.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1792.81625 | 85.63525 | 37.60425 | 38.07750 | 3.33965 | 0.99850 | 6.98414 | 15.75604 |
| preparation | 12--16 | 1793.94975 | 75.83925 | 42.11100 | 42.33375 | 3.35322 | 0.99892 | 7.00399 | 15.80408 |
| preparation | 16--20 | 1801.41775 | 74.01875 | 34.70600 | 28.48550 | 3.38539 | 0.99932 | 7.04426 | 15.91557 |
| preparation | 20--24 | 1791.73525 | 70.58575 | 37.61125 | 29.77300 | 3.36761 | 0.99885 | 7.05829 | 15.95338 |
| previous_extension | 24--28 | 1796.07750 | 78.45775 | 36.82625 | 33.16000 | 3.36159 | 0.99829 | 7.07660 | 16.01193 |
| previous_extension | 28--32 | 1794.50025 | 79.69350 | 37.88000 | 25.93450 | 3.35385 | 0.99777 | 7.09188 | 16.06554 |
| previous_extension | 32--36 | 1801.47025 | 85.21550 | 40.78175 | 24.44575 | 3.35171 | 0.99936 | 7.05069 | 15.94403 |
| previous_extension | 36--40 | 1792.59925 | 97.11700 | 38.90625 | 31.83925 | 3.31321 | 0.99879 | 6.99074 | 15.75590 |
| extension | 40--44 | 1793.58025 | 107.11800 | 35.83225 | 34.97475 | 3.30172 | 0.99920 | 6.99170 | 15.75900 |
| extension | 44--48 | 1796.53125 | 96.74575 | 35.33125 | 41.56550 | 3.32951 | 0.99867 | 6.99917 | 15.79039 |

Final exact graph:

```json
{"component_sizes": [998, 1, 1], "distinct_degree": {"0": 2, "1": 30, "2": 119, "3": 332, "4": 517}, "giant": 998, "inter": 1703, "intra": 93, "intra_loops": {"0": 907, "1": 93}, "isolated_stars": [422, 659], "mean_degree": 3.332, "multiplicity": {"0": 497834, "1": 1629, "2": 37, "3": 0, "4": 0}}
```

Final L1/L2: 37/45; bound fraction 0.89800.

Original 8M bonds never broken: 1/1787; distinct edges never lost: 1/1665. Current original-edge overlap (includes returns): 11.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1796.53125 | 858.3096374235449 | 23.301614158773237 | {'5': 1.2245313516811305, '10': 1.3828565066757939, '20': 1.2072750348899077} |
| intra | 96.74575 | 6323.829634567045 | 3.1626405446909676 | {'5': 3.1828657389999986, '10': 2.2278697488981605, '20': 1.5443686870198345} |
| L1 | 35.33125 | 2501.518796094434 | 7.995142803334341 | {'5': 0.9949038898305705, '10': 0.7823148742673884, '20': 0.5893076753141864} |
| L2 | 41.56550 | 3210.653608225156 | 6.229261216084899 | {'5': 1.342290288555349, '10': 1.032005787020811, '20': 0.7500540243700343} |
| mean_degree | 3.32951 | 2697.4626421809494 | 7.414375156584049 | {'5': 0.006003589936446382, '10': 0.005286535961498998, '20': 0.003890987594496582} |
| mean_rg2 | 6.99917 | 381.17835911451147 | 52.4688758471509 | {'5': 0.006798130583060357, '10': 0.004859001323431557, '20': 0.004572962248513998} |
| mean_center_terminal_r2 | 15.79039 | 804.9843810949166 | 24.845202552621675 | {'5': 0.021461416611357566, '10': 0.015803382515067566, '20': 0.013690553516720744} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 32 visited identities, 2 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 827000, 'end_step': 44104800, 'left_censored': False, 'right_censored': False, 'star': 857, 'start_step': 43277800}`.

Extension satellite: 10 visited identities, 2 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 432300, 'end_step': 47616500, 'left_censored': False, 'right_censored': False, 'star': 102, 'start_step': 47184200}`.

Exact event-integrated exposure:

```json
{"bond_steps": 14360451200, "final_bonds": 1796, "free_sticker_steps": 3279097600}
{"absent_interstar_pair_steps": 3982737514600, "distinct_neighbor_edge_steps": 13262485400, "distinct_neighbor_incidence_steps": 26524970800, "final_edges": 1666, "initial_edges": 1650, "neighbor_gains": 2804, "neighbor_losses": 2788, "original_edges_never_lost": 304, "original_neighbor_first_loss_survival_steps": 6395122800, "star_steps": 8000000000}
```

## EA08_R003

Native/replayed step interval: 40000000 to 48000000; receipt: `validated`. Extension accepted C/B and distinct G/L: 3150/3135 and 2878/2863.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1792.77225 | 87.20450 | 41.93525 | 38.55875 | 3.32939 | 0.99750 | 7.02431 | 15.86388 |
| preparation | 12--16 | 1795.09950 | 92.98550 | 38.39175 | 34.68525 | 3.32798 | 0.99834 | 7.00759 | 15.81018 |
| preparation | 16--20 | 1791.78075 | 104.65400 | 39.74550 | 31.44375 | 3.29499 | 0.99840 | 6.98439 | 15.74474 |
| preparation | 20--24 | 1792.18350 | 104.56075 | 34.90875 | 34.50125 | 3.30543 | 0.99644 | 6.99399 | 15.77937 |
| previous_extension | 24--28 | 1797.49375 | 99.86675 | 35.71875 | 39.48950 | 3.32495 | 0.99793 | 6.99060 | 15.77125 |
| previous_extension | 28--32 | 1788.46100 | 92.47175 | 32.61900 | 30.60925 | 3.32674 | 0.99910 | 7.03491 | 15.89060 |
| previous_extension | 32--36 | 1797.88750 | 99.06325 | 31.66850 | 32.69275 | 3.33499 | 0.99803 | 7.05253 | 15.93624 |
| previous_extension | 36--40 | 1790.18325 | 93.21425 | 30.50175 | 27.97250 | 3.33293 | 0.99843 | 7.02601 | 15.87320 |
| extension | 40--44 | 1792.31075 | 89.69575 | 36.82700 | 29.98825 | 3.33256 | 0.99833 | 7.02496 | 15.86116 |
| extension | 44--48 | 1791.08375 | 90.95650 | 33.77925 | 35.74100 | 3.33347 | 0.99754 | 7.03438 | 15.88920 |

Final exact graph:

```json
{"component_sizes": [998, 1, 1], "distinct_degree": {"0": 2, "1": 26, "2": 137, "3": 276, "4": 559}, "giant": 998, "inter": 1709, "intra": 97, "intra_loops": {"0": 905, "1": 93, "2": 2}, "isolated_stars": [679, 900], "mean_degree": 3.364, "multiplicity": {"0": 497818, "1": 1656, "2": 25, "3": 1, "4": 0}}
```

Final L1/L2: 28/31; bound fraction 0.90300.

Original 8M bonds never broken: 1/1803; distinct edges never lost: 1/1674. Current original-edge overlap (includes returns): 14.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1791.08375 | 1549.5912194426458 | 12.906629664043633 | {'5': 2.476062461348672, '10': 2.2280645640081707, '20': 1.6689829819620499} |
| intra | 90.95650 | 3933.956700256703 | 5.0839400440515625 | {'5': 1.2843111845460184, '10': 1.0101529174667898, '20': 0.757557284615285} |
| L1 | 33.77925 | 6996.911255340948 | 2.8584041257824175 | {'5': 3.0335427308676564, '10': 2.104536866774044, '20': 1.4652825430342955} |
| L2 | 35.74100 | 2206.258049854761 | 9.065122731820336 | {'5': 1.0580707974894685, '10': 0.8158636528244163, '20': 0.622524212169167} |
| mean_degree | 3.33347 | 3817.607685488896 | 5.238882998905827 | {'5': 0.00848242828587424, '10': 0.006324180291635538, '20': 0.004646805211223366} |
| mean_rg2 | 7.03438 | 163.96437274429476 | 121.97771787405512 | {'5': 0.004531485529926902, '10': 0.004083446740042762, '20': 0.003992427327869652} |
| mean_center_terminal_r2 | 15.88920 | 155.11434904564473 | 128.9371365257427 | {'5': 0.01223910201805419, '10': 0.012257820137157564, '20': 0.01098909184880603} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 31 visited identities, 3 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 2055800, 'end_step': 48000000, 'left_censored': False, 'right_censored': True, 'star': 900, 'start_step': 45944200}`.

Extension satellite: 9 visited identities, 0 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 885700, 'end_step': 44056400, 'left_censored': False, 'right_censored': False, 'star': 162, 'start_step': 43170700}`.

Exact event-integrated exposure:

```json
{"bond_steps": 14333572700, "final_bonds": 1806, "free_sticker_steps": 3332854600}
{"absent_interstar_pair_steps": 3982667936400, "distinct_neighbor_edge_steps": 13332063600, "distinct_neighbor_incidence_steps": 26664127200, "final_edges": 1682, "initial_edges": 1667, "neighbor_gains": 2878, "neighbor_losses": 2863, "original_edges_never_lost": 318, "original_neighbor_first_loss_survival_steps": 6385581300, "star_steps": 8000000000}
```

## EA10_R001

Native/replayed step interval: 56000000 to 88000000; receipt: `validated`. Extension accepted C/B and distinct G/L: 1692/1660 and 1527/1507.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1791.54500 | 102.93175 | 41.30250 | 30.26450 | 3.29462 | 0.99574 | 7.00512 | 15.81311 |
| preparation | 12--16 | 1796.74150 | 99.87350 | 45.26000 | 29.78900 | 3.30322 | 0.99582 | 7.02368 | 15.85974 |
| preparation | 16--20 | 1797.47600 | 97.07675 | 45.33900 | 33.51600 | 3.31012 | 0.99521 | 7.03054 | 15.87584 |
| preparation | 20--24 | 1781.80950 | 95.14925 | 43.10575 | 32.91100 | 3.28711 | 0.99639 | 7.06186 | 15.96256 |
| previous_extension | 24--28 | 1793.62875 | 96.13350 | 45.28300 | 32.96975 | 3.30442 | 0.99766 | 7.06380 | 15.95740 |
| previous_extension | 28--32 | 1808.26150 | 97.38950 | 43.84650 | 36.25900 | 3.33405 | 0.99737 | 7.04176 | 15.90420 |
| previous_extension | 32--36 | 1805.04175 | 95.08600 | 42.13800 | 37.69250 | 3.33564 | 0.99755 | 7.04517 | 15.91832 |
| previous_extension | 36--40 | 1790.93225 | 92.07025 | 38.16250 | 36.34475 | 3.32140 | 0.99682 | 7.02640 | 15.86671 |
| previous_extension | 40--44 | 1796.40650 | 86.57325 | 36.60225 | 37.86725 | 3.34646 | 0.99764 | 7.02945 | 15.88350 |
| previous_extension | 44--48 | 1783.00850 | 87.82525 | 34.69325 | 35.89175 | 3.32098 | 0.99669 | 7.02631 | 15.86711 |
| previous_extension | 48--52 | 1797.38825 | 90.73550 | 35.56925 | 35.78850 | 3.34217 | 0.99659 | 7.00400 | 15.79770 |
| previous_extension | 52--56 | 1789.87475 | 87.10250 | 31.54200 | 33.90900 | 3.34246 | 0.99890 | 6.98488 | 15.75758 |
| extension | 56--60 | 1789.47925 | 87.05950 | 30.02650 | 29.16700 | 3.34479 | 0.99763 | 6.98718 | 15.75831 |
| extension | 60--64 | 1794.82300 | 90.19825 | 35.52775 | 25.58850 | 3.33819 | 0.99745 | 7.01309 | 15.82871 |
| extension | 64--68 | 1800.29225 | 94.89425 | 35.34900 | 34.80750 | 3.34010 | 0.99841 | 7.00460 | 15.81801 |
| extension | 68--72 | 1795.55725 | 93.46725 | 33.18775 | 37.18700 | 3.33780 | 0.99931 | 7.03263 | 15.89532 |
| extension | 72--76 | 1810.21725 | 93.14575 | 38.12800 | 35.78275 | 3.35789 | 0.99925 | 7.06115 | 15.98345 |
| extension | 76--80 | 1790.87775 | 89.45575 | 41.45950 | 30.25500 | 3.31993 | 0.99900 | 7.05904 | 15.96725 |
| extension | 80--84 | 1790.42375 | 86.77150 | 41.01875 | 34.42575 | 3.32527 | 0.99868 | 7.07636 | 16.01546 |
| extension | 84--88 | 1795.16825 | 85.35925 | 41.29175 | 37.96775 | 3.33703 | 0.99903 | 7.08079 | 16.03151 |

Final exact graph:

```json
{"component_sizes": [999, 1], "distinct_degree": {"0": 1, "1": 19, "2": 127, "3": 325, "4": 528}, "giant": 999, "inter": 1720, "intra": 87, "intra_loops": {"0": 913, "1": 87}, "isolated_stars": [718], "mean_degree": 3.36, "multiplicity": {"0": 497820, "1": 1640, "2": 40, "3": 0, "4": 0}}
```

Final L1/L2: 40/45; bound fraction 0.90350.

Original 8M bonds never broken: 163/1783; distinct edges never lost: 170/1643. Current original-edge overlap (includes returns): 206.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1795.16825 | 1524.3844577392745 | 13.12004980007526 | {'5': 0.9269391498366886, '10': 0.9315323434773637, '20': 0.7061350768164176} |
| intra | 85.35925 | 3300.3078026663634 | 6.060040819175026 | {'5': 0.3264196398043477, '10': 0.2529446167971687, '20': 0.18863891816740347} |
| L1 | 41.29175 | 2811.0011269563356 | 7.114902875067637 | {'5': 0.3282835569290669, '10': 0.2742072031836104, '20': 0.1992582544681254} |
| L2 | 37.96775 | 2642.433904725321 | 7.568779663413752 | {'5': 0.9197070185662382, '10': 0.704651061203739, '20': 0.5125187384250862} |
| mean_degree | 3.33703 | 1537.8286357628194 | 13.005350228817441 | {'5': 0.0018974274360301336, '10': 0.0018378872910068428, '20': 0.0014046603775702481} |
| mean_rg2 | 7.08079 | 286.1131708337353 | 69.90240939177981 | {'5': 0.004803653459933664, '10': 0.0045826180489786745, '20': 0.0037061551707871848} |
| mean_center_terminal_r2 | 16.03151 | 115.2249914945493 | 173.57345607568212 | {'5': 0.011503646218063737, '10': 0.0113607585121499, '20': 0.009123206375305256} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 19 visited identities, 1 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 7737800, 'end_step': 84840200, 'left_censored': False, 'right_censored': False, 'star': 427, 'start_step': 77102400}`.

Extension satellite: 4 visited identities, 2 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 2069200, 'end_step': 62446500, 'left_censored': False, 'right_censored': False, 'star': 526, 'start_step': 60377300}`.

Exact event-integrated exposure:

```json
{"bond_steps": 57467341700, "final_bonds": 1807, "free_sticker_steps": 13065316600}
{"absent_interstar_pair_steps": 15930598016700, "distinct_neighbor_edge_steps": 53401983300, "distinct_neighbor_incidence_steps": 106803966600, "final_edges": 1680, "initial_edges": 1660, "neighbor_gains": 1527, "neighbor_losses": 1507, "original_edges_never_lost": 675, "original_neighbor_first_loss_survival_steps": 35156088900, "star_steps": 32000000000}
```

## EA10_R002

Native/replayed step interval: 56000000 to 88000000; receipt: `validated`. Extension accepted C/B and distinct G/L: 1732/1749 and 1565/1584.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1795.18275 | 92.31050 | 37.26825 | 39.16525 | 3.33121 | 0.99901 | 6.98181 | 15.74784 |
| preparation | 12--16 | 1791.84325 | 95.86525 | 37.09250 | 36.42250 | 3.31777 | 0.99818 | 7.00985 | 15.81888 |
| preparation | 16--20 | 1799.88875 | 101.97150 | 42.83500 | 38.52975 | 3.31210 | 0.99735 | 7.02006 | 15.85172 |
| preparation | 20--24 | 1795.76425 | 98.52150 | 38.90850 | 33.46500 | 3.31867 | 0.99802 | 7.02921 | 15.87100 |
| previous_extension | 24--28 | 1785.03900 | 94.34700 | 29.39650 | 33.35925 | 3.32278 | 0.99877 | 7.03423 | 15.89184 |
| previous_extension | 28--32 | 1800.84025 | 91.03225 | 25.80250 | 35.74050 | 3.36801 | 0.99784 | 7.06104 | 15.97231 |
| previous_extension | 32--36 | 1810.03350 | 87.01450 | 26.02525 | 36.21725 | 3.39399 | 0.99829 | 7.04966 | 15.93866 |
| previous_extension | 36--40 | 1814.58025 | 84.66825 | 25.20900 | 38.68250 | 3.40941 | 0.99936 | 7.06730 | 15.99186 |
| previous_extension | 40--44 | 1802.17675 | 89.35000 | 24.96775 | 35.23700 | 3.37572 | 0.99854 | 7.07998 | 16.01432 |
| previous_extension | 44--48 | 1792.45800 | 91.13075 | 24.27825 | 32.34325 | 3.35410 | 0.99795 | 7.09477 | 16.06744 |
| previous_extension | 48--52 | 1798.77300 | 93.18150 | 28.79775 | 28.56500 | 3.35463 | 0.99633 | 7.09321 | 16.07359 |
| previous_extension | 52--56 | 1789.86875 | 92.53800 | 28.88700 | 23.78875 | 3.33689 | 0.99815 | 7.08336 | 16.03516 |
| extension | 56--60 | 1793.45350 | 90.39600 | 30.73500 | 26.83200 | 3.34464 | 0.99830 | 7.05569 | 15.95224 |
| extension | 60--64 | 1782.66675 | 97.75150 | 33.20075 | 23.23950 | 3.30343 | 0.99787 | 7.03898 | 15.90793 |
| extension | 64--68 | 1796.66175 | 102.70175 | 37.33100 | 23.61625 | 3.31326 | 0.99913 | 7.05721 | 15.95986 |
| extension | 68--72 | 1788.77575 | 100.46775 | 37.50700 | 28.65000 | 3.30160 | 0.99828 | 7.05997 | 15.96256 |
| extension | 72--76 | 1790.61850 | 101.49175 | 36.12800 | 30.51400 | 3.30600 | 0.99773 | 7.06764 | 15.98260 |
| extension | 76--80 | 1805.37200 | 101.03700 | 38.81450 | 35.76475 | 3.33104 | 0.99788 | 7.05845 | 15.97533 |
| extension | 80--84 | 1803.62550 | 92.07400 | 38.18325 | 37.23050 | 3.34674 | 0.99875 | 7.08831 | 16.04257 |
| extension | 84--88 | 1791.77925 | 91.68875 | 32.25050 | 34.32075 | 3.33568 | 0.99981 | 7.05698 | 15.96955 |

Final exact graph:

```json
{"component_sizes": [1000], "distinct_degree": {"1": 23, "2": 157, "3": 313, "4": 507}, "giant": 1000, "inter": 1684, "intra": 91, "intra_loops": {"0": 909, "1": 91}, "isolated_stars": [], "mean_degree": 3.304, "multiplicity": {"0": 497848, "1": 1620, "2": 32, "3": 0, "4": 0}}
```

Final L1/L2: 32/36; bound fraction 0.88750.

Original 8M bonds never broken: 161/1787; distinct edges never lost: 164/1665. Current original-edge overlap (includes returns): 195.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1791.77925 | 3651.0117361362572 | 5.4779336374210965 | {'5': 3.3084148300205496, '10': 2.249913703592004, '20': 1.6067588851883088} |
| intra | 91.68875 | 5909.246859743491 | 3.3845260613918846 | {'5': 0.7003163347730795, '10': 0.4913004639050663, '20': 0.34735028486347425} |
| L1 | 32.25050 | 2661.5346611994187 | 7.5144615967492285 | {'5': 0.491360133964896, '10': 0.3622103823900016, '20': 0.2610230126979127} |
| L2 | 34.32075 | 4009.6177391999463 | 4.988006663196446 | {'5': 0.5475593004415139, '10': 0.4417371091623513, '20': 0.3124607922772492} |
| mean_degree | 3.33568 | 4119.387046120435 | 4.855091249275943 | {'5': 0.006356435616758776, '10': 0.004311828562867003, '20': 0.0030763371076655433} |
| mean_rg2 | 7.05698 | 282.9340891431877 | 70.68784132928702 | {'5': 0.003962683035338612, '10': 0.0038913103445199337, '20': 0.004707243633508537} |
| mean_center_terminal_r2 | 15.96955 | 298.5837525675844 | 66.98288111129892 | {'5': 0.01565052882408135, '10': 0.01320952138008434, '20': 0.013655948282468239} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 22 visited identities, 2 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 7967100, 'end_step': 63967100, 'left_censored': True, 'right_censored': False, 'star': 787, 'start_step': 56000000}`.

Extension satellite: 2 visited identities, 0 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 11021900, 'end_step': 82388400, 'left_censored': False, 'right_censored': False, 'star': 72, 'start_step': 71366500}`.

Exact event-integrated exposure:

```json
{"bond_steps": 57411836300, "final_bonds": 1775, "free_sticker_steps": 13176327400}
{"absent_interstar_pair_steps": 15930835197200, "distinct_neighbor_edge_steps": 53164802800, "distinct_neighbor_incidence_steps": 106329605600, "final_edges": 1652, "initial_edges": 1671, "neighbor_gains": 1565, "neighbor_losses": 1584, "original_edges_never_lost": 629, "original_neighbor_first_loss_survival_steps": 33971795900, "star_steps": 32000000000}
```

## EA10_R003

Native/replayed step interval: 56000000 to 88000000; receipt: `validated`. Extension accepted C/B and distinct G/L: 1689/1684 and 1529/1522.

| Segment | Absolute interval / 1M | Bonds | Intra | L1 | L2 | Degree | Giant fraction | Rg² | Center-terminal r² |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preparation | 8--12 | 1802.75375 | 84.89950 | 44.71650 | 35.26775 | 3.34906 | 0.99947 | 7.01130 | 15.81520 |
| preparation | 12--16 | 1786.61175 | 84.33725 | 36.99725 | 35.13400 | 3.33255 | 0.99713 | 7.01898 | 15.82934 |
| preparation | 16--20 | 1782.83225 | 81.72375 | 36.93975 | 32.15475 | 3.32994 | 0.99629 | 7.01086 | 15.81735 |
| preparation | 20--24 | 1786.04200 | 78.33475 | 40.90275 | 32.44925 | 3.33361 | 0.99752 | 7.01994 | 15.84009 |
| previous_extension | 24--28 | 1785.23125 | 73.94050 | 43.41775 | 36.16500 | 3.33575 | 0.99862 | 7.03513 | 15.89093 |
| previous_extension | 28--32 | 1793.78100 | 79.46950 | 41.00725 | 34.81725 | 3.34661 | 0.99945 | 7.03499 | 15.88686 |
| previous_extension | 32--36 | 1781.91725 | 85.36175 | 36.73625 | 33.19100 | 3.31964 | 0.99781 | 7.01952 | 15.83426 |
| previous_extension | 36--40 | 1781.25750 | 87.13375 | 38.63150 | 32.41700 | 3.31135 | 0.99729 | 6.98738 | 15.75032 |
| previous_extension | 40--44 | 1800.43475 | 83.01000 | 42.92925 | 30.68725 | 3.35099 | 0.99878 | 6.97873 | 15.72897 |
| previous_extension | 44--48 | 1788.06050 | 85.08600 | 40.58900 | 28.77075 | 3.32677 | 0.99943 | 6.99347 | 15.77592 |
| previous_extension | 48--52 | 1791.79825 | 91.80825 | 42.46800 | 31.23575 | 3.31704 | 0.99987 | 7.03204 | 15.87805 |
| previous_extension | 52--56 | 1801.32875 | 91.65275 | 41.41875 | 33.43800 | 3.33851 | 0.99900 | 7.02519 | 15.86154 |
| extension | 56--60 | 1795.37150 | 86.13350 | 40.82850 | 33.28650 | 3.33859 | 0.99717 | 7.05437 | 15.94718 |
| extension | 60--64 | 1798.96875 | 88.25500 | 41.40875 | 28.50925 | 3.34048 | 0.99818 | 7.06686 | 15.98005 |
| extension | 64--68 | 1797.02200 | 85.72850 | 37.58750 | 32.37375 | 3.34741 | 0.99861 | 7.06970 | 15.98950 |
| extension | 68--72 | 1799.80850 | 84.92000 | 41.55625 | 33.04875 | 3.34666 | 0.99665 | 7.06520 | 15.98526 |
| extension | 72--76 | 1797.24750 | 87.77725 | 38.73400 | 34.21850 | 3.34147 | 0.99736 | 7.05481 | 15.96443 |
| extension | 76--80 | 1801.73850 | 87.89775 | 36.36075 | 39.40325 | 3.35496 | 0.99899 | 7.06062 | 15.97102 |
| extension | 80--84 | 1790.36925 | 85.41175 | 37.04750 | 38.87100 | 3.33582 | 0.99805 | 7.05368 | 15.94824 |
| extension | 84--88 | 1790.00325 | 88.94150 | 37.75425 | 41.64800 | 3.32692 | 0.99849 | 7.02918 | 15.86848 |

Final exact graph:

```json
{"component_sizes": [999, 1], "distinct_degree": {"0": 1, "1": 16, "2": 150, "3": 296, "4": 537}, "giant": 999, "inter": 1715, "intra": 89, "intra_loops": {"0": 912, "1": 87, "2": 1}, "isolated_stars": [458], "mean_degree": 3.352, "multiplicity": {"0": 497824, "1": 1638, "2": 37, "3": 1, "4": 0}}
```

Final L1/L2: 40/43; bound fraction 0.90200.

Original 8M bonds never broken: 153/1803; distinct edges never lost: 152/1674. Current original-edge overlap (includes returns): 192.

| Final 4M metric | Mean | IAT physical time | ESS | 5/10/20-block SEM |
|---|---:|---:|---:|---|
| bonds | 1790.00325 | 4062.4396345718055 | 4.92315007706153 | {'5': 4.734483416250396, '10': 3.423406848650763, '20': 2.409677180688645} |
| intra | 88.94150 | 6365.506167173903 | 3.1419339601204737 | {'5': 0.8451871464356288, '10': 0.581720054856476, '20': 0.4113847123787507} |
| L1 | 37.75425 | 3913.629857848887 | 5.110345312776444 | {'5': 0.6467293435046846, '10': 0.47823083251361653, '20': 0.34807596626235726} |
| L2 | 41.64800 | 3856.9200060659023 | 5.1854847828177295 | {'5': 0.7107475817756965, '10': 0.5217812440732863, '20': 0.37757090655092096} |
| mean_degree | 3.32692 | 4168.2438108635315 | 4.798183817336879 | {'5': 0.009293110203263465, '10': 0.006729640243397521, '20': 0.004726071433798735} |
| mean_rg2 | 7.02918 | 270.4080445276999 | 73.96229662816577 | {'5': 0.005226197895185308, '10': 0.003944077905668697, '20': 0.0030725429434693193} |
| mean_center_terminal_r2 | 15.86848 | 242.63784329041525 | 82.42737294718629 | {'5': 0.014911179011331857, '10': 0.011080479027198787, '20': 0.008682817110459852} |

The IAT/ESS are descriptive within-window estimates; they presume local stationarity and cannot resolve a drift by themselves. No universal ESS cutoff is used.

Extension isolated: 22 visited identities, 4 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'isolated', 'duration_steps': 19012500, 'end_step': 76471500, 'left_censored': False, 'right_censored': False, 'star': 166, 'start_step': 57459000}`.

Extension satellite: 3 visited identities, 0 identities with nonzero-gap returns. Longest segment-censored observed episode: `{'category': 'satellite', 'duration_steps': 1575700, 'end_step': 71134600, 'left_censored': False, 'right_censored': False, 'star': 682, 'start_step': 69558900}`.

Exact event-integrated exposure:

```json
{"bond_steps": 57482099300, "final_bonds": 1804, "free_sticker_steps": 13035801400}
{"absent_interstar_pair_steps": 15930535386900, "distinct_neighbor_edge_steps": 53464613100, "distinct_neighbor_incidence_steps": 106929226200, "final_edges": 1676, "initial_edges": 1669, "neighbor_gains": 1529, "neighbor_losses": 1522, "original_edges_never_lost": 681, "original_neighbor_first_loss_survival_steps": 35128618400, "star_steps": 32000000000}
```
