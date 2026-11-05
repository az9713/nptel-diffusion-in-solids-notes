# Book-wide notation contract

| Symbol | Meaning | Domain / units | Main treatment / scope |
|---|---|---|---|
| x, t | position, elapsed time | m, s | Ch1; local redefinition |
| c, c_i | amount concentration of selected species | mol m⁻³ | Ch1 |
| J, J_i | molar flux, lattice frame unless stated | mol m⁻² s⁻¹ | Ch1 |
| D | scalar diffusivity in a specified model | m² s⁻¹; nonnegative | Ch1 |
| M | areal solute amount | mol m⁻² | Ch3 |
| ell | jump length | m | Ch7 |
| Gamma | total successful jump frequency per atom | s⁻¹ | Ch7 |
| f | tracer jump correlation factor | dimensionless | Ch8 |
| k_B, R | Boltzmann and molar gas constants | J K⁻¹; J mol⁻¹ K⁻¹ | Ch6/9 |
| Q, Q_m, Q_f | activation, migration, formation molar enthalpy | J mol⁻¹ | Ch4/9 |
| N_i | mole fraction of species i | [0,1] | Ch10 |
| mu_i | molar chemical potential | J mol⁻¹ | Ch10 |
| V_m | molar volume | m³ mol⁻¹ | Ch10 |
| D_i* | tracer diffusivity of species i | m² s⁻¹ | Ch7 |
| D_i | intrinsic diffusivity in specified frame | m² s⁻¹ | Ch13 |
| D-tilde | binary interdiffusion coefficient | m² s⁻¹ | Ch10 |
| v_K | marker/lattice velocity in the volume-fixed frame | m s⁻¹ | Ch13 |
| Phi | thermodynamic factor d ln(a_i)/d ln(N_i) | dimensionless | Ch13 |
| delta, D_b | boundary thickness and boundary diffusivity | m; m² s⁻¹ | Ch20 |
| s_b | grain-boundary segregation factor | dimensionless | Ch20 |
| q | scattering wavevector magnitude | m⁻¹ | Ch19 |

All supplementary symbols are chapter-local and require first-use definitions.
Avoid using M for mobility when M denotes areal amount; write B_i for atomic
mobility with its convention specified. Do not equate successful jumps to
attempt frequency or per-neighbor rate without a coordination factor.
