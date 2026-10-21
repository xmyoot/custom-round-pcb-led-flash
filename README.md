# Round LED Flash

**Engineering draft — incomplete electrical design; not for fabrication.**

Open `Round_LED_Flash.kicad_pro` in **KiCad 10**. This is the only authoritative project, with one `.kicad_sch` and one `.kicad_pcb`. Project libraries are under `libraries/`; generated checks and previews are under `analysis/`.

The implemented core contains the ESP32-C3 module, 3.3 V buck-boost circuit, switched battery/capacitor ADC sensing, shutter, two logic indicators, UART programming pads, USB/battery connector interfaces, four supercapacitors, and mounting holes. Charging, cell protection, capacitor charging/balancing/isolation, the LED boost/current drivers, and hardware flash timing remain to be implemented.

See [implementation status](docs/IMPLEMENTATION_STATUS.md) for the actual state, component decisions, verification limits, and next engineering work. The architecture document is a requirements baseline; its provisional LED voltage and capacitor assumptions must not be used as frozen design values.

Do not regenerate the mechanical seed after electrical placement. Scripts refuse to overwrite a routed board. When using external generators, close/reopen KiCad editors so their in-memory documents do not overwrite external changes.
