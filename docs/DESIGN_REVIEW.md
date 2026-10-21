# Round LED Flash — Engineering Design Review

**Project:** Round LED Flash (Camera Ring Strobe)  
**KiCad Version:** 10.0.7 (Single-sheet hierarchical schematic, 4-layer annular PCB)  
**Date:** 2026-10-21  
**Author / Reviewer:** Hector Jimenez  
**Analyzers Run:**
- `analyze_schematic.py` (v1.4.0)
- `analyze_pcb.py --full` (v1.4.0)
- `cross_analysis.py` (v1.4.0)
- `analyze_emc.py` (v1.4.0)
- `analyze_thermal.py` (v1.4.0)
- `check_design_envelope.py` (13 hardware corner verification models)

---

## 1. Executive Summary & Review Verdict

**Verdict:** **Approved as Prototype Design Candidate.**  
The schematic design, part selection (100% MPN coverage across 94 unique parts), and analytical operating envelope have been verified with zero ERC errors, zero schematic-to-layout netlist parity errors, and 13 passing mathematical boundary models. The board layout demonstrates physical feasibility within the 84 mm OD / 55 mm ID ring form factor. Physical fabrication and testing are pending first-article prototype bring-up.

---

## 2. System Architecture & Specifications

| Subsystem | IC / Components | Key Parameters & Role |
| :--- | :--- | :--- |
| **Form Factor** | 4-layer FR-4, 1.6 mm | 84.0 mm Outer Diameter, 55.0 mm Central Lens Opening, Annular width 14.5 mm |
| **RF / MCU** | ESP32-C3-WROOM-02-N4 | 32-bit RISC-V @ 160 MHz, BLE 5.0, 2.4 GHz PCB antenna with dedicated keepout |
| **Battery Power** | 1S 18650 Li-ion + DW01A + 2× AO3400A | Keyed JST-PH connector, 2.79 V UVLO cutoff, 3 A overcurrent protection, 4 A fuse F1 |
| **USB-C Charging** | GCT USB4085 + TUSB320LAI + TP4056 | Type-C receptacle with active CC negotiation (1.5 A / 3.0 A qualified); 300 mA cell charge current |
| **Logic Supply** | TI TPS63070RNMR synchronous buck-boost | 3.3 V @ 500 mA continuous across 2.7 V to 4.35 V battery swing; auto-PFM/PWM |
| **Energy Storage** | 2× Eaton 5.0 F / 2.7 V supercapacitors (HV1020) | Series configuration: 2.5 F effective, 4.8 V nominal, 28.8 J stored energy |
| **Capacitor Charger** | ADI / LTC LTC3225EDDB | Active cell balancing, 60 mA constant-current charge rate, automatic charge termination |
| **LED Boost Converter** | MPS MP3435GL-Z high-efficiency boost | 4.8 V to 21.07 V boost, fused input (F2 4 A), input P-FET disconnect (`Q70`), 10 mΩ current shunt (`R270`) |
| **Constant-Current Sinks** | 2× onsemi CAT4101 | 200 mA nominal per channel (`R230`, `R231` = 2.49 kΩ) for warm and cool LED channels |
| **Optical Emitter** | Bridgelux Vesta Tunable COB (BXRV-TR-2765G) | Off-board 2700 K warm / 6500 K cool dual-channel array mounted on central metal heat spreader |
| **Hardware Safety Gate** | 2× ADI LTC6993-1 TimerBlocks | Non-retriggerable 1.403 ms maximum pulse window, 1.258 s minimum cooldown timer |
| **Physical Cutoff** | Alpha & Omega AO4407A P-FET | High-side power switch isolating 21 V rail from COB except during valid hardware flash window |
| **Thermal Sensing** | TDK 10 kΩ NTC (B57861S0103F040) | Pack thermistor on JST-GH connector (`J3`); onboard NTC near inner edge (`TH1`) |

---

## 3. Design Envelope & Physics Verification

All 13 parametric verification checks passed in `scripts/check_design_envelope.py`:

```
PASS permanent_bleed_to_half_volt_model_within_60min  (2967 s ~ 49.5 min to safe <0.5 V)
PASS ADC_off_leakage_below_unpowered_pin_limit        (0.111 V max unpowered leakage vs 0.3 V max)
PASS cap_ready_reachable_at_charger_min               (4.38 V to 4.63 V vs charger output)
PASS boost_ready_reachable_at_boost_min               (19.07 V to 20.23 V vs 21.07 V boost target)
PASS input_above_converter_min_3V                     (3.18 V min loaded input voltage)
PASS current_below_min_average_limit                  (3.88 A peak input current vs 4.46 A limit)
PASS cap_terminal_above_uvlo                          (3.37 V loaded cap terminal vs 3.29 V UVLO)
PASS nominal_requested_1ms_plus_50us_inside_window    (1.05 ms pulse inside 1.357 ms min window)
PASS hardware_cutoff_model_below_2ms                  (1.403 ms nominal cutoff window)
PASS minimum_cooldown_exceeds_1s                      (1.217 s min cooldown enforced in hardware)
PASS open_ntc_halts                                   (Comparator halts charging on sensor fault)
PASS zeroC_always_cold_inhibited                      (Low-temperature charge lockout verified)
PASS fortyfiveC_always_hot_inhibited                  (High-temperature charge lockout verified)
```

---

## 4. Analyzer Findings & Triage Matrix

| Rule ID | Severity | Category | Analyzer Finding Summary | Triage Decision / Engineering Assessment | Evidence Basis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PP-001** | Error | Power | U70.11 (IN) has no DC path to rail (`CAP_FUSED`) | **False Positive (Dismissed)**. `CAP_FUSED` is the fused 4.8 V supercapacitor rail from fuse `F2`. Analyzer expects standard rail names like `VCC`/`VDD`. | Raw-file verified |
| **VM-001** | Error | Signal Integrity | Domain crossing without level shifter on `CC_ALLOWED`, `BAT_PROT`, `CHARGE_ALLOWED` | **False Positive (Dismissed)**. Discrete comparator and transistor divider networks with safe thresholds (<3.3 V into ADC/MCU), not CMOS bus shorts. | Analytical / Schematic |
| **UC-003** | Warning | USB Compliance | `CC1` and `CC2` missing 5.1 kΩ pull-downs at `J1` | **False Positive (Dismissed)**. Active CC line control and source qualification are handled by `U3` (TUSB320LAI) per USB Type-C spec. | Datasheet verified |
| **PU-001** | Warning | Signal Integrity | Missing pull-ups on `CELL_OD`, `CAP_CHG_EN`, `BOOST_EN` | **False Positive (Dismissed)**. Pins are actively driven by supervisor and comparator outputs with pulldowns for default-off safety. | Schematic verified |
| **XV-001** | Warning | Parity | `LED1`, `TH2` in schematic but missing from PCB | **Expected Design Feature**. Offboard Bridgelux COB and offboard battery thermistor; symbols properly declared `(in_bom yes) (on_board no)`. | Raw-file verified |
| **TS-001** | Error | Thermal | `R270` (0.010 Ω 0.5 W) estimated Tj 175°C > 125°C | **False Positive (Pulsed Shunt)**. Analyzer assumed continuous DC load; current is pulsed only during the 1.0 ms flash window (<15 mJ energy). | Datasheet verified |
| **PS-002** | Warning | EMC | `/GND` plane split into islands on inner layer | **Layout Gap**. Annular ring routing requires completed ground stitching vias and flood fill around perimeter. | PCB layout verified |

---

## 5. Verification Basis & Limits

- **Datasheet Extractions:** Structured extractions cached in `datasheets/extracted/`:
  - MPS MP3435GL-Z (20-pin QFN, 16 A switch, pinout & compensation verified)
  - TI TPS63070RNMR (15-pin QFN, $10\text{ k}\Omega$ PS/SYNC pull-up verified)
  - TI TLV3011BIDBVR (SOT-23-6, 1.242 V precision internal reference verified)
- **Review Limits:**
  - Prototype design candidate: layout has been screened for mechanical and component clearance; final production panelization and factory assembly notes remain to be created.
  - Benchtop thermal and optical pulse verification must be performed on physical first-article hardware before full release.

---

## 6. Sign-off & Conclusion

The Round LED Flash architecture is sound, robustly protected, and ready for portfolio presentation as an advanced, hardware-interlocked camera flash prototype candidate.
