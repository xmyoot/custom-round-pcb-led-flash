# Implementation status —2026-10-20

## Actual state

One authoritative KiCad10 project exists at the root. Current candidate:244 symbols, including6 nonphysical power flags and2 offboard assembly items;236 PCB footprints. No routed tracks or planes yet. Schematic and PCB are matched by native netlist/pad assignments. The source remains an unreleased prototype candidate.

Implemented: MCU/boot/UART isolation; TPS63070 logic supply; independent battery undervoltage supervisor; fused DW01/AO3400A protection; TUSB320LAI source-current qualification; TLV760 USB logic supply; TPS25200 VBUS clamp/current limiter; TP4056300mA cell charging with separate pack NTC and shorted-NTC comparator; three indicators; shutter/slide controls; LED-area NTC; switched ADC dividers; LTC3225 balanced4.8V2.5F effective capacitor bank; default-on discharge; fused MP3435 boost with input disconnect/current sense; two CAT4101200mA sinks; AO4407A physical LED cutoff; two LTC6993-1 non-retriggerable timers; separate preflash energy, loaded-bank UVLO, boost-ready, and startup interlocks.

External items in the same BOM: one Bridgelux BXRV-TR-2765G-10A0-A-23 COB and one TDK B57861S0103F040 cell NTC. J4/J5 are solder-wire lands, not separate purchased LEDs/connectors. J3 is a1.25mm JST-GH NTC interface, distinct from the2mm JST-PH battery connector to prevent interchange.

## Engineering decisions

- Preserve84mm OD/55mm opening,4layers1.6mm. Rear cell mounting replaces the incompatible18x70mm battery cutout. RF module antenna extends beyond board perimeter; enclosure envelope is larger than PCB.
- Selected COB is2700/6500K, a departure from requested approximate3000K warm. Its18V channels require21.07V boost, superseding10.5V architecture assumptions.
- Use200mA nominal/channel via2.49k RSET.300/350mA were provisional and lacked simultaneous-flash aged/cold ESR margin. Current-bound scaling from the CAT4101350mA specification is a model requiring prototype characterization.
- Two Eaton5F/2.7V cells in series give2.5F,80mohm initial bank ESR. Model200% aged ESR and conservative150% cold multiplier at0C, plus50mohm for interconnects and power components. Stored energy28.8J at4.8V. Nominal cold start charge time~160s; real/tolerance time longer.
- Boost feedback162k/10k0.1%; compensation120k/33n plus47p is an analytical starting network. Stability and pulse load response require qualification.
- Separate GPIO2 trigger allows LED PFET settling before precise channel pulses. Firmware sets TRIG_REQ low before ARM, waits for GPIO7 permission, triggers window, waits50us, then commands0.5–1ms pulses within the window. Startup strap levels remain intact.
- Hardware window1.403ms nominal; cooldown1.258s nominal. Physical cutoff remains independent of sink enables. Output reservoir is before cutoff; do not add bulk capacitance on LED_ANODES.
- USB charging only with advertised1.5A/3A Type-C source. Legacy/default-current charging unsupported. USB presence inhibits logic and supercap recharge in hardware.
- Pack NTC is isolated and bonded to the cell. A shorted TEMP pin disables TP4056 internal monitoring, so U8 independently inhibits CE on a short. Native TDK R/T8016 boundary calculations include NTC tolerance and divider loading.

## Checks actually run

Native ERC:0violations. Latest placed-candidate DRC:0geometric violations,0schematic parity issues; hundreds of unconnected items because routing has not started. Refresh these reports after edits. Current report paths: `analysis/draft_erc.rpt`, `analysis/core_parity_drc.rpt`.

`check_design_envelope.py` writes `analysis/design_envelope.json`. It covers comparator/ref/resistor corners, readiness reachability, cap sag/current-limit allocation, window/cooldown bounds, PFET-off estimate, and cell NTC boundaries. These are calculations with explicitly listed assumptions, not measured guarantees.

Schematic analyzer run: `analysis/2026-10-20_2150/schematic.json`. Count238 excludes6flags and includes2offboard items. Preliminary high findings PP-001 CAP_FUSED and VM-001 CC_ALLOWED/BAT_PROT/CHARGE_ALLOWED are analyzer topology/domain-inference limitations to cross-check, not accepted design blockers. No suppressions were added. Full routed-board review remains pending.

Independent extraction cache: MP3435GL-Z86/100, TPS63070RNMR86/100, TLV3011BIDBVR93/100. Source pinout/operating facts are in `datasheets/extracted/`. Source PDF downloads/failed attempts are recorded; lack of a cached PDF is not proof that a part was checked. No distributor API credentials are configured, and lifecycle/stock audit is not complete.

## Layout and footprint status

All parts fit through conservative screening plus native DRC. Power-block seeds now precede ordinary logic placement. Critical loop/decoupling distances must still be reviewed and refined before routing; fit alone is insufficient.

Project footprints: TPS63070 RNM0015A, Coilcraft XFL4020, MP3435 special20pin QFN, TopPower TP4056 ESOP8, and RF module derived to remove open via-in-pad holes. The TPS63070 and MP3435 package drawings were inspected. TP4056 EP dimensions2.145x3.302mm in conventional SOIC orientation were transcribed from TopPower page14. Independent package/sign/paste checks remain part of release.

Panasonic35SVPF120M is10mm diameter and12.7mm maximum height; its initial8mm provisional land was corrected toCP_Elec_10x12.6. Eaton cells max10.5mm diameter/22.3mm height. JST-GH NTC mechanical tabs are grounded. No validated full rear-cell/enclosure/heat-spreader3D assembly yet.

Default trace/clearance target0.20mm. Board clearance floor0.125mm accommodates the MPS recommended land pattern; U70 local clearance0.125mm, J1 local0.15mm. Fabricator must support5mil copper clearance and appropriate fine-pitch mask openings. Do not silently relax these rules through router settings.

Reference silk, fiducials, mask color/ENIG fabrication notes, final stackup, test documentation and fabrication package remain unfinished. Earlier image previews may be stale.

## Remaining work

1. Complete independent component/footprint and effective-capacitance checks; fix any issues before final routing.
2. Finish deliberate power-loop placement/routes, low-impedance ground return/thermal vias, then automate ordinary signals with pinned router. Native DRC/parity must finish with0unconnected items.
3. Improve schematic composition/annotations and assembly/test labeling.
4. Run full KiCad skill review: schematic/PCB/cross/EMC/thermal, lifecycle when accessible, Gerber analysis after export; raw-file and manufacturer cross-checks plus false-positive triage. No SPICE simulator was found on PATH; disclose simulation limits if still unavailable.
5. Generate/inspect schematic PDF, Gerbers, plated/NPTH drills, BOM/CPL and assembly/fabrication notes. Release as a prototype design with an explicit bring-up/qualification plan. No physical tests have occurred.
6. Portfolio assets follow a successful prototype-design release; do not present measurements or compliance that do not exist.

## Tooling note

Datasheet workers installed temporary validation dependencies under ignored `datasheets/extracted/_python_deps` and `_pipeline_deps`. Automatic approval review rejected optional cleanup with only “blocked by policy”; cleanup was not retried. These directories are excluded from tracked project artifacts.
