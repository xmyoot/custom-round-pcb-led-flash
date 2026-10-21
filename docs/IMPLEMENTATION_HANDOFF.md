# Implementation handoff

**Implementation update:** the model switch occurred and the first core draft now exists. This original handoff is historical; read `IMPLEMENTATION_STATUS.md` before further work. It records the 65-symbol project, checks, open circuits, and component changes. Do not restart from the mechanical seed or treat the old 10.5 V/0.5 F assumptions as frozen.

The user requested architecture first, followed by implementation using 6.1 Sol after compaction/model switch. Preserve this boundary; no schematic or PCB has been created yet. Do not claim the current chat model was changed by tools.

Read `docs/SYSTEM_ARCHITECTURE.md` and the three client screenshots first. The user authorizes routine engineering assumptions and wants an accurate, fast PCB-focused workflow for a hiring portfolio. One authoritative KiCad 10 project only. Do not ask for repeated permission for ordinary implementation choices. Record departures prominently.

Installed KiCad CLI is `C:/Program Files/KiCad/10.0/bin/kicad-cli.exe`, version 10.0.7. Bundled Python is `C:/Program Files/KiCad/10.0/bin/python.exe`. Installed skill `C:/Users/hecto/.codex/skills/kicad/SKILL.md` contains kicad-happy analyzers. There is no separate `kicad-happy` skill directory in the inspected skills folder. Relevant companion skills: bom, datasheets, digikey, spice, emc, and fabrication skills. Read applicable instructions before use.

Important baseline decisions:

- Preserve 84 mm circular PCB with 55 mm opening; move cell behind PCB rather than intersecting the annulus with the requested battery cutout.
- Use 3.3 V buck-boost instead of LDO; maintain ESP32 supply across usable cell range.
- Provisional two-channel 8–9.5 V COB envelope at 350 mA/channel, 10.5 V boost. It is not an identified real emitter. Do not start routing until a compatible real emitter is selected; revise architecture if necessary.
- Balanced 0.5 F effective low-ESR cap bank, limited recharge, reverse blocking, independent flash fault isolation, hardware pulse cutoff. Exact capacitor and sink/timer/limiter parts remain unselected.
- TP4056/DW01 topology, hardware operation inhibit on USB, conservative low-current charging baseline. Verify USB current rules and charger programmability before locking this choice.
- UART pogo programming; no USB data routing. GPIO allocation is preliminary.

First implementation work:

1. Select real COB and cap bank with manufacturer datasheets, validate electrical envelope/ESR/physical fit. Select actual USB-C connector and resolve true THT versus hybrid construction.
2. Resolve hardware current-sink, timer/re-arm, cap charger, balancing, discharge, and isolation circuits. Fetch actual datasheets; TPS61088 datasheet web fetch failed in architecture phase.
3. Validate footprints mechanically on annulus before committing detailed schematic. Verify rear battery/heat spreader/antenna coexistence.
4. Establish single `Round_LED_Flash.kicad_sch/.kicad_pcb/.kicad_pro` with one schematic sheet and project-relative libraries. Use Git history, not named duplicate board variants.
5. Verify pcbnew import with bundled Python. Review/install a pinned KiCadRoutingTools version only when routing is needed. Route critical power/analog nets deliberately; automate ordinary signals with fixed rules and placement.
6. Complete all release gates in architecture document and keep an evidence-backed review. No physical measurements exist yet. Portfolio publishing follows fabrication-ready design, not this architecture stage.

Files created in architecture phase: this handoff and `SYSTEM_ARCHITECTURE.md`; original screenshots unchanged. No tools installed, no orders placed, no PCB exports or portfolio published. No ERC/DRC/simulation has been run because no design files exist.
