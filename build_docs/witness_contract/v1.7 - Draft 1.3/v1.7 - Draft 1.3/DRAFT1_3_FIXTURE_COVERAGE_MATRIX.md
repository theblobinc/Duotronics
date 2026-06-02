# Draft 1.3 Fixture Coverage Matrix

Draft 1.3 redo adds positive branch coverage for:

- Bayesian model families: discrete, conjugate, graphical_bayesian_network, hierarchical, particle_monte_carlo, external_verified.
- Knot encodings: planar_diagram, gauss_code, dowker_thistlethwaite, grid_diagram, braid_closure, implementation_defined.
- Calibration rules: brier, log_score, reliability_bins, expected_calibration_error, custom.
- Knot invariants: crossing_count, component_count, determinant, alexander_polynomial, jones_polynomial, signature, linking_number, fundamental_group_presentation, wirtinger_presentation, quandle_coloring, custom.

It also adds semantic negative fixtures for duplicate Bayesian hypothesis IDs and mathematically invalid typed knot encoding payloads.
