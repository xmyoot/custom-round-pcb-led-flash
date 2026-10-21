# Prototype bring-up and qualification

This is a design qualification plan. No physical measurements have been made. Do not represent calculated results as tested performance.

## Assembly and fixture

Use an isolated 18650 cell/harness with correct polarity, an insulated rear holder, and a bonded isolated TDK pack thermistor. The battery connector is JST-PH; the thermistor connector is JST-GH. Do not connect cell negative directly to protected board ground: that bypasses the low-side protection FETs. The COB needs a separate electrically appropriate heat spreader and insulated leads through the center opening. Establish the complete enclosure, holder and optical assembly mechanically before use.

Keep USB disconnected for flashing/programming. USB presence deliberately inhibits system operation. Use a battery simulator or current-limited supply at the cell input for initial logic tests. UART fixture TX/RX are 3.3V logic; TP2 is a voltage sense reference, not an independent power input. Fixture EN/BOOT controls must be open drain. Match fixture ground to protected GND, never raw cell negative.

## Initial electrical tests

1. Inspect polarity, QFN orientation, exposed pads, solder bridges and capacitor vent clearance. Check resistance from each rail to ground before applying power.
2. Start without the external COB or supercapacitors fitted. Apply a current-limited 3.7V source to the cell interface. Verify protected battery rail, 3.3V regulation, supervisor operation and absence of excessive idle current. Increase current limit only after verifying regulation.
3. Verify power-off ADC nodes remain below 0.3V with a charged simulated capacitor rail and battery present. The 22k dividers model about 0.111V at 5uA leakage; inspect behavior during startup/shutdown and at temperature.
4. Program the ESP32-C3 through the buffered UART fixture. Initialize ARM and both requests LOW; drive GPIO2 trigger LOW after boot. Enforce at least 1.3s after every reset before arming. Cooldown hardware does not retain state without power.
5. Sweep battery voltage. Record running cutoff and cold-start threshold separately: the nominal 2.79V supervisor threshold is below TPS63070's specified 3V minimum startup input. Confirm stable shutdown and no repeated high-current restart near depletion.

## USB and cell charging

Use a USB-C source advertising 1.5A or 3A. A default-current source is intentionally rejected. Confirm no cell-charge current until source qualification. Measure eFuse clamp and current limit using a controlled source; do not inject unbounded voltage transients into a cell.

Measure nominal approximately 300mA cell-charge current, termination and thermal regulation. Substitute precision resistors at the pack-NTC connector for the TDK R/T8016 endpoints. Verify inhibition at 0C and 45C, open circuit and short circuit. Confirm U8 inhibits CE on a short, rather than relying on TP4056 TEMP alone. Qualify charging over component tolerances and the chosen cell's limits.

## Capacitor bank and boost

Fit correctly polarized Eaton cells and first charge through the intended balancing charger under current monitoring. Measure each cell, total bank voltage, balance, charging time and steady bleeder current. The nominal 4.8V bank stores 28.8J. Do not short test points or connect an ammeter directly across it.

Verify recharge inhibition during USB insertion, system-off and an active hardware flash window. Verify active service discharge when logic power-good is low. Its MOSFET loses enhancement at low voltage; the permanent 330ohm resistor provides the final bleed. The conservative RC calculation is under 60min to 0.5V, but always measure TP7 and each cell before service.

With the COB disconnected, verify boost startup, approximately 21.07V output, input disconnect and current-limit response using an electronic load. Measure SW ringing, MOSFET VGS, current-sense waveform and reservoir ripple with short probe ground springs or suitable differential probes. Check compensation using load steps and, preferably, loop-gain measurement. The 120k/33n/47p network is an analytical starting point; compensation requires hardware qualification.

## Optical pulse and fault tests

Mount the COB on its heat spreader before connection. Start with one channel, reduced request width, and current monitoring. Confirm approximately 200mA regulated current per channel. Characterize current over battery voltage and temperature rather than extrapolating the CAT4101 350mA test specification.

For each pulse, wait for GPIO7 permission, issue a trigger edge, wait 50us for the high-side switch to settle, then command 0.5–1ms channel pulses. End both requests before the minimum calculated hardware window of approximately 1.357ms. The nominal window is 1.403ms; nominal cooldown is 1.258s during continuous power.

Capture both channel currents, LED anode voltage, timer outputs, bank voltage and boost output. Test warm, cool and simultaneous requests; stuck-high requests; repeated triggers; reset; battery brownout; USB insertion; open LED; and sensor faults. Verify physical LED cutoff bounds illumination even when firmware requests remain high. Do not add bulk capacitance after the high-side LED cutoff.

Repeat at 0C/40C, near the loaded-bank UVLO threshold, with maximum practical bank ESR and capacitance tolerance, and after repeated flashes. Measure the actual converter efficiency and total series-path resistance against the design-envelope assumptions. Use a photodiode to measure optical pulse timing and afterglow.

## Thermal and EMC evidence

Record charger, boost, current-sink, cell and supercapacitor temperatures during charging, repeated simultaneous flashes, and fault tests. Inspect the RF antenna clearance with the final enclosure and rear cell installed. Perform near-field scans around both switching converters and conducted checks at USB/battery leads, followed by applicable radiated/ESD testing. A module approval or automated EMC risk report does not establish final-product compliance.

Retain oscilloscope captures, thermal images, source conditions, component revision, firmware hash, and pass/fail limits in the portfolio evidence. State failures and resulting revisions explicitly.
