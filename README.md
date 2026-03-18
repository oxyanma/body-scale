# BioScale — Free OKOK Alternative for Body Composition

> **Open-source, ad-free, fully offline body composition analyzer for BLE smart scales (Chipsea chipset). A free alternative to the OKOK International app.**

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License" />
  <img src="https://img.shields.io/badge/platform-macOS-blue" alt="macOS" />
  <img src="https://img.shields.io/badge/python-3.10%2B-yellow" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/100%25-offline-brightgreen" alt="100% Offline" />
  <img src="https://img.shields.io/badge/no%20ads-no%20paywall-orange" alt="No Ads" />
</p>

---

## Why BioScale?

The **OKOK International** app is filled with ads, locks key features behind a paywall, and uses **inaccurate bioimpedance calculations**. BioScale was built as a **completely free alternative** that fixes all of that:

- **No ads, no login, no paywall** — all features unlocked from day one
- **100% offline** — your data never leaves your computer
- **Accurate BIA calculations** — formulas derived from reverse-engineering the OKOK CsAlgoBuilder plus validated scientific references (Janssen 2000, Mifflin-St Jeor, Kyle 2004, EWGSOP2)
- **20+ body composition metrics** — more than most commercial apps offer
- **Open source** — audit the code, contribute, or fork it

## Features

### Dashboard
- Real-time weight display with BMI classification bar
- Weight goal tracking with progress indicator
- Quick access to History, Composition, and Settings

### Body Composition (20+ metrics)
- **General:** Body Score, BMI, Obesity Degree, Ideal Weight, Metabolic Age
- **Fat:** Body Fat %, Fat Mass (kg), Visceral Fat Index, Subcutaneous Fat
- **Muscle:** Muscle Mass (% and kg), Skeletal Muscle Mass (SMM), FFMI, SMI, LBM, Bone Mass
- **Other:** Body Water (% and kg), Protein %, Basal Metabolic Rate (BMR)
- **Tier 2 (optional):** Waist-to-Hip Ratio (WHR), Waist-to-Height Ratio (WHtR), Cardiovascular Risk Score

### History & Comparison
- Full measurement history with timeline
- Side-by-side comparison between any two measurements
- Track your progress over time

### BLE Scale Communication
- Native BLE (Bluetooth Low Energy) connection via `bleak`
- Supports Chipsea V1 (FFF0→FFF4) and V2 (FFB0→FFB2/FFB3) protocols
- Auto-scan and connect to compatible scales
- Mock mode for testing without a physical scale

## Compatible Scales

BioScale works with smart scales using the **Chipsea chipset**, which is common in many affordable BLE body composition scales sold under brands like:

- OKOK / QardioBase-compatible scales
- Generic Bluetooth body fat scales (AliExpress, Amazon)
- Any scale advertising "OKOK International" app compatibility

## Installation

### Requirements
- Python 3.10+
- macOS with Bluetooth access (Apple Silicon or Intel)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/brumathey/bioscale-okok-alternative.git
cd bioscale-okok-alternative

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

The dashboard opens automatically at `http://localhost:8050`.

### macOS Bluetooth Permission

Your terminal app (Terminal, iTerm2, VS Code) needs Bluetooth permission:

**System Settings → Privacy & Security → Bluetooth** → Enable toggle for your terminal.

### Other Commands

```bash
# Scan for compatible BLE scales nearby
python main.py --scan

# Run in mock mode (no physical scale needed)
USE_MOCK_BLE=1 python main.py

# Debug mode
python main.py --debug
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, Flask |
| Frontend | Dash, Plotly, Dash Bootstrap Components |
| BLE | bleak |
| Database | SQLite via SQLAlchemy |
| Data | Pandas, NumPy |

## Scientific References

- **Body Fat %** — Reverse-engineered from OKOK CsAlgoBuilder (getBFR), with BMI-based fallback (Deurenberg 1991)
- **Skeletal Muscle Mass** — Janssen et al., *J Appl Physiol* 2000 (validated against MRI)
- **BMR** — Mifflin-St Jeor equation
- **Impedance Index** — Kyle et al. 2004 (H²/R)
- **Sarcopenia Risk** — EWGSOP2 thresholds (Cruz-Jentoft 2019)
- **Body Water** — Pace & Rathbun 1945 (73% of FFM)
- **Cardiovascular Risk** — AHA risk factor guidelines, Ashwell 2012 (WHtR)

## Data Storage

All data is stored locally in `~/.bioscale/bioscale.db` (SQLite). Nothing is sent to any server, ever.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Keywords:** OKOK alternative, OKOK International replacement, free body composition app, open source smart scale, BLE body fat scale, Chipsea scale app, bioimpedance analyzer, body composition calculator, OKOK without ads, OKOK free alternative, smart scale open source, body fat percentage calculator, BIA calculator
