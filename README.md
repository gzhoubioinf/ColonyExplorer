![ColonyExplorer](app/assets/Picture.png)

A *Klebsiella pneumoniae* discovery platform linking plate-to-fitness phenotypic data with established genomic typing (Kleborate) and predicted genetic associations (GWAS).

---

## Overview

ColonyExplorer is an interactive Streamlit application for high-throughput chemical genomics screening of *Klebsiella pneumoniae* clinical isolates. It integrates four independent data streams into a single browser:

- **Plate images** — high-density agar plate images (1536-well format) captured with IRIS
- **Phenotypic data** — colony morphology metrics (size, circularity, opacity, biofilm) extracted per-colony by [IRIS](https://github.com/critichu/Iris)
- **Absolute fitness** — pre-computed fitness scores per isolate per condition
- **Genomic data** — AMR genes, virulence loci, and sequence types from [Kleborate](https://github.com/klebgenomics/Kleborate)
- **GWAS results** — gene- and SNP-level associations from pan-genome and SNP GWAS analyses

**Dataset:** 1,462 isolates · 225 conditions · 214 conditions with fitness data · 2 GWAS modes

---

## Workflow and Methodology

![Workflow](app/assets/workflow.png)

---

## Features


| Feature | Description |
| --- | --- |
| Colony Inspection | Browse plate images for any isolate and condition; view four replicate crops with quantitative IRIS morphology metrics |
| Fitness Distribution | Visualise absolute fitness density across all isolates for any condition; see where a strain sits relative to the population with percentile annotation |
| Genomic Profiling | Full Kleborate strain overview: ST, K-type, AMR genes, virulence score, resistance score — linked to each colony |
| Gene-level GWAS | Pan-genome associations between gene presence/absence and fitness phenotypes; interactive table with fitness boxplots |
| SNP-level GWAS | SNP associations across conditions; allele distributions, annotations, and isolate presence per significant SNP |
| Seamless Navigation | Jump from any GWAS hit to Colony Viewer for any isolate — and back — with condition and gene context preserved |

---

## Project Structure

```text
ColonyExplorer/
├── app/
│   ├── main.py                  # Entry point; navigation and home page
│   ├── colony_picker.py         # Colony Viewer page
│   ├── strain_overview.py       # Genomic metadata panels
│   └── utils/
│       ├── data_loading.py      # CSV / Excel / IRIS file parsers
│       └── image_handling.py    # Plate image loading and colony extraction
├── config/
│   └── config.yaml              # File and directory paths
├── data/
│   ├── plate_images/            # *.JPG.grid.jpg plate images
│   ├── iris_measurements/       # *.iris measurement files
│   ├── GWAS_files/              # Pan-genome and SNP presence/absence files
│   ├── GWAS_results/            # GWAS summary result files
│   ├── strain_names.csv         # Strain ID → Row / Column / Plate mapping
│   ├── kleborate_all.tsv        # Kleborate output (genomic metadata)
│   └── condition_clean_tags_mapping.csv  # Human-readable condition labels
├── requirements.txt
└── README.md
```

---

## Data Format

### Plate images

Filename convention: `{Condition}-{Plate}-{Batch}_A.JPG.grid.jpg`

Example: `Ceftazidime-1ugml-1-1_A.JPG.grid.jpg`

### IRIS files

Filename convention: `{Condition}-{Plate}-{Batch}_A.JPG.iris`

Each file contains per-colony measurements and grid coordinates.

### Strain map (`data/strain_names.csv`)

Must contain at minimum: `ID`, `Row`, `Column`, `Plate`, `GenBank_acc`, `ENA_acc`.

### Kleborate file (`data/kleborate_all.tsv`)

Standard Kleborate output TSV; matched to strains via `strain`, `GenBank_acc`, or `ENA_acc`.

### GWAS files (`data/GWAS_files/`)

- `gene_presence_absence_roary.csv` — Roary pan-genome presence/absence matrix
- `pan_genome_reference.fa` — pan-genome reference sequences
- `significant_snps_presence_absence.csv` — SNP presence/absence matrix

---

## Configuration

Edit `config/config.yaml` to point to your data:

```yaml
files:
  strain_file: "data/strain_names.csv"
  kleborate_file: "data/kleborate_all.tsv"

directories:
  image_directory: "data/plate_images/"
  iris_directory:  "data/iris_measurements/"
```

---

## Live Demo

**[https://colonyexplorer.onrender.com](https://colonyexplorer.onrender.com)**

> Hosted on Render. The app may take ~30 seconds to wake up on first load.

---

## Installation

### Option A — Docker (recommended)

```bash
docker pull gzhoubioinf09/colonyexplorer:latest
docker run -p 8501:8501 gzhoubioinf09/colonyexplorer:latest
```

Open `http://localhost:8501` in your browser.

### Option B — Local install

**Requirements:** Python 3.11+

```bash
git clone https://github.com/gzhoubioinf/ColonyExplorer.git
cd ColonyExplorer

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Running the App

**Locally (after Option B install):**
```bash
streamlit run app/main.py
```
Opens at `http://localhost:8501`.

**On Render (or any server):**
```bash
streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
```

---

## Usage

### Colony Viewer

1. Navigate to **Colony Viewer** in the left panel.
2. Select a **Condition** — the plate/batch list updates automatically.
3. Select a **Plate / Batch**.
4. Choose a lookup method:
   - **Search by accession number** — select a strain from the dropdown, shown as `ID (Accession)`. Reference strains without an accession show `ID (NA)`; if the same ID appears at multiple wells, the well position is appended as `ID (NA, R#, C#)`.
   - **Enter grid position** — enter Row (1–32) and Column (1–48) directly.
5. Optionally adjust which **Metrics** to display.
6. Click **Analyse** to load the plate image and display results.

### Gen-GWAS Explorer

1. Navigate to **Gen-GWAS Explorer**.
2. Select a condition and sample from the dropdowns.
3. Browse the GWAS results table; filter by significance threshold.
4. Expand any gene to view the isolate presence/absence table and pan-genome sequence.
5. Click any isolate row to jump directly to Colony Viewer.

### SNP-GWAS Explorer

1. Navigate to **SNP-GWAS Explorer**.
2. Select a condition and SNP from the results table.
3. View isolates carrying the SNP, sorted by p-value or effect size.
4. Click any isolate row to jump to Colony Viewer.

---

## Available Metrics

| Metric | Description |
| --- | --- |
| Colony size | Total colony area in pixels |
| Circularity | Roundness (1 = perfect circle) |
| Opacity | Optical density proxy for colony density |
| Colony color intensity | Mean pixel intensity of the colony |
| Biofilm area size | Area covered by biofilm |
| Biofilm color intensity | Mean intensity within the biofilm region |
| Biofilm area ratio | Fraction of colony area covered by biofilm |
| Size normalized color intensity | Color intensity corrected for colony size |
| Mean sampled color intensity | Sampled mean intensity |
| Average pixel saturation | Mean HSV saturation across colony |
| Max 10% opacity | 90th-percentile opacity value |

---

## References

If you use ColonyExplorer in your research, please cite our work:

- *(citation forthcoming)*

This application relies on the following foundational workflows and tools. Please also consider citing them:

- **High-Throughput Phenotypic Screening Pipeline:**
  Williams G., Ahmad H., Sutherland S., et al. (2025). High-throughput chemical genomic screening: a step-by-step workflow from plate to phenotype. *mSystems*, 10(12), e00885-25. DOI: [10.1128/msystems.00885-25](https://doi.org/10.1128/msystems.00885-25)

- **Kleborate (Genomic Profiling):**
  Lam, M. M. C., et al. (2021). A genomic surveillance framework and genotyping tool for *Klebsiella pneumoniae* and its related species complex. *Nature Communications*, 12(1), 4188. DOI: [10.1038/s41467-021-24448-3](https://doi.org/10.1038/s41467-021-24448-3)

- **IRIS (Phenotypic Image Analysis):**
  Kritikos, G., Banzhaf, M., Herrera-Dominguez, L., et al. (2017). A tool named Iris for versatile high-throughput phenotyping in microorganisms. *Nature Microbiology*, 2(5), 17014. DOI: [10.1038/nmicrobiol.2017.14](https://doi.org/10.1038/nmicrobiol.2017.14)

- **Scoary (Bacterial GWAS):**
  Brynildsrud, O., Bohlin, J., Scheffer, L., & Eldholm, V. (2016). Rapid scoring of genes in microbial pan-genome-wide association studies with Scoary. *Genome Biology*, 17(1), 238. DOI: [10.1186/s13059-016-1108-8](https://doi.org/10.1186/s13059-016-1108-8)

- **Panaroo (Pan-genome Pipeline):**
  Tonkin-Hill, G., MacAlasdair, N., Ruis, C., et al. (2020). Producing polished prokaryotic pangenomes with the Panaroo pipeline. *Genome Biology*, 21(1), 180. DOI: [10.1186/s13059-020-02090-4](https://doi.org/10.1186/s13059-020-02090-4)

---

## Contact and Collaboration

ColonyExplorer is a joint project developed by the
**[Infectious Disease Epidemiology Lab](https://ide.kaust.edu.sa/)** (KAUST)
and the **Banzhaf Lab** (Newcastle University).

**Support and Inquiries:**

| Name | Email |
| :--- | :--- |
| **Ge Zhou (PhD student)** | [ge.zhou@kaust.edu.sa](mailto:ge.zhou@kaust.edu.sa) |
| **Danesh Moradigaravand (PI)** | [danesh.moradigaravand@kaust.edu.sa](mailto:danesh.moradigaravand@kaust.edu.sa) |
| **Manuel Banzhaf (PI)** | [manuel.banzhaf@newcastle.ac.uk](mailto:manuel.banzhaf@newcastle.ac.uk) |

---

## License

See [LICENSE](LICENSE).
