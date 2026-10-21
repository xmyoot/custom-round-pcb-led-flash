# Implementation status — 2026-10-20

## Actual state

The authoritative root files now exist:

- `Round_LED_Flash.kicad_pro`
- `Round_LED_Flash.kicad_sch`
- `Round_LED_Flash.kicad_pcb`

KiCad 10.0.7 and its bundled `pcbnew` import were exercised successfully. The schematic and PCB contain **65 symbols/footprints**, including non-BOM mounting holes and test pads. There are no routed tracks, ground planes, or fabrication outputs. The schematic is deliberately marked incomplete.

Implemented core: ESP32-C3-WROOM-02-N4; TPS63070 adjustable 3.3 V supply; 1.5 µH logic inductor; boot/reset passives; ADC networks; power-good-controlled high-side sensing switches; shutter and slide switches; BLE/ready indicators; local NTC interface; UART pogo pads; USB/battery interfaces; 2S2P capacitor bank; three M2.5 mounting holes. The battery connector's raw cell terminals are not yet connected to the protected system rail because the protection stage is absent.

## Checks actually run

| Check | Result | Meaning |
|---|---|---|
| KiCad board DRC with schematic parity | 0 geometric violations, 125 unconnected items, 0 parity issues | Placed core matches the schematic; it is unrouted |
| KiCad schematic ERC | 2 errors, 5 warnings | Missing power-stage connections and intentionally unfinished interfaces |
| Native netlist export | Succeeded | Source for PCB pad-net assignments, including native no-connect nets |
| Schematic SVG export and visual inspection | Succeeded | Draft readable at zoom; final schematic composition remains open |
| PCB top render and visual inspection | Succeeded | Placement preview only; some custom footprints lack 3D bodies |
| BOM export | Succeeded | Draft grouped BOM; many exact passive MPNs and sourcing checks remain |

`analysis/core_parity_drc.rpt` is the latest PCB result. `analysis/floorplan_drc.rpt` records the earlier mechanical-only seed and is not a release report. ERC's two undriven supply errors reflect the absent battery/protection circuits. Its isolated labels are HW_OK, CC1, CC2, CELL_P, and CELL_N_RAW. No checks were suppressed to hide these.

This is not the full KiCad skill design review. Analyzer, SPICE, EMC, thermal, lifecycle, Gerber, and manufacturing assessments are pending the complete circuit and layout. No physical measurements exist.

## Component findings and departures

**COB candidate:** Bridgelux **BXRV-TR-2765G-10A0-A-23**. The manufacturer's current DS350 PDF was downloaded and read. It provides a documented 2700 K / 6500 K two-channel emitter, with a roughly 18 V operating envelope and a combined-current limit. The 2700 K endpoint is a departure from the requested ~3000 K. A 10.5 V boost cannot drive this part. The COB is not yet on the schematic or BOM, and source availability is not verified. Its selection requires completing the driver/power budget.

**Flash direction under evaluation:** approximately 20.5–21 V regulated output using **MP3435GL-Z**, with two **CAT4101TV-T75** current sinks. Consider about 300 mA nominal per channel, allowing tolerance below the COB's combined-current limit. These are candidates, not implemented or frozen circuits. CAT4101 is a five-lead D2PAK with a grounded tab, not SOT-223. Its pulse timing specifications require checking and bench confirmation. Current tolerances, sink compliance, converter duty cycle, compensation, input disconnect, current limiting and transient headroom remain open.

**Capacitor selection for fit:** four Eaton **HV1020-2R7505-R**, 5 F / 2.7 V cells, arranged as two parallel groups in series. This provides 5 F nominal bank capacitance and 40 mΩ maximum initial cell-bank ESR at the specified test conditions, before interconnects. The old 0.5 F architecture assumption is superseded for this draft. Aging and temperature increase ESR; nominal DC capacitance is not proof of 1 ms pulse performance. Each can can reach **10.5 mm diameter and 22.3 mm height**. Stored energy is **44.1 J at 4.2 V**. Controlled recharge, balancing, fault isolation, and discharge are still absent; the two 2.2 kΩ resistors do not establish transient overvoltage protection.

**USB connector:** GCT **USB4085-GF-A**, with actual through-hole contacts and shell stakes. The manufacturer drawing was downloaded. Its dense land pattern requires **0.15 mm local pad clearance**; ordinary trace/clearance targets remain 0.20 mm. Fabricator suitability remains a release gate.

**USB charging direction:** use **TUSB320LAI** sink-current detection with TP4056 rather than assume that 80 mA is supported by every TP4056 variant. A possible conservative implementation permits ~300 mA charging only when the Type-C source advertises at least 1.5 A; legacy/default-current charging would then be unavailable. This behavior has not been implemented or frozen. TUSB320 provides its own Rd termination; do not add duplicate external Rd resistors. Resolve VBUS transient/overvoltage protection, its independent logic supply, charger CE behavior and pack-temperature sensing before wiring.

**ADC correction:** permanent battery/capacitor dividers can back-power an unpowered ESP32. The draft now switches each divider's upper leg using its own PMOS and an NMOS driven by TPS63070 power-good. Each PMOS gate returns to its own source. The TPS63070 data sheet states PG low when EN is low. Independent pin, leakage, startup, and shutdown checks remain part of verification. The 2N7002 orderable suffix/lifecycle needs resolution: a related `-7` listing is NRND; do not release the present draft BOM unchanged.

## Mechanical and footprint limits

The board retains 84 mm OD, a 55 mm opening, four copper layers, and 1.6 mm nominal thickness. The ESP32 antenna extends approximately 5 mm beyond the PCB perimeter, and the module body extends about 0.6 mm into the opening. This preserves the specified PCB outline but enlarges the component/enclosure envelope. Battery, heat spreader, enclosure, fasteners and wiring do not yet have a validated 3D assembly.

The antenna rule area blocks copper, pads and vias on every copper layer. A custom placement rule exempts the RF module itself and disallows other footprints in that area. The project-derived module footprint retains its electrical pad coordinates and exposed ground pad, removes stock 0.2 mm open via-in-pad holes, and removes edge-crossing silk. Separate ground stitching must be designed during routing.

TPS63070 RNM0015A and Coilcraft XFL4020 footprints were created in the project library. The TI land pattern was checked visually from its package drawing, including its unusual power leads and solder-mask-defined pads. The Coilcraft dimensions were read from the manufacturer drawing's extracted data; independent visual and dimensional checking remains open. Zero DRC errors does not prove that a transcribed footprint matches a manufactured component.

Reference silkscreen is intentionally unfinished and currently hidden. The preview uses default green mask; the requested matte black mask and ENIG finish are still manufacturing requirements and have not been applied as a released stackup.

## Next required engineering work

1. Close the real emitter/driver/current envelope, source availability, boost input sag, pulse settling, and cap aging/temperature budget.
2. Complete TP4056/DW01 protection from exact manufacturer circuits; keep CELL_N_RAW separate from protected GND. Add a pack-temperature sensor connection and proper USB power qualification/protection.
3. Complete reverse-blocking, limited cap recharge, per-section protection/balancing, boost input isolation, and service discharge. Recalculate charge time for 5 F.
4. Implement hardware pulse cutoff and cooldown. **LTC6993-1** is the rising-edge non-retriggerable variant; **-2 is retriggerable and must not be substituted**. Two timers were considered, but neither is currently on the schematic. Verify the exact divider codes, resistor range and timing limits before adoption.
5. Finish the schematic, MPNs, independent symbol/footprint checks, and all-component floorplan before routing. Improve schematic composition with local circuit wiring and larger functional group labels.
6. Route and validate critical power/sense loops deliberately; use a pinned routing tool for ordinary signals only. KiCadRoutingTools has not been installed or run.
7. Complete the architecture's release gates and full skill review, then generate and inspect manufacturing files. Portfolio assets follow that stage.

## Reproducibility

Run the schematic generator with KiCad's Python, then export a fresh native netlist with KiCad CLI before `sync_core_pcb.py`. That synchronizer preserves existing placement, transfers exact native net names and symbol fields, and rejects stale netlists. `place_core.py` is an unrouted-stage placement screen using conservative bounds plus native DRC. It is not a router or electrical optimizer. The mechanical seed generator now refuses to overwrite the electrically populated board.

Downloaded evidence is in `datasheets/`; `sources.json` records successful PDFs and failed fetches. Manufacturer website access was used because DigiKey API credentials were absent. A LCSC search for MP3435 returned an unrelated NXP MCU; that result was rejected and not added to the BOM. No stock or price claim is made.
