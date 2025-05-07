# dpest Multi-Treatment Calibration Script

This repository contains an example script that demonstrates how to use [`dpest`](https://github.com/yourusername/dpest) to **calibrate multiple DSSAT treatments or genotypes simultaneously** using a simple Python `for` loop. It automates the full workflow of generating PEST files, validating inputs, adjusting observation weights, and running the calibration.

## 🔍 What It Does

- Iterates through a list of treatment-cultivar pairs.
- For each cultivar:
  - Generates PEST input files using `dpest` (TPL, INS, PST).
  - Validates input/output files using DSSAT and PEST utilities.
  - Optionally fills missing simulation lines using `uplantgro`.
  - Adjusts observation weights using `pwtadj1`.
  - Runs PEST calibration.

The script is modular and can be adapted to use either:
- A structured `config.yaml` file (as included), or
- Plain Python dictionaries/lists if preferred.

## 📁 Folder Structure

```
pest_cal1/
├── config.yaml         # (Optional) Configuration file with treatments, file paths, variables, and commands
├── [Cultivar_1]/       # Auto-generated folder with PEST files and outputs
├── [Cultivar_2]/       # ...
```

## ⚙️ Requirements

- Python 3.8+
- [`dpest`](https://github.com/yourusername/dpest)
- `pyemu`
- DSSAT utilities:
  - `tempchek.exe`
  - `inschek.exe`
  - `PEST.exe`
  - `pwtadj1.exe`

Make sure these executables are accessible in your system PATH or located in the working directory.

## 🚀 How to Use

1. Clone this repo:
   ```bash
   git clone https://github.com/yourusername/dpest-multi-calibration.git
   cd dpest-multi-calibration
   ```

2. Update `config.yaml` (optional) or modify the script to pass lists manually.

3. Run the script:
   ```bash
   python calibrate_multi_genotypes.py
   ```

Each genotype/treatment will be processed in a separate folder under the `pest_cal1/` directory.

## 🧠 Notes

- The script can be adapted to include or exclude `PlantGro.OUT` variables.
- You can bypass the YAML approach entirely by storing configuration directly in Python structures.

## 📞 Contact

For questions or suggestions, feel free to open an [issue](https://github.com/DS4Ag/dpest/issues) or reach out directly.

---