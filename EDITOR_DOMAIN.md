# Domain: Diffusion in Solids

## Manuscript and reader
Original HTML textbook chapters following Mayur Vaidya, NPTEL113106635,
IIT Hyderabad. Quantitative graduate unfamiliar with materials science.
Canonical prose: chapters/chNN.html. Root reader pages are generated. Code:
code/chNN.py with actual saved output. Source archive is private; normalized
captions remove only exact rolling overlaps. Detailed maps: work/source-maps/.

## Review responsibilities
Use science-editor. Review actual full chapter, exercise solutions, source
boundaries, code and relevant visual assets. Require precise statements, local
definitions, consequential derivations, checks, limits, and a concrete tie.
Two independent full reviewers must remain independent; do not read each other's
reports before your verdict. Root applies fixes. Subsequent targeted checks must
identify changed content and bind the resulting body/code/asset digests.

## Distinctions that must survive
- Balance law versus constitutive law; reaction sources versus transport.
- Amount versus concentration; number, molar and site-fraction conventions.
- Instantaneous Fick law versus steady-state assumption.
- Flux density versus total transfer rate, especially changing radial area.
- Scalar isotropic response versus anisotropic tensor and principal orientation.
- Tracer, self, uncorrelated jump, intrinsic and interdiffusion coefficients.
- Lattice, volume-fixed and laboratory frames and marker signs.
- Equilibrium driving forces versus kinetic mobilities.
- Source example, verified correction, research extension, synthetic construction.
- Caption reading, selected-frame checks, numerical verification, scientific
  review, browser usability, and publication are separate evidence dimensions.

## Sources and citation discipline
Official course and exact recording identities: source-manifest.json. Consult
the assigned private maps and source text, not memory. Do not invent papers,
pages, reference metadata, visual observations or empirical constants. Primary
references inspected for Ch9 onward are recorded in source maps, including
Darken1948 and owning software/probe documentation. For Ch1 Fick1855 DOI metadata
is only bibliographic verification; the text does not claim full article reading.

## Pilot running case and numbers
Stationary, nonreacting planar coating; molar concentration and signed SI molar
flux. Ch1 series layers L=(1e-3,2e-3)m, D=(1e-12,4e-12)m²/s, endpoints2 and0.5
mol/m³ give J=1e-9mol/(m²s), interface1mol/m³. Directional tensor diag(1,4)e-12,
45degree gradient magnitude1000mol/m⁴ gives D_n=2.5e-12 and transverse flux
-1.5e-9. Verify all numbers against executing code, not this brief alone.
Animation is exact nondimensional u=1+.5cos(pi xi)exp(-pi²tau) on[0,1], no-flux
faces, mean1; geometry and displayed plot must share that state. No measured
material behavior or material-specific clock is claimed.

## House conventions
See spec/house-style.md and plan/notation.md. Derive central claims, define all
symbols before use, use SI, qualify physical assumptions locally, and write
continuous textbook prose. No production diary in the scientific body.
