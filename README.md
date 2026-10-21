# Round LED Flash

**Prototype design candidate — layout and release verification in progress; not for fabrication yet.**

Open `Round_LED_Flash.kicad_pro` in KiCad10.0.7. This is the single authoritative project. Project libraries are under `libraries/`; source generators are under `scripts/`; evidence is under `analysis/` and `datasheets/`.

The candidate now includes the ESP32-C3, 3.3V buck-boost, protected USB-C charging, DW01 cell protection, balanced4.8V supercapacitor charging,21.07V LED boost, two nominal200mA current sinks, independent flash/cooldown timers, physical LED power cutoff, rail interlocks, and service discharge.

Read `docs/IMPLEMENTATION_STATUS.md` for actual checks and remaining work. The original architecture is historical where it conflicts with implementation. Source files are versioned with Git, rather than named PCB copies. Close/reopen KiCad editors after external generation to avoid saving stale in-memory documents.
