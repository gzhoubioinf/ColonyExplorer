import sys
import os
import yaml
import pandas as pd
import streamlit as st

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.colony_picker import run_colony_viewer, list_conditions, find_available_runs


def load_config(config_path="config/config.yaml"):
    with open(config_path, "r") as fh:
        return yaml.safe_load(fh)


_ACCENT       = "#0d9488"
_ACCENT_BG    = "rgba(13,148,136,0.08)"
_ACCENT_MID   = "rgba(13,148,136,0.18)"
_FONT_IMPORT  = "@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');"

_WORKFLOW_CSS = f"""
<style>
{_FONT_IMPORT}
.wf-row {{ display:flex; align-items:stretch; gap:1rem; width:100%; }}
.wf-step {{
    flex:1; text-align:center; padding:1.4rem 1rem;
    border:1px solid rgba(128,128,128,0.2); border-radius:12px;
    background:{_ACCENT_BG};
}}
.wf-arrow {{
    display:flex; align-items:center; justify-content:center;
    flex:0 0 2.5rem;
    font-family:'Material Symbols Outlined'; font-size:1.8rem;
    color:{_ACCENT}; opacity:0.5;
}}
.wf-icon {{
    font-family:'Material Symbols Outlined'; font-size:2.8rem;
    font-weight:200; display:block; margin-bottom:0.5rem; color:{_ACCENT};
}}
.wf-num {{
    display:inline-block; font-size:0.68rem; font-weight:700;
    letter-spacing:0.1em; text-transform:uppercase;
    color:{_ACCENT}; background:{_ACCENT_MID};
    border-radius:20px; padding:0.1rem 0.55rem; margin-bottom:0.4rem;
}}
.wf-title {{ font-weight:700; font-size:0.95rem; margin-bottom:0.4rem; }}
.wf-desc  {{ font-size:0.82rem; opacity:0.8; line-height:1.45; }}
</style>
"""

_FEATURE_CSS = f"""
<style>
{_FONT_IMPORT}
.fc-grid {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.75rem; width:100%; }}
.fc {{
    border:1px solid rgba(128,128,128,0.2); border-top:3px solid {_ACCENT};
    border-radius:10px; padding:1rem 1.1rem;
}}
.fc-icon {{
    font-family:'Material Symbols Outlined'; font-size:1.6rem;
    font-weight:300; margin-bottom:0.3rem; color:{_ACCENT}; display:block;
}}
.fc-title {{ font-weight:700; font-size:0.97rem; margin-bottom:0.25rem; }}
.fc-desc  {{ font-size:0.85rem; opacity:0.85; line-height:1.45; }}
</style>
"""

_FEATURES = [
    ("image_search", "Colony Inspection",
     "Browse plate images for any isolate and condition. View four replicate crops "
     "alongside quantitative IRIS morphology metrics — size, circularity, opacity, and biofilm."),
    ("bar_chart", "Fitness Distribution",
     "Visualise the absolute fitness density across all isolates for any condition. "
     "See where a selected strain sits relative to the population, with percentile annotation."),
    ("genetics", "Genomic Profiling",
     "Full Kleborate strain overview: sequence type, K-type, AMR genes, virulence score, "
     "and resistance score — linked directly to each colony."),
    ("scatter_plot", "Gene-level GWAS",
     "Explore pan-genome associations between gene presence/absence and fitness phenotypes. "
     "Interactive table with fitness boxplots comparing carriers vs non-carriers."),
    ("biotech", "SNP-level GWAS",
     "Browse single-nucleotide polymorphism associations across conditions. "
     "Inspect allele distributions, annotations, and isolate presence for each significant SNP."),
    ("compare_arrows", "Seamless Navigation",
     "Jump directly from any GWAS hit to the Colony Viewer for any isolate — "
     "and back — with condition and gene context preserved across pages."),
]


def render_home():
    # ---- Hero banner ----
    st.html("""
    <style>
    .hero {
        background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
        border-radius: 14px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
    }
    .hero h1 {
        margin: 0 0 0.4rem;
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.02em;
    }
    .hero p {
        margin: 0;
        color: rgba(255,255,255,0.88);
        font-size: 1rem;
        line-height: 1.6;
    }
    </style>
    <div class="hero">
        <h1>ColonyExplorer</h1>
        <p>A genotype–phenotype browser for <em>Klebsiella pneumoniae</em> — linking plate images, IRIS morphology, absolute fitness, and Kleborate genomic data.</p>
    </div>
    """)

    # ---- Stats bar ----
    _s1, _s2, _s3, _s4 = st.columns(4)
    with _s1:
        st.metric("Isolates", "1,462")
    with _s2:
        st.metric("Conditions", "225")
    with _s3:
        st.metric("GWAS modes", "2")
    with _s4:
        st.metric("Conditions with fitness", "214")

    st.divider()

    # ---- Quick-launch cards ----
    st.markdown("#### Explore the data")
    _q1, _q2, _q3 = st.columns(3)
    with _q1:
        st.html(f"""
        <div style="border:1px solid rgba(128,128,128,0.2);border-radius:12px;
                    padding:1.2rem;background:{_ACCENT_BG};margin-bottom:0.5rem;">
            <span style="font-family:'Material Symbols Outlined';font-size:2rem;color:{_ACCENT};">image_search</span>
            <div style="font-weight:700;font-size:1rem;margin:0.3rem 0 0.2rem;">Colony Viewer</div>
            <div style="font-size:0.85rem;opacity:0.8;line-height:1.4;">
                Inspect plate images, colony morphology, fitness distribution,
                and full genomic profiles for any isolate.</div>
        </div>""")
        if st.button("Open Colony Viewer →", key="home_cv", use_container_width=True):
            st.session_state.page = "Colony Viewer"
            st.rerun()
    with _q2:
        st.html(f"""
        <div style="border:1px solid rgba(128,128,128,0.2);border-radius:12px;
                    padding:1.2rem;background:{_ACCENT_BG};margin-bottom:0.5rem;">
            <span style="font-family:'Material Symbols Outlined';font-size:2rem;color:{_ACCENT};">scatter_plot</span>
            <div style="font-weight:700;font-size:1rem;margin:0.3rem 0 0.2rem;">Gene-level GWAS</div>
            <div style="font-size:0.85rem;opacity:0.8;line-height:1.4;">
                Explore pan-genome associations between gene presence/absence
                and fitness across 214 conditions.</div>
        </div>""")
        if st.button("Open Gen-GWAS Explorer →", key="home_gwas", use_container_width=True):
            st.session_state.page = "Gen-GWAS Explorer"
            st.rerun()
    with _q3:
        st.html(f"""
        <div style="border:1px solid rgba(128,128,128,0.2);border-radius:12px;
                    padding:1.2rem;background:{_ACCENT_BG};margin-bottom:0.5rem;">
            <span style="font-family:'Material Symbols Outlined';font-size:2rem;color:{_ACCENT};">biotech</span>
            <div style="font-weight:700;font-size:1rem;margin:0.3rem 0 0.2rem;">SNP-level GWAS</div>
            <div style="font-size:0.85rem;opacity:0.8;line-height:1.4;">
                Browse SNP associations across conditions with allele distributions,
                annotations, and isolate presence.</div>
        </div>""")
        if st.button("Open SNP-GWAS Explorer →", key="home_snp", use_container_width=True):
            st.session_state.page = "SNP-GWAS Explorer"
            st.rerun()

    st.divider()

    # ---- Workflow ----
    st.markdown("#### Workflow and Methodology")
    _WORKFLOW = [
        ("analytics", "Step 1", "Phenotypic Data Generation",
         "Clinical strains are arrayed on agar plates during high-throughput chemical genomics screening. "
         "Plate images are processed by IRIS to extract quantitative colony morphology metrics, "
         "from which absolute fitness values per condition are calculated."),
        ("genetics", "Step 2", "Genotypic Data Generation",
         "Genomes of the same strains are analysed with Kleborate to identify sequence types, "
         "AMR genes, and virulence determinants."),
        ("hub", "Step 3", "Data Integration",
         "ColonyExplorer links both streams — physical colony measurements, fitness data, "
         "GWAS results, and genomic profiles — into a single interactive browser."),
    ]
    wf_steps = ""
    for i, (icon, num, title, desc) in enumerate(_WORKFLOW):
        if i > 0:
            wf_steps += '<div class="wf-arrow material-symbols-outlined">arrow_forward</div>'
        wf_steps += (
            f'<div class="wf-step">'
            f'<span class="wf-icon material-symbols-outlined">{icon}</span>'
            f'<span class="wf-num">{num}</span>'
            f'<div class="wf-title">{title}</div>'
            f'<div class="wf-desc">{desc}</div>'
            f'</div>'
        )
    st.html(_WORKFLOW_CSS + f'<div class="wf-row">{wf_steps}</div>')

    st.divider()

    # ---- Features ----
    st.markdown("#### Key features")
    fc_items = "".join(
        f'<div class="fc">'
        f'<span class="fc-icon material-symbols-outlined">{icon}</span>'
        f'<div class="fc-title">{title}</div>'
        f'<div class="fc-desc">{desc}</div>'
        f'</div>'
        for icon, title, desc in _FEATURES
    )
    st.html(_FEATURE_CSS + f'<div class="fc-grid">{fc_items}</div>')


def render_about():
    st.title("About ColonyExplorer")
    st.markdown(
        """
        ColonyExplorer is a *Klebsiella pneumoniae* discovery platform linking
        plate-to-fitness phenotypic data with established genomic typing (Kleborate)
        and predicted genetic associations (GWAS).

        The app streamlines high-throughput chemical genomics screening for clinical
        isolates by integrating colony quantification from
        [IRIS](https://github.com/critichu/Iris) with comprehensive whole-genome
        analysis. By unifying strain typing, antimicrobial resistance (AMR), and
        virulence identification via
        [Kleborate](https://github.com/klebgenomics/Kleborate), pangenome dynamics
        via [Panaroo](https://github.com/gtonkinhill/panaroo), and variant calling
        via [Snippy](https://github.com/tseemann/snippy), the platform provides a
        robust interface for bridging physical phenotypes with high-resolution
        genomic data.
        """
    )

    st.divider()

    st.markdown("### Dataset")
    st.markdown(
        """
        | Data layer | Description |
        | :--- | :--- |
        | Plate images | 1536-well agar plates imaged across chemical and antibiotic conditions |
        | Morphology metrics | Colony size, circularity, opacity, biofilm area and more (IRIS) |
        | Absolute fitness | Pre-computed fitness scores per isolate per condition |
        | Genomic metadata | Sequence type, AMR genes, virulence loci (Kleborate) |
        | Gene-level GWAS | Pan-genome gene–fitness associations (Panaroo + Scoary) |
        | SNP-level GWAS | SNP–fitness associations from whole-genome SNP calls (Snippy + Scoary))|
        """
    )

    st.divider()

    st.markdown("### References")
    st.markdown(
        """
        If you use ColonyExplorer in your research, please cite our work:
        * *(citation forthcoming)*

        This application relies on the following tools and workflows — please also cite them:

        * **High-Throughput Phenotypic Screening Pipeline:**
          Williams G., Ahmad H., Sutherland S., et al. (2025). High-throughput chemical genomic screening: a step-by-step workflow from plate to phenotype. *mSystems*, 10(12), e00885-25. DOI: [10.1128/msystems.00885-25](https://doi.org/10.1128/msystems.00885-25)

        * **Kleborate (Genomic Profiling):**
          Lam, M. M. C., et al. (2021). A genomic surveillance framework and genotyping tool for *Klebsiella pneumoniae* and its related species complex. *Nature Communications*, 12(1), 4188. DOI: [10.1038/s41467-021-24448-3](https://doi.org/10.1038/s41467-021-24448-3)

        * **IRIS (Phenotypic Image Analysis):**
          Kritikos, G., Banzhaf, M., Herrera-Dominguez, L., et al. (2017). A tool named Iris for versatile high-throughput phenotyping in microorganisms. *Nature Microbiology*, 2(5), 17014. DOI: [10.1038/nmicrobiol.2017.14](https://doi.org/10.1038/nmicrobiol.2017.14)

        * **Snippy (SNP Calling):**
          Seemann, T. (2015). Snippy: fast bacterial variant calling from NGS reads. GitHub. [https://github.com/tseemann/snippy](https://github.com/tseemann/snippy)

        * **Scoary (Bacterial GWAS):**
          Brynildsrud, O., Bohlin, J., Scheffer, L., & Eldholm, V. (2016). Rapid scoring of genes in microbial pan-genome-wide association studies with Scoary. *Genome Biology*, 17(1), 238. DOI: [10.1186/s13059-016-1108-8](https://doi.org/10.1186/s13059-016-1108-8)

        * **Panaroo (Pan-genome Pipeline):**
          Tonkin-Hill, G., MacAlasdair, N., Ruis, C., et al. (2020). Producing polished prokaryotic pangenomes with the Panaroo pipeline. *Genome Biology*, 21(1), 180. DOI: [10.1186/s13059-020-02090-4](https://doi.org/10.1186/s13059-020-02090-4)
        """
    )

    st.divider()

    st.markdown("### Contact and Collaboration")
    st.markdown(
        """
        ColonyExplorer is a joint project developed by the
        **[Infectious Disease Epidemiology Lab](https://ide.kaust.edu.sa/)** (KAUST)
        and the **Banzhaf Lab** (Newcastle University).

        | Name | Email |
        | :--- | :--- |
        | **Ge Zhou (PhD student)** | [ge.zhou@kaust.edu.sa](mailto:ge.zhou@kaust.edu.sa) |
        | **Danesh Moradigaravand (PI)** | [danesh.moradigaravand@kaust.edu.sa](mailto:danesh.moradigaravand@kaust.edu.sa) |
        | **Manuel Banzhaf (PI)** | [manuel.banzhaf@newcastle.ac.uk](mailto:manuel.banzhaf@newcastle.ac.uk) |
        """
    )


def render_help():
    st.title("Help Guide")
    st.markdown("Welcome to the ColonyExplorer Help Guide. Expand the sections below to learn how to navigate the app, interpret results, and format your data.")

    with st.expander("🚀 Getting started", expanded=True):
        st.info(
        """
        1. Use the **navigation panel on the left** to move between pages.
        2. Go to **Colony Viewer** to inspect plate images, colony morphology, and genomic profiles for any strain.
        3. Go to **Gen-GWAS Explorer** to explore pan-genome gene–fitness associations.
        4. Go to **SNP-GWAS Explorer** to explore SNP-level associations across conditions.
        5. From any GWAS page, click an isolate row to jump directly to Colony Viewer — and use the **← Back** button to return.
        """,
        icon="💡"
    )

    with st.expander("🔍 Colony Viewer — step by step"):
        st.markdown(
    """
    **Follow these steps to inspect colony morphology for a strain:**

    1. **Select a condition** — the Plate / Batch list updates automatically to show available runs.
    2. **Select a Plate / Batch** — the sample list updates to show strains on that plate.
    3. **Choose a lookup method:**
       - **Search by accession number** — select a strain from the dropdown, shown as *ID (Accession)*. Reference strains without an accession show *ID (NA)*; if the same ID appears at multiple wells, the position is shown as *ID (NA, R#, C#)*.
       - **Enter grid position** — enter Row (1–32) and Column (1–48) directly.
    4. **Select metrics** — optionally add or remove morphological metrics to display.
    5. **Click Analyse** — loads the plate image, extracts colony crops, and renders the genomic profile.
    """
    )

    with st.expander("📊 Understanding Colony Viewer results"):
        st.markdown(
    """
    Once analysis is complete, the page shows:

    * **Genomic Risk Cards** — ST, K-type, virulence score, resistance score, and AMR gene count from Kleborate.
    * **Automated Insight** — flags Hypervirulent & Carbapenem-resistant (Hv-CRKP) profiles; detects potential fitness cost when a highly resistant strain shows reduced colony size.
    * **Colony Images** — four replicate crops (A–D) extracted from the 1536-well plate.
    * **Metrics Table** — up to 11 IRIS morphology measurements per replicate.
    * **Fitness Distribution** — absolute fitness density across all isolates for this condition, with the selected strain's percentile highlighted.
    * **Plate Context** — full plate image with replicate positions highlighted in red.
    * **Genomics Panels** — detailed resistance genes, virulence loci, and metadata tables.

    **Key Morphology Metrics (from IRIS):**

    | Metric | Description |
    | --- | --- |
    | Colony size | Total colony area in pixels |
    | Circularity | Roundness (1.0 = perfect circle) |
    | Opacity | Optical density proxy for colony density |
    | Biofilm area ratio | Fraction of colony area covered by biofilm |
    | Biofilm color intensity | Mean intensity within the biofilm region |
    """
    )

    with st.expander("🧬 Gen-GWAS Explorer — step by step"):
        st.markdown(
    """
    **Explore pan-genome gene–fitness associations:**

    1. **Select a condition** and **sample** from the dropdowns.
    2. **Filter results** — set a Bonferroni p-value threshold; optionally search by gene name or annotation.
    3. **Robust only** — check **Show robust associations only** to remove lineage-biased hits (Worst pairwise p < 0.05).
    4. **Click a gene row** — loads the pan-genome sequence and isolate presence table below.
    5. **Pan-genome sequence** — view the Panaroo FASTA sequence, length, and GC content.
    6. **Isolate presence** — see which isolates carry the gene, with strain metadata.
    7. **Jump to Colony Viewer** — select an isolate and click **View in Colony Viewer**.

    **Confidence tiers:**
    * ⭐⭐⭐ **Robust** — significant in all pairwise comparisons (Worst p < 0.05)
    * ⭐⭐ **Context-specific** — significant in at least one comparison (Best p < 0.01)
    * ⭐ **Low** — pairwise support does not meet either threshold
    """
    )

    with st.expander("🔬 SNP-GWAS Explorer — step by step"):
        st.markdown(
    """
    **Explore SNP-level associations across conditions:**

    1. **Select a condition** from the dropdown.
    2. **Browse the SNP table** — sort by p-value or effect size; filter by significance threshold.
    3. **Click a SNP row** — loads the isolate presence table for that SNP.
    4. **Isolate presence** — see which isolates carry the SNP allele, with strain metadata.
    5. **Jump to Colony Viewer** — select an isolate and click **View in Colony Viewer**.
    """
    )

    with st.expander("💾 Saving colony images"):
        st.markdown("Export colony crops for presentations or downstream analysis.")
        st.success(
            "Click **Save colony images** (at the bottom of the Colony Viewer results) to export the four replicate crops as `.png` files into a `saved_colonies/` folder in your working directory.",
            icon="✅"
        )

    with st.expander("📁 File & data requirements"):
        st.markdown("ColonyExplorer reads file paths from `config/config.yaml`.")
        st.markdown(
            """
            | Configuration Key | Expected Content |
            | :--- | :--- |
            | `image_directory` | Folder containing `.JPG.grid.jpg` plate images |
            | `iris_directory` | Folder containing `.JPG.iris` measurement files |
            | `strain_file` | CSV or Excel with `ID`, `Row`, `Column`, `Plate`, `GenBank_acc`, `ENA_acc` |
            | `kleborate_file` | TSV output from Kleborate |
            """
        )
        st.divider()
        st.markdown("**Image naming convention** — filenames must follow this exact pattern:")
        st.code("{Condition}-{Plate}-{Batch}_A.JPG.grid.jpg", language="text")
        st.caption("Example: `Ceftazidime-1ugml-1-1_A.JPG.grid.jpg`")
        st.markdown("**IRIS file naming** — must match the plate image stem:")
        st.code("{Condition}-{Plate}-{Batch}_A.JPG.iris", language="text")


_SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.5rem;
}
.sidebar-title {
    font-size: 2.8rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    line-height: 1.3;
    margin-bottom: 0.15rem;
    text-align: center;
}
.sidebar-subtitle {
    font-size: 0.78rem;
    opacity: 0.6;
    margin-bottom: 0;
    text-align: center;
}
/* Nav buttons: full width, left-aligned, no border */
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 0.45rem 0.75rem;
    font-size: 0.95rem;
    color: inherit;
    transition: background 0.15s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(13, 148, 136, 0.1);
    border: none;
}
[data-testid="stSidebar"] .stButton > button:focus:not(:active) {
    border: none;
    box-shadow: none;
}
/* Active page button */
[data-testid="stSidebar"] .stButton > button[data-active="true"] {
    background: rgba(13, 148, 136, 0.15);
    color: #0d9488;
    font-weight: 600;
}
/* Analyse (primary) button — teal */
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #0d9488 !important;
    color: #ffffff !important;
    border: none !important;
    text-align: center !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background: #0f766e !important;
}
/* Metric value colour — everywhere */
[data-testid="stMetricValue"] {
    color: #0d9488 !important;
}
/* Primary buttons — teal */
[data-testid="baseButton-primary"] {
    background-color: #0d9488 !important;
    border-color: #0d9488 !important;
    color: white !important;
}
[data-testid="baseButton-primary"]:hover {
    background-color: #0f766e !important;
    border-color: #0f766e !important;
}
/* Multiselect tags in sidebar */
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: #0d9488 !important;
}
</style>
"""

_ROARY_META_COLS = 14  # number of metadata columns before isolate columns begin
_STRAIN_COLS = ["ID", "GenBank_acc", "ENA_acc"]  # columns to join from strain_names.csv


def _format_isolate_label(row: pd.Series) -> str:
    """Return 'SampleName (GenBankAcc)' or 'SampleName (NA)' if accession is missing."""
    acc = row.get("GenBank_acc", None)
    name = row.get("Isolate", "")
    if pd.notna(acc) and str(acc).strip():
        return f"{name} ({acc})"
    return f"{name} (NA)"


@st.cache_data
def _build_isolate_lookup(path: str) -> pd.DataFrame:
    """
    Build a lookup keyed by any isolate identifier (strain ID or ENA_acc).
    Some isolates in the pan-genome CSV are named by ERR accession rather than
    strain ID, so we index both to ensure every row in the presence table
    can be annotated.
    Returns a DataFrame with columns [Isolate, ID, GenBank_acc, ENA_acc].
    """
    strains = pd.read_csv(path, usecols=_STRAIN_COLS)
    by_id  = strains.rename(columns={"ID": "Isolate"})
    by_ena = strains.rename(columns={"ENA_acc": "Isolate"})
    return pd.concat([by_id, by_ena], ignore_index=True).drop_duplicates("Isolate")

@st.cache_data(show_spinner="Loading pan-genome presence/absence…")
def _load_roary(path: str) -> pd.DataFrame:
    """Load gene_presence_absence_roary.csv with Gene as index. Cached."""
    return pd.read_csv(path, index_col=0, low_memory=False)


def _isolate_presence(gene: str, roary: pd.DataFrame) -> pd.DataFrame:
    """
    Return a DataFrame with columns [Isolate, Locus Tag] for all isolates
    where *gene* is present (non-empty cell). Returns empty DataFrame if not found.
    """
    if gene not in roary.index:
        return pd.DataFrame(columns=["Isolate", "Locus Tag"])
    row = roary.loc[gene]
    isolate_cols = roary.columns[_ROARY_META_COLS - 1:]   # -1 because Gene was used as index
    present = row[isolate_cols].dropna()
    present = present[present != ""]
    return pd.DataFrame({"Isolate": present.index, "Locus Tag": present.values})


@st.cache_data(show_spinner=False)
def _isolate_presence_cached(gene: str, roary_path: str) -> pd.DataFrame:
    """Cached wrapper: keys on gene name + file path so repeated calls are instant."""
    return _isolate_presence(gene, _load_roary(roary_path))


@st.cache_data
def _load_gwas_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def _load_fitness_csv(path: str) -> pd.DataFrame:
    """Load absolute_fitness.csv with strain IDs / ENA accessions as index."""
    return pd.read_csv(path, index_col=0)


@st.cache_data(show_spinner="Indexing pan-genome reference…")
def _load_fasta_index(fasta_path: str) -> dict[str, str]:
    """Parse a FASTA file into {header: sequence} dict. Cached after first load."""
    index: dict[str, str] = {}
    current_header = None
    chunks: list[str] = []
    with open(fasta_path) as fh:
        for line in fh:
            line = line.rstrip()
            if line.startswith(">"):
                if current_header is not None:
                    index[current_header] = "".join(chunks)
                current_header = line[1:]  # strip ">"
                chunks = []
            else:
                chunks.append(line)
    if current_header is not None:
        index[current_header] = "".join(chunks)
    return index


def _lookup_sequence(gene: str, fasta_index: dict[str, str]) -> tuple[str, str] | None:
    """
    Return (matched_header, sequence) for *gene* from the FASTA index.
    Tries exact match first, then prefix match before '~~~'.
    """
    if gene in fasta_index:
        return gene, fasta_index[gene]
    # prefix match for compound headers like "ybbA~~~iroE"
    for header, seq in fasta_index.items():
        if header.split("~~~")[0] == gene:
            return header, seq
    return None


def _list_gwas_conditions(gwas_dir: str) -> list[str]:
    """Return condition names (stem of each CSV) sorted alphabetically."""
    stems = []
    for f in os.listdir(gwas_dir):
        if f.endswith(".results.csv"):
            stems.append(f[:-len(".results.csv")])
        elif f.endswith(".csv"):
            stems.append(f[:-4])
    return sorted(stems)


_GWAS_CSS = """
<style>
.gwas-banner {
    background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
    border-radius: 12px;
    padding: 1.4rem 2rem;
    margin-bottom: 1.2rem;
}
.gwas-banner h2 {
    margin: 0 0 0.3rem;
    font-size: 1.7rem;
    font-weight: 700;
    color: #ffffff;
}
.gwas-banner p {
    margin: 0;
    color: rgba(255,255,255,0.85);
    font-size: 0.92rem;
}
.gwas-section-title {
    border-left: 4px solid #0d9488;
    padding: 0.15rem 0 0.15rem 0.7rem;
    margin: 0.2rem 0 0.6rem;
    font-size: 1.5rem;
    font-weight: 700;
}
</style>
"""


def _style_gwas_table(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    """Binary color for Odds Ratio (>1 green, <1 pink); gradient for p-values."""
    from matplotlib.colors import LinearSegmentedColormap

    def _or_color(val):
        if pd.isna(val):
            return ""
        return "background-color: #c5f0c5" if val > 1 else "background-color: #fac5c5"

    cmap_pval = LinearSegmentedColormap.from_list("pval", ["#c5dff7", "#ffffff"])
    return (
        df.style
        .map(_or_color, subset=["Odds Ratio"])
        .background_gradient(subset=["Bonferroni p", "BH p"], cmap=cmap_pval, axis=None)
        .format({
            "Odds Ratio":   "{:.3f}",
            "Bonferroni p": "{:.2e}",
            "BH p":         "{:.2e}",
        })
    )


def render_gwas_explorer(config: dict) -> None:
    st.markdown("""
    <style>
    [data-testid="baseButton-primary"] {
        background-color: #0d9488 !important;
        border-color: #0d9488 !important;
        color: white !important;
    }
    [data-testid="baseButton-primary"]:hover {
        background-color: #0f766e !important;
        border-color: #0f766e !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.html(_GWAS_CSS)
    st.html(
        '<div class="gwas-banner">'
        "<h2>Gen-GWAS Explorer</h2>"
        "<p>Significant gene associations per experimental condition — Scoary bacterial GWAS</p>"
        "</div>"
    )

    gwas_dir = config["directories"].get("gwas_directory", "data/GWAS_results/")
    conditions = _list_gwas_conditions(gwas_dir)
    if not conditions:
        st.error(f"No GWAS CSV files found in `{gwas_dir}`.")
        return

    label_map = _build_condition_label_map("data/condition_clean_tags_mapping.csv")

    import re as _re
    def _gwas_label_to_clean(cond: str) -> str:
        key = _re.sub(r"[.\-,_%\s]", "", cond).lower()
        return label_map.get(key, None)

    display_to_raw = {
        _gwas_label_to_clean(c): c
        for c in conditions
        if _gwas_label_to_clean(c) is not None
    }

    if not display_to_raw:
        st.error("No conditions matched the Clean_Tags mapping.")
        return

    _sorted_displays = sorted(display_to_raw)
    _jump_cond = st.session_state.pop("gwas_jump_condition", None)
    _cond_default_idx = (
        _sorted_displays.index(_jump_cond)
        if _jump_cond and _jump_cond in _sorted_displays else 0
    )
    selected_display = st.selectbox("Condition", _sorted_displays, index=_cond_default_idx)
    condition = display_to_raw[selected_display]
    _results_path = os.path.join(gwas_dir, f"{condition}.results.csv")
    _csv_path = os.path.join(gwas_dir, f"{condition}.csv")
    df = _load_gwas_csv(_results_path if os.path.exists(_results_path) else _csv_path)

    with st.expander("Filter", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            p_thresh = st.number_input(
                "Benjamini-Hochberg p upper bound", value=0.05, format="%.2e", min_value=0.0, max_value=1.0
            )
        with c2:
            search = st.text_input("Search gene / annotation", placeholder="e.g. tesA, transporter")
        show_robust_only = st.checkbox("Show robust associations only (filter lineage-biased hits)")

    mask = df["Benjamini_H_p"] <= p_thresh
    if search:
        term = search.lower()
        mask &= (
            df["Gene"].str.lower().str.contains(term, na=False) |
            df["Annotation"].str.lower().str.contains(term, na=False)
        )

    filtered = df[mask].sort_values("Bonferroni_p").copy()
    original_count = len(filtered)

    if show_robust_only:
        filtered = filtered[filtered["Worst_pairwise_comp_p"] < 0.05]
        removed = original_count - len(filtered)
        st.caption(f"Showing {len(filtered)} robust associations. (Filtered out {removed} potential lineage-biased hits)")
    else:
        st.write(f"**{len(filtered)}** significant associations (of {len(df)} total)")

    def _confidence(row):
        if row["Worst_pairwise_comp_p"] < 0.05:
            return "⭐⭐⭐ Robust"
        elif row["Best_pairwise_comp_p"] < 0.01:
            return "⭐⭐ Context-specific"
        else:
            return "⭐ Low"

    filtered["Confidence"] = filtered.apply(_confidence, axis=1)

    display = filtered[[
        "Gene", "Annotation",
        "Number_pos_present_in", "Number_neg_present_in",
        "Odds_ratio", "Bonferroni_p", "Benjamini_H_p",
        "Confidence",
    ]].rename(columns={
        "Number_pos_present_in":  "n pos",
        "Number_neg_present_in":  "n neg",
        "Odds_ratio":             "Odds Ratio",
        "Bonferroni_p":           "Bonferroni p",
        "Benjamini_H_p":          "BH p",
    })

    table_event = st.dataframe(
        _style_gwas_table(display),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="gwas_table",
    )

    st.html("""
    <div style="display:flex; gap:2rem; align-items:flex-start; margin:0.4rem 0 0.8rem; flex-wrap:wrap;">
        <div>
            <div style="font-size:0.75rem; font-weight:600; opacity:0.6; margin-bottom:0.35rem; letter-spacing:0.05em; text-transform:uppercase;">Odds Ratio</div>
            <div style="display:flex; align-items:center; gap:0.5rem;">
                <div style="width:22px;height:14px;border-radius:3px;background:#fac5c5;"></div>
                <span style="font-size:0.78rem;">OR &lt; 1 &nbsp;(depleted)</span>
                <div style="width:22px;height:14px;border-radius:3px;background:#c5f0c5; margin-left:0.75rem;"></div>
                <span style="font-size:0.78rem;">OR &gt; 1 &nbsp;(enriched)</span>
            </div>
        </div>
        <div>
            <div style="font-size:0.75rem; font-weight:600; opacity:0.6; margin-bottom:0.35rem; letter-spacing:0.05em; text-transform:uppercase;">P-value (Bonferroni / BH)</div>
            <div style="display:flex; align-items:center; gap:0.5rem;">
                <span style="font-size:0.78rem; white-space:nowrap;">p low &nbsp;(significant)</span>
                <div style="width:90px; height:14px; border-radius:3px;
                            background:linear-gradient(to right,#c5dff7,#ffffff);
                            border:1px solid rgba(0,0,0,0.1);"></div>
                <span style="font-size:0.78rem; white-space:nowrap;">p high &nbsp;(not significant)</span>
            </div>
        </div>
        <div>
            <div style="font-size:0.75rem; font-weight:600; opacity:0.6; margin-bottom:0.35rem; letter-spacing:0.05em; text-transform:uppercase;">Confidence</div>
            <div style="display:flex; flex-direction:column; gap:0.25rem;">
                <div style="font-size:0.78rem;">⭐⭐⭐ <b>Robust</b> — significant in all pairwise comparisons (Worst p &lt; 0.05)</div>
                <div style="font-size:0.78rem;">⭐⭐ <b>Context-specific</b> — significant in at least one comparison (Best p &lt; 0.01)</div>
                <div style="font-size:0.78rem;">⭐ <b>Low</b> — pairwise support does not meet either threshold</div>
            </div>
        </div>
    </div>
    """)

    st.download_button(
        "Download filtered table",
        data=display.to_csv(index=False).encode(),
        file_name=f"gwas_{condition}_filtered.csv",
        mime="text/csv",
    )

    # ---- Gene selector (shared by sequence viewer + isolate presence) ----
    gwas_files_dir = config["directories"].get("gwas_files_directory", "data/GWAS_files/")
    gene_list = filtered["Gene"].dropna().unique().tolist() if not filtered.empty else []

    if not gene_list:
        st.info("No genes in current filtered results — adjust the filter above.")
        return

    selected_rows = table_event.selection.get("rows", [])
    if selected_rows:
        st.session_state["gwas_selected_gene"] = display["Gene"].iloc[selected_rows[0]]
    selected_gene = st.session_state.get("gwas_selected_gene", gene_list[0])
    if selected_gene not in gene_list:
        selected_gene = gene_list[0]

    # ---- Fitness boxplot (present vs absent) ----
    _fitness_path = "data/absolute_fitness.csv"
    _roary_file_bp = os.path.join(gwas_files_dir, "gene_presence_absence_roary.csv")
    if os.path.exists(_fitness_path) and os.path.exists(_roary_file_bp):
        import plotly.graph_objects as go
        from scipy import stats as _stats

        _fit_df      = _load_fitness_csv(_fitness_path)
        _roary_bp    = _load_roary(_roary_file_bp)
        _presence_bp = _isolate_presence_cached(selected_gene, _roary_file_bp)
        _cond_key    = _re.sub(r"[.\-,_%\s]", "", condition or "").lower()
        _col_map     = {_re.sub(r"[.\-,_%\s]", "", c).lower(): c for c in _fit_df.columns}
        _fit_col     = _col_map.get(_cond_key)

        st.divider()
        st.html('<div class="gwas-section-title">Fitness Boxplot</div>')
        if not _fit_col:
            st.info(
                f"No fitness data available for **{selected_display}**. "
                "This condition was not included in the absolute fitness experiment."
            )
        elif _presence_bp.empty:
            st.info(f"Gene **{selected_gene}** not found in the pan-genome — cannot compute boxplot.")
        if _fit_col and not _presence_bp.empty:

            all_iso     = set(_roary_bp.columns[_ROARY_META_COLS - 1:])
            present_iso = set(_presence_bp["Isolate"].tolist())
            absent_iso  = all_iso - present_iso

            _fit_idx    = set(_fit_df.index)
            _present_list = [iso for iso in present_iso if iso in _fit_idx]
            _absent_list  = [iso for iso in absent_iso  if iso in _fit_idx]

            def _clean(series):
                return [float(v) for v in series if pd.notna(v) and float(v) != 0]

            vals_present = _clean(_fit_df.loc[_present_list, _fit_col]) if _present_list else []
            vals_absent  = _clean(_fit_df.loc[_absent_list,  _fit_col]) if _absent_list  else []

            st.caption(f"n present = {len(vals_present)}  ·  n absent = {len(vals_absent)}  ·  {len(all_iso) - len(vals_present) - len(vals_absent)} excluded (no fitness data)")

            if vals_present and vals_absent:
                _, pval = _stats.mannwhitneyu(vals_absent, vals_present, alternative="two-sided")
                p_label = f"p = {pval:.2e}" if pval >= 1e-4 else "p < 1e-4"

                fig = go.Figure()
                fig.add_trace(go.Box(
                    y=vals_absent,
                    name="Absent",
                    marker_color="#e07070",
                    boxpoints="outliers",
                    marker=dict(size=4, opacity=0.7),
                    line=dict(width=1.5),
                ))
                fig.add_trace(go.Box(
                    y=vals_present,
                    name="Present",
                    marker_color="#0d9488",
                    boxpoints="outliers",
                    marker=dict(size=4, opacity=0.7),
                    line=dict(width=1.5),
                ))
                fig.update_layout(
                    title=dict(
                        text=(
                            f"<b>Gene:</b> {selected_gene}     "
                            f"<b>Condition:</b> {selected_display}     "
                            f"<b>P-value:</b> {p_label} (Mann-Whitney U)"
                        ),
                        font=dict(size=16),
                        x=0.5,
                        xanchor="center",
                    ),
                    yaxis_title="Fitness",
                    xaxis_title="Type",
                    showlegend=False,
                    height=550,
                    plot_bgcolor="white",
                    font=dict(size=15),
                    yaxis=dict(
                        gridcolor="rgba(0,0,0,0.08)",
                        zeroline=False,
                        title_font=dict(size=17),
                        tickfont=dict(size=14),
                    ),
                    xaxis=dict(
                        title_font=dict(size=17),
                        tickfont=dict(size=15),
                    ),
                    margin=dict(t=100, b=60, l=80, r=30),
                )

                st.plotly_chart(fig, use_container_width=True)

    # ---- Pan-genome sequence viewer ----
    st.divider()
    st.html('<div class="gwas-section-title">Pan-genome sequence</div>')
    fasta_file = os.path.join(gwas_files_dir, "pan_genome_reference.fa")
    if not os.path.exists(fasta_file):
        st.warning(f"pan_genome_reference.fa not found at `{fasta_file}`.")
    else:
        fasta_index = _load_fasta_index(fasta_file)
        result = _lookup_sequence(selected_gene, fasta_index)
        if result is None:
            st.warning(f"No sequence found for **{selected_gene}** in pan_genome_reference.fa.")
        else:
            matched_header, seq = result
            seq_len = len(seq)
            col1, col2, col3 = st.columns(3)
            col1.metric("Gene", matched_header)
            col2.metric("Length (bp)", f"{seq_len:,}")
            col3.metric("GC content", f"{(seq.upper().count('G') + seq.upper().count('C')) / seq_len * 100:.1f}%")

            with st.expander("View FASTA sequence", expanded=False):
                lines = []
                for i in range(0, seq_len, 60):
                    lines.append(f"{i+1:>7}  {seq[i:i+60]}")
                st.html("""
                <style>
                .fasta-scroll pre, .fasta-scroll code {
                    max-height: 320px;
                    overflow-y: auto;
                    display: block;
                }
                </style>
                <div class="fasta-scroll">
                """)
                st.code("\n".join(lines), language=None)
                st.html("</div>")
                st.download_button(
                    f"Download {matched_header}.fa",
                    data=f">{matched_header}\n{seq}\n".encode(),
                    file_name=f"{matched_header}.fa",
                    mime="text/plain",
                )

    # ---- Isolate presence ----
    roary_file = os.path.join(gwas_files_dir, "gene_presence_absence_roary.csv")
    if not os.path.exists(roary_file):
        st.warning(f"gene_presence_absence_roary.csv not found at `{roary_file}`.")
    else:
        st.divider()
        st.html('<div class="gwas-section-title">Isolate presence</div>')
        roary = _load_roary(roary_file)
        presence = _isolate_presence_cached(selected_gene, roary_file)
        total_isolates = len(roary.columns) - (_ROARY_META_COLS - 1)
        n_present = len(presence)

        m1, m2, m3 = st.columns(3)
        m1.metric("Present in", f"{n_present} isolates")
        m2.metric("Absent in", f"{total_isolates - n_present} isolates")
        m3.metric("Frequency", f"{n_present / total_isolates * 100:.1f}%")

        if presence.empty:
            st.info(f"**{selected_gene}** not found in gene_presence_absence_roary.csv.")
        else:
            strain_file = config["files"]["strain_file"]
            if os.path.exists(strain_file):
                isolate_lookup = _build_isolate_lookup(strain_file)
                presence = presence.merge(isolate_lookup, on="Isolate", how="left")
                # If the isolate name is an ERR accession, copy it into ENA_acc
                err_mask = presence["Isolate"].str.startswith("ERR", na=False)
                presence.loc[err_mask, "ENA_acc"] = presence.loc[err_mask, "Isolate"]
                presence = presence.drop(columns=["ID"], errors="ignore")
                presence.insert(0, "ID", presence.apply(_format_isolate_label, axis=1))

            iso_search = st.text_input("Filter isolates", placeholder="e.g. DKPB001")
            shown = presence.reset_index(drop=True)
            if iso_search:
                shown = presence[
                    presence.apply(
                        lambda r: r.astype(str).str.contains(iso_search, case=False, na=False).any(),
                        axis=1,
                    )
                ].reset_index(drop=True)

            pres_table_event = st.dataframe(
                shown,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key=f"gwas_pres_table_{selected_gene}",
            )

            st.download_button(
                "Download presence table",
                data=presence.to_csv(index=False).encode(),
                file_name=f"{selected_gene}_isolates.csv",
                mime="text/csv",
            )

            pres_selected_rows = pres_table_event.selection.get("rows", [])
            if not pres_selected_rows:
                st.caption("👆 Select a row to inspect the isolate in Colony Viewer.")
            else:
                iso_row = shown.iloc[pres_selected_rows[0]]
                iso_isolate = iso_row.get("Isolate", None)
                has_acc = "GenBank_acc" in shown.columns
                selected_acc = iso_row.get("GenBank_acc", None) if has_acc else iso_isolate

                label = f"{iso_isolate}"
                if has_acc and pd.notna(selected_acc):
                    label += f"  ({selected_acc})"
                st.info(f"Selected: **{label}**")

                if st.button("View in Colony Viewer →", key="jump_btn", type="primary"):
                    img_dir = config["directories"]["image_directory"]

                    import re as _re2
                    _norm = lambda s: _re2.sub(r"[.\-,_%\s]", "", s).lower()
                    _condition_norm = _norm(condition)
                    cv_condition = None
                    for cv_cond in list_conditions(img_dir):
                        if _norm(cv_cond) == _condition_norm:
                            cv_condition = cv_cond
                            break

                    strain_file = config["files"]["strain_file"]
                    plate_num = None
                    if os.path.exists(strain_file):
                        if pd.notna(selected_acc):
                            strains = pd.read_csv(strain_file, usecols=["GenBank_acc", "Plate"])
                            hit = strains[strains["GenBank_acc"] == selected_acc]
                            if not hit.empty:
                                plate_num = int(hit.iloc[0]["Plate"])
                        else:
                            strains = pd.read_csv(strain_file, usecols=["ID", "Row", "Column", "Plate"])
                            hit = strains[strains["ID"] == iso_isolate]
                            if not hit.empty:
                                plate_num = int(hit.iloc[0]["Plate"])
                                st.session_state.grid_row = int(hit.iloc[0]["Row"])
                                st.session_state.grid_col = int(hit.iloc[0]["Column"])

                    if plate_num is not None:
                        # Find a run for the correct plate, trying the current condition first
                        matching = []
                        if cv_condition:
                            runs = find_available_runs(img_dir, cv_condition)
                            matching = [r for r in runs if r[0] == plate_num]
                        if not matching and cv_condition:
                            # No batch for this plate under the matched condition —
                            # try all batches for that condition (any plate).
                            runs = find_available_runs(img_dir, cv_condition)
                            matching = runs[:1]  # fall back to first available batch
                        if matching:
                            st.session_state.plate_batch = matching[0]
                            st.session_state.condition = cv_condition

                    st.session_state.strain_plate_num  = plate_num
                    st.session_state.active_strain_id  = str(iso_isolate) if iso_isolate else None
                    st.session_state.active_strain     = selected_acc if pd.notna(selected_acc) else None
                    st.session_state.lookup_mode       = "Search by accession number"
                    st.session_state.gwas_back = {
                        "page":      "Gen-GWAS Explorer",
                        "condition": selected_display,
                        "gene":      selected_gene,
                    }
                    st.session_state.page          = "Colony Viewer"
                    st.session_state.pending_jump  = True
                    st.rerun()



# ── SNP-GWAS helpers ──────────────────────────────────────────────────────────

_SNP_GWAS_CSS = """
<style>
.snp-banner {
    background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
    border-radius: 12px;
    padding: 1.4rem 2rem;
    margin-bottom: 1.2rem;
}
.snp-banner h2 { margin: 0 0 0.3rem; font-size: 1.7rem; font-weight: 700; color: #ffffff; }
.snp-banner p  { margin: 0; color: rgba(255,255,255,0.85); font-size: 0.92rem; }
.snp-section-title {
    border-left: 4px solid #0d9488;
    padding: 0.15rem 0 0.15rem 0.7rem;
    margin: 0.2rem 0 0.6rem;
    font-size: 1.5rem;
    font-weight: 700;
}
</style>
"""


@st.cache_data(show_spinner="Loading SNP-GWAS data…")
def _load_snp_gwas(path: str) -> pd.DataFrame:
    """Load Significant_SNPs.csv, reconstruct multi-column SNP IDs, cache."""
    df = pd.read_csv(path)

    def _reconstruct(row):
        parts = [str(row["Gene"]).strip('"')]
        # Non.unique.Gene.name — always part of SNP ID when not NA
        v1 = row.get("Non.unique.Gene.name", None)
        if v1 is not None and pd.notna(v1) and str(v1).strip() not in ("NA", ""):
            parts.append(str(v1).strip('"'))
        # Annotation — only include if it looks like a VCF fragment (contains "|")
        # Real annotations (gene function strings) do not contain "|"
        v2 = row.get("Annotation", None)
        if v2 is not None and pd.notna(v2) and "|" in str(v2):
            parts.append(str(v2).strip('"'))
        return ",".join(parts)

    df["SNP_ID"] = df.apply(_reconstruct, axis=1)
    return df


@st.cache_data(show_spinner="Loading SNP annotations…")
def _load_snp_annotations(path: str) -> pd.DataFrame:
    """Load annotated_SNP.csv indexed by POS for fast lookup."""
    df = pd.read_csv(path, dtype={"POS": str})
    return df


def _lookup_snp_annotation(snp_id: str, annot_df: pd.DataFrame) -> pd.DataFrame:
    """Return annotation rows matching the SNP position (and REF/ALT if possible).
    Handles multi-allelic SNPs (e.g. ALT='G,C') by searching each ALT separately."""
    pos, ref, alt = _parse_snp_id(snp_id)
    hits = annot_df[annot_df["POS"].astype(str) == str(pos)]
    if hits.empty:
        return hits
    # Refine by REF + each individual ALT allele
    if "REF" in hits.columns and "ALT" in hits.columns:
        alt_alleles = [a.strip() for a in alt.split(",") if a.strip()]
        ref_mask = hits["REF"] == ref
        alt_mask = hits["ALT"].isin(alt_alleles)
        refined = hits[ref_mask & alt_mask]
        if not refined.empty:
            return refined
        # Fall back to REF match only if no ALT match
        ref_only = hits[ref_mask]
        if not ref_only.empty:
            return ref_only
    return hits


@st.cache_data(show_spinner="Loading SNP presence/absence…")
def _load_snp_presence(path: str) -> pd.DataFrame:
    """Load significant_snps_presence_absence.csv with SNP_ID as index."""
    return pd.read_csv(path, index_col=0, low_memory=False)


def _parse_snp_id(snp_id: str) -> tuple[str, str, str]:
    """Return (position, ref, alt) from a VCF-style SNP ID POS|.|REF|ALT|..."""
    parts = snp_id.split("|")
    pos = parts[0] if len(parts) > 0 else snp_id
    ref = parts[2] if len(parts) > 2 else ""
    alt = parts[3] if len(parts) > 3 else ""
    return pos, ref, alt


def _build_condition_label_map(mapping_path: str) -> dict[str, str]:
    """Map normalised label key -> Clean_Tag from condition_clean_tags_mapping.csv."""
    import re, csv as _csv
    result = {}
    if not os.path.exists(mapping_path):
        return result
    with open(mapping_path, encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            fname = row.get("File_name", "").strip()
            ctag  = row.get("Clean_Tag", "").strip()
            if fname and ctag:
                key = re.sub(r"[.\-,_%\s]", "", fname).lower()
                result[key] = ctag
    return result


def _style_snp_table(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    from matplotlib.colors import LinearSegmentedColormap

    def _or_color(val):
        if pd.isna(val):
            return ""
        return "background-color: #c5f0c5" if val > 1 else "background-color: #fac5c5"

    cmap_pval = LinearSegmentedColormap.from_list("pval", ["#c5dff7", "#ffffff"])
    return (
        df.style
        .map(_or_color, subset=["Odds Ratio"])
        .background_gradient(subset=["Bonferroni p", "BH p"], cmap=cmap_pval, axis=None)
        .format({
            "Odds Ratio":   "{:.3f}",
            "Bonferroni p": "{:.2e}",
            "BH p":         "{:.2e}",
        })
    )


def render_snp_gwas_explorer(config: dict) -> None:
    import re


    st.html(_SNP_GWAS_CSS)
    st.html(
        '<div class="snp-banner">'
        "<h2>SNP-GWAS Explorer</h2>"
        "<p>Significant SNP associations per experimental condition — Scoary bacterial GWAS</p>"
        "</div>"
    )

    snp_cfg  = config.get("snp_gwas", {})
    sig_path = snp_cfg.get("significant_snps_file", "data/GWAS_files/Significant_SNPs.csv")
    pres_path = snp_cfg.get("presence_absence_file", "data/GWAS_files/significant_snps_presence_absence.csv")
    map_path = "data/condition_clean_tags_mapping.csv"

    if not os.path.exists(sig_path):
        st.error(f"Significant_SNPs.csv not found at `{sig_path}`.")
        return

    df_all = _load_snp_gwas(sig_path)
    label_map = _build_condition_label_map(map_path)

    # Build condition list — only include labels that have a Clean_Tag match
    raw_labels = sorted(df_all["label"].dropna().unique().tolist())

    def _label_to_clean(lbl: str) -> str | None:
        key = re.sub(r"[.\-,_%\s]", "", lbl).lower()
        return label_map.get(key, None)

    display_to_raw = {
        _label_to_clean(l): l
        for l in raw_labels
        if _label_to_clean(l) is not None
    }

    if not display_to_raw:
        st.error("No conditions matched the Clean_Tags mapping.")
        return

    _snp_sorted_displays = sorted(display_to_raw)
    _snp_jump_cond = st.session_state.pop("gwas_jump_condition", None)
    _snp_cond_default_idx = (
        _snp_sorted_displays.index(_snp_jump_cond)
        if _snp_jump_cond and _snp_jump_cond in _snp_sorted_displays else 0
    )
    selected_display = st.selectbox("Condition", _snp_sorted_displays, index=_snp_cond_default_idx)
    condition = display_to_raw[selected_display]
    df = df_all[df_all["label"] == condition].copy()

    with st.expander("Filter", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            p_thresh = st.number_input(
                "Benjamini-Hochberg p upper bound", value=0.05, format="%.2e",
                min_value=0.0, max_value=1.0, key="snp_p_thresh"
            )
        with c2:
            search = st.text_input(
                "Search SNP position / allele",
                placeholder="e.g. 304662, T>C",
                key="snp_search"
            )
        show_robust_only = st.checkbox(
            "Show robust associations only (filter lineage-biased hits)",
            key="snp_robust"
        )

    mask = df["Benjamini_H_p"] <= p_thresh
    if search:
        term = search.lower().replace(">", "").replace(" ", "")
        mask &= df["SNP_ID"].str.lower().str.replace("|", "", regex=False).str.contains(term, na=False)

    filtered = df[mask].sort_values("Benjamini_H_p").copy()
    original_count = len(filtered)

    if show_robust_only:
        filtered = filtered[filtered["Worst_pairwise_comp_p"] < 0.05]
        removed = original_count - len(filtered)
        st.caption(f"Showing {len(filtered)} robust associations. (Filtered out {removed} potential lineage-biased hits)")
    else:
        st.write(f"**{len(filtered)}** significant associations (of {len(df)} total)")

    def _confidence(row):
        if row["Worst_pairwise_comp_p"] < 0.05:
            return "⭐⭐⭐ Robust"
        elif row["Best_pairwise_comp_p"] < 0.01:
            return "⭐⭐ Context-specific"
        else:
            return "⭐ Low"

    filtered["Confidence"] = filtered.apply(_confidence, axis=1)

    # Parse SNP IDs into Position / REF / ALT columns
    parsed = filtered["SNP_ID"].apply(lambda s: pd.Series(_parse_snp_id(s), index=["Position", "REF", "ALT"]))
    filtered = pd.concat([filtered, parsed], axis=1)

    display = filtered[[
        "Position", "REF", "ALT",
        "Number_pos_present_in", "Number_neg_present_in",
        "Odds_ratio", "Bonferroni_p", "Benjamini_H_p",
        "Confidence",
    ]].rename(columns={
        "Number_pos_present_in":  "n pos",
        "Number_neg_present_in":  "n neg",
        "Odds_ratio":             "Odds Ratio",
        "Bonferroni_p":           "Bonferroni p",
        "Benjamini_H_p":          "BH p",
    })

    table_event = st.dataframe(
        _style_snp_table(display),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="snp_gwas_table",
    )

    st.html("""
    <div style="display:flex; gap:2rem; align-items:flex-start; margin:0.4rem 0 0.8rem; flex-wrap:wrap;">
        <div>
            <div style="font-size:0.75rem; font-weight:600; opacity:0.6; margin-bottom:0.35rem; letter-spacing:0.05em; text-transform:uppercase;">Odds Ratio</div>
            <div style="display:flex; align-items:center; gap:0.5rem;">
                <div style="width:22px;height:14px;border-radius:3px;background:#fac5c5;"></div>
                <span style="font-size:0.78rem;">OR &lt; 1 &nbsp;(depleted)</span>
                <div style="width:22px;height:14px;border-radius:3px;background:#c5f0c5; margin-left:0.75rem;"></div>
                <span style="font-size:0.78rem;">OR &gt; 1 &nbsp;(enriched)</span>
            </div>
        </div>
        <div>
            <div style="font-size:0.75rem; font-weight:600; opacity:0.6; margin-bottom:0.35rem; letter-spacing:0.05em; text-transform:uppercase;">P-value (Bonferroni / BH)</div>
            <div style="display:flex; align-items:center; gap:0.5rem;">
                <span style="font-size:0.78rem; white-space:nowrap;">p low &nbsp;(significant)</span>
                <div style="width:90px; height:14px; border-radius:3px;
                            background:linear-gradient(to right,#c5dff7,#ffffff);
                            border:1px solid rgba(0,0,0,0.1);"></div>
                <span style="font-size:0.78rem; white-space:nowrap;">p high &nbsp;(not significant)</span>
            </div>
        </div>
        <div>
            <div style="font-size:0.75rem; font-weight:600; opacity:0.6; margin-bottom:0.35rem; letter-spacing:0.05em; text-transform:uppercase;">Confidence</div>
            <div style="display:flex; flex-direction:column; gap:0.25rem;">
                <div style="font-size:0.78rem;">⭐⭐⭐ <b>Robust</b> — significant in all pairwise comparisons (Worst p &lt; 0.05)</div>
                <div style="font-size:0.78rem;">⭐⭐ <b>Context-specific</b> — significant in at least one comparison (Best p &lt; 0.01)</div>
                <div style="font-size:0.78rem;">⭐ <b>Low</b> — pairwise support does not meet either threshold</div>
            </div>
        </div>
    </div>
    """)

    st.download_button(
        "Download filtered table",
        data=display.to_csv(index=False).encode(),
        file_name=f"snp_gwas_{condition}_filtered.csv",
        mime="text/csv",
        key="snp_dl_filtered",
    )

    if filtered.empty:
        st.info("No SNPs in current filtered results — adjust the filter above.")
        return

    # ── SNP selector (from table click or first row) ──────────────────────────
    selected_rows = table_event.selection.get("rows", [])
    selected_snp = filtered["SNP_ID"].iloc[selected_rows[0]] if selected_rows else filtered["SNP_ID"].iloc[0]

    # ── SNP Annotation ────────────────────────────────────────────────────────
    annot_path = snp_cfg.get("annotated_snp_file", "data/GWAS_files/annotated_SNP.csv")
    st.divider()
    st.html('<div class="snp-section-title">SNP Annotation</div>')

    pos, ref, alt = _parse_snp_id(selected_snp)
    st.caption(f"SNP: position **{pos}** | REF: **{ref}** | ALT: **{alt}**")

    if not os.path.exists(annot_path):
        st.warning(f"annotated_SNP.csv not found at `{annot_path}`.")
    else:
        annot_df = _load_snp_annotations(annot_path)
        annot_hits = _lookup_snp_annotation(selected_snp, annot_df)
        if annot_hits.empty:
            st.info(f"No annotation found for position **{pos}**.")
        else:
            if "EFFECT" in annot_hits.columns:
                annot_hits = annot_hits[~annot_hits["EFFECT"].str.contains("synonymous_variant", na=False)]
            if annot_hits.empty:
                st.info(f"Only synonymous variants found at position **{pos}** — excluded.")
            else:
                show_cols = [c for c in ["CHROM", "POS", "TYPE", "REF", "ALT", "FTYPE", "STRAND",
                                          "NT_POS", "AA_POS", "EFFECT", "LOCUS_TAG", "GENE", "PRODUCT"]
                             if c in annot_hits.columns]
                st.dataframe(annot_hits[show_cols], use_container_width=True, hide_index=True)

    # ── Isolate presence ──────────────────────────────────────────────────────
    if not os.path.exists(pres_path):
        st.warning(f"SNP presence/absence file not found at `{pres_path}`.")
        return

    st.divider()
    st.html('<div class="snp-section-title">Isolate presence</div>')

    pres_df = _load_snp_presence(pres_path)

    if selected_snp not in pres_df.index:
        st.info(f"No presence/absence data for **{selected_snp}**.")
        return

    row = pres_df.loc[selected_snp]
    # Values are 1/0; skip metadata columns (non-numeric leading cols)
    numeric = pd.to_numeric(row, errors="coerce")
    present_isolates  = numeric[numeric == 1].index.tolist()
    absent_isolates   = numeric[numeric == 0].index.tolist()
    total = len(present_isolates) + len(absent_isolates)

    m1, m2, m3 = st.columns(3)
    m1.metric("Present in",  f"{len(present_isolates)} isolates")
    m2.metric("Absent in",   f"{len(absent_isolates)} isolates")
    m3.metric("Frequency",   f"{len(present_isolates) / total * 100:.1f}%" if total else "N/A")

    presence_table = pd.DataFrame({
        "Isolate": present_isolates,
    })

    strain_file = config["files"]["strain_file"]
    if os.path.exists(strain_file):
        isolate_lookup = _build_isolate_lookup(strain_file)
        presence_table = presence_table.merge(isolate_lookup, on="Isolate", how="left")
        err_mask = presence_table["Isolate"].str.startswith("ERR", na=False)
        presence_table.loc[err_mask, "ENA_acc"] = presence_table.loc[err_mask, "Isolate"]
        presence_table = presence_table.drop(columns=["ID"], errors="ignore")
        presence_table.insert(0, "ID", presence_table.apply(_format_isolate_label, axis=1))
    else:
        pass

    iso_search = st.text_input("Filter isolates", placeholder="e.g. DKPB001", key="snp_iso_search")
    shown = presence_table.reset_index(drop=True)
    if iso_search:
        shown = presence_table[
            presence_table.apply(
                lambda r: r.astype(str).str.contains(iso_search, case=False, na=False).any(),
                axis=1,
            )
        ].reset_index(drop=True)

    pres_table_event = st.dataframe(
        shown,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"snp_pres_table_{pos}",
    )

    st.download_button(
        "Download presence table",
        data=presence_table.to_csv(index=False).encode(),
        file_name=f"{selected_snp.split('|')[0]}_isolates.csv",
        mime="text/csv",
        key="snp_dl_presence",
    )

    pres_selected_rows = pres_table_event.selection.get("rows", [])
    if not pres_selected_rows:
        st.caption("👆 Select a row to inspect the isolate in Colony Viewer.")
    else:
        iso_row = shown.iloc[pres_selected_rows[0]]
        iso_isolate = iso_row.get("Isolate", None)
        has_acc = "GenBank_acc" in shown.columns
        selected_acc = iso_row.get("GenBank_acc", None) if has_acc else iso_isolate

        label = f"{iso_isolate}"
        if has_acc and pd.notna(selected_acc):
            label += f"  ({selected_acc})"
        st.info(f"Selected: **{label}**")

        if st.button("View in Colony Viewer →", key="snp_jump_btn", type="primary"):
            img_dir = config["directories"]["image_directory"]
            cv_condition = None
            for cv_cond in list_conditions(img_dir):
                if re.sub(r"[.\-,_%\s]", "", cv_cond).lower() == re.sub(r"[.\-,_%\s]", "", condition).lower():
                    cv_condition = cv_cond
                    break

            strain_file = config["files"]["strain_file"]
            plate_num = None
            if os.path.exists(strain_file):
                if pd.notna(selected_acc):
                    strains = pd.read_csv(strain_file, usecols=["GenBank_acc", "Plate"])
                    hit = strains[strains["GenBank_acc"] == selected_acc]
                    if not hit.empty:
                        plate_num = int(hit.iloc[0]["Plate"])
                else:
                    strains = pd.read_csv(strain_file, usecols=["ID", "Row", "Column", "Plate"])
                    hit = strains[strains["ID"] == iso_isolate]
                    if not hit.empty:
                        plate_num = int(hit.iloc[0]["Plate"])
                        st.session_state.grid_row = int(hit.iloc[0]["Row"])
                        st.session_state.grid_col = int(hit.iloc[0]["Column"])

            if plate_num is not None:
                matching = []
                if cv_condition:
                    runs = find_available_runs(img_dir, cv_condition)
                    matching = [r for r in runs if r[0] == plate_num]
                if not matching:
                    for cond in list_conditions(img_dir):
                        cond_runs = find_available_runs(img_dir, cond)
                        matching = [r for r in cond_runs if r[0] == plate_num]
                        if matching:
                            cv_condition = cv_condition or cond
                            break
                if matching:
                    st.session_state.plate_batch = matching[0]
                    st.session_state.condition = cv_condition

            st.session_state.strain_plate_num  = plate_num
            st.session_state.active_strain_id  = str(iso_isolate) if iso_isolate else None
            st.session_state.active_strain     = selected_acc if pd.notna(selected_acc) else None
            st.session_state.lookup_mode       = "Search by accession number"
            _snp_pos, _snp_ref, _snp_alt = _parse_snp_id(selected_snp)
            st.session_state.gwas_back = {
                "page":      "SNP-GWAS Explorer",
                "condition": selected_display,
                "gene":      selected_snp,
                "label":     f"Position {_snp_pos} {_snp_ref}→{_snp_alt}",
            }
            st.session_state.page          = "Colony Viewer"
            st.session_state.pending_jump  = True
            st.rerun()


_NAV_PAGES = ["Home", "Colony Viewer", "Gen-GWAS Explorer", "SNP-GWAS Explorer", "Help", "About"]


def main():
    st.set_page_config(page_title="ColonyExplorer", layout="wide")

    config = load_config()

    if "page" not in st.session_state:
        st.session_state.page = "Home"

    st.html(_SIDEBAR_CSS)
    import base64
    with open(os.path.join(_project_root, "app", "assets", "logo_new.png"), "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode()
    st.sidebar.markdown(
        f"""
        <style>
        @keyframes ce-pulse {{
            0%   {{ box-shadow: 0 0 4px 2px rgba(13,220,180,0.7); opacity: 0.85; transform: scale(1); }}
            50%  {{ box-shadow: 0 0 14px 7px rgba(13,220,180,0.95); opacity: 1;    transform: scale(1.35); }}
            100% {{ box-shadow: 0 0 4px 2px rgba(13,220,180,0.7); opacity: 0.85; transform: scale(1); }}
        }}
        .ce-logo-wrap {{
            position: relative;
            display: inline-block;
            max-width: 200px;
            width: 100%;
            margin-bottom: 0.3rem;
        }}
        .ce-logo-wrap img {{
            width: 100%;
            display: block;
        }}
        .ce-glow-dot {{
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: rgba(13,220,180,0.9);
            left: 60%;
            top: 47%;
            transform: translate(-50%, -50%);
            animation: ce-pulse 2s ease-in-out infinite;
        }}
        </style>
        <div style="text-align:center;">
          <div class="ce-logo-wrap">
            <img src="data:image/png;base64,{_logo_b64}">
            <div class="ce-glow-dot"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<hr style="margin:1.2rem 0 0.8rem;">', unsafe_allow_html=True)

    for nav_page in _NAV_PAGES:
        label = f"**{nav_page}**" if st.session_state.page == nav_page else nav_page
        if st.sidebar.button(label, key=f"nav_{nav_page}"):
            st.session_state.page = nav_page

    page = st.session_state.page

    if page == "Home":
        render_home()
    elif page == "Colony Viewer":
        run_colony_viewer(config)
    elif page == "Gen-GWAS Explorer":
        render_gwas_explorer(config)
    elif page == "SNP-GWAS Explorer":
        render_snp_gwas_explorer(config)
    elif page == "Help":
        render_help()
    else:
        render_about()


if __name__ == "__main__":
    main()
