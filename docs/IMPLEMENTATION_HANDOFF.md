# Implementation handoff

Continue from `IMPLEMENTATION_STATUS.md`, then the authoritative root KiCad files and scripts. The original architecture describes requirements and provisional decisions, not frozen component values.

KiCad10.0.7 CLI and pcbnew Python: `C:/Program Files/KiCad/10.0/bin/`.

Generate with `scripts/build_schematic.py`, export a fresh native netlist to `analysis/draft.net`, then run `scripts/sync_core_pcb.py`. Before routing, `scripts/seed_power_placement.py` seeds the power blocks and `scripts/place_core.py` screens fit. **Do not run reseeding/placement or net synchronization on a routed board.** All have track guards. After routing, use reviewed incremental edits.

`select_bom.py` enriches source symbol properties. Manufacturer selection is separate from stock and effective-capacitance qualification. Do not overwrite BOM choices only in CSV.

KiCadRoutingTools is installed outside the project at `C:/Users/hecto/.codex/tools/KiCadRoutingTools`, commit0523df20d2f6e9f6c34e4491839c2d08b4280085; router binaryv0.23.1. Use explicit output/overwrite to avoid generating PCB copies. Keep project DRC settings: pass `--no-fix-drc-settings`, `--escalation off`, and do not request severity relaxation or pad swaps.

The prototype channel setpoint is200mA (R230/R2312.49k), not the earlier350mA or300mA assumptions. GPIO2 is a post-boot trigger output with its required10k strap pull-up; initialize it LOW before ARM. Trigger the hardware window, wait50us, then generate0.5–1ms warm/cool requests. GPIO7 reads trigger permission.

Independent datasheet extractions exist for MP3435GL-Z, TPS63070RNMR and TLV3011BIDBVR. They caught the mandatory TPS63070 PS/SYNC-to-VIN series resistor (R1810k). FB2 NC is permitted with VSEL grounded. TLV3011B reference is1.223–1.260V and its POR output is Hi-Z; the20ms supervisor delay handles initial comparator/timer settling.

No manufacturing order or portfolio publication is authorized by merely reaching this draft stage. Complete prototype release checks and inspect fabrication outputs first. Publishing must be an explicit user action/request.
