# Decision-interval and reference-bound analysis

Analysis specified before execution on 2026-09-23. This is a retrospective sensitivity check prompted by review, not a preregistered experiment.

- Keep the complete existing German one-second normalized and clipped activation record unchanged: 18,313,200 samples, 5,087 h. Keep E = 2 MWh, R = 0.75 MW, S = 0.1 MW, eta = 0.94, physical inverter limit = 1 MW and electrolyzer electrical-input bounds = [0,1] MW. Initial and final inventory are E/2. Comparator H0 = S*T = 508.7 MWh.
- Vary baseline decision duration only: 60, 300 and 900 seconds. For each duration, retain all original one-second samples for native computations. Form the matched coarse driver by averaging precisely those samples within each decision interval, with unchanged normalization and clipping.
- Compute a capacity-free cyclic evaluated dual upper bound for every duration. Reconstruct and independently replay a native feasible schedule where possible. Also audit the inherited 900-second witness, repeated at shorter decisions: nested admissible decisions guarantee this remains a feasible lower bound.
- Compute exact matched coarse optima using the actual duration (duration/3600 h), verifying interval-energy equations, inventory replay and cyclic endpoint residuals. A small test is run before the full 60-second case.
- Tighten the 900-second native finite-capacity bound by refining support knots, retaining conservative dual residual compensation and an outward margin. Attempt a physically audited witness guided by relaxed inventories and backward feasible intervals. Never call a relaxed solution a feasible native schedule without replay, and never claim a globally exact native solution from a nonzero bracket.
- Optional large finite-capacity LPs are attempted only after bounded pilots. One solver thread, no GPU. All caches, scripts, logs and outputs remain in this new D-drive project. Source data and previous frozen results are read-only.
- Report runtime, actual completed checks, unresolved brackets, and the sign test upper < comparator. Timing here is computational accounting, not performance benchmarking.
