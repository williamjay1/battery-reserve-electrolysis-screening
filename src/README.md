# Analysis modules

- `revision_evidence.py` is the primary reproduction entry point. It regenerates the revision-specific enclosure results, parameter grid, and three added figures after the public-source inputs have been reconstructed.
- `reachability.py` implements native-path reachability, reconstruction, and schedule audit routines.
- `hydrogen_lp_pilot.py` solves the interval-constant physical linear program.
- `native_hydrogen_bound.py` forms the finite-capacity convex-relaxation upper value from a reconstructed native activation cache.
- `cyclic_energy_dual.py` evaluates the capacity-free scalar-dual upper value from a reconstructed native activation cache.
- `verify_hydrogen_optimization.py` provides small synthetic verification fixtures.
- `main_result_audit.py` checks the public derived result ledger without requiring provider inputs.

All allocation quantities are electrical input under the stated model. The upper-value modules must not be treated as dispatch schedulers or exact native optimum solvers.
