"""
Streamlit interface for visualising colony morphology across imaging conditions.
"""
import csv
import glob
import os
import re
import sys

import cv2
import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loading import load_csv, load_excel, load_iris, parse_iris_grid, read_tabular
from app.utils.image_handling import load_plate_image, extract_colony, find_grid_params
from app.strain_overview import render_strain_overview, render_resistance, render_virulence, render_detailed_tables

ALL_METRICS = [
    'colony size', 'circularity', 'colony color intensity', 'biofilm area size',
    'biofilm color intensity', 'biofilm area ratio', 'size normalized color intensity',
    'mean sampled color intensity', 'average pixel saturation', 'opacity', 'max 10% opacity',
]
DEFAULT_METRICS = ['circularity', 'colony size', 'opacity', 'biofilm color intensity']

_LOOKUP_BY_ID  = "Search by accession number"
_LOOKUP_BY_POS = "Enter grid position"

_CSS = """
<style>
  ul  { margin-top: 0; margin-bottom: 0; padding-left: 18px; }
  li  { margin-bottom: 2px; }
  table { width: 100%; border-collapse: collapse; background: transparent; }
  th, td { background: transparent; text-align: left;
            padding: 5px; vertical-align: top; border: none; }
</style>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hero_card(label: str, value: str,
               bg_color: str = "#f0f2f6", text_color: str = "#31333f") -> None:
    st.markdown(
        f"""
        <div style="
            background-color: {bg_color};
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid rgba(49, 51, 63, 0.1);
        ">
            <p style="margin:0;font-size:0.8rem;font-weight:600;
                      color:{text_color};opacity:0.8;">{label}</p>
            <p style="margin:0;font-size:1.8rem;font-weight:700;
                      color:{text_color};">{value}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def _load_fitness_df(path: str) -> pd.DataFrame:
    """Load absolute fitness CSV with strain IDs as index."""
    return pd.read_csv(path, index_col=0)



@st.cache_data(show_spinner=False)
def _load_condition_clean_tags(mapping_path: str) -> dict[str, str]:
    """Return {normalised_key: Clean_Tag} from condition_clean_tags_mapping.csv."""
    result = {}
    if not os.path.exists(mapping_path):
        return result
    with open(mapping_path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            fname = row.get("File_name", "").strip()
            ctag  = row.get("Clean_Tag", "").strip()
            if fname and ctag:
                key = re.sub(r"[.\-,_%\s]", "", fname).lower()
                result[key] = ctag
    return result


@st.cache_data(show_spinner=False)
def list_conditions(img_dir: str) -> list[str]:
    """Return sorted unique condition names found in *img_dir*."""
    names = set()
    for fpath in glob.glob(os.path.join(img_dir, "*.JPG.grid.jpg")):
        m = re.match(r'^(.*)-(\d+)-(\d+)_A\.JPG\.grid\.jpg$', os.path.basename(fpath))
        if m:
            names.add(m.group(1))
    return sorted(names)


@st.cache_data(show_spinner=False)
def find_available_runs(img_dir: str, condition: str) -> list[tuple[int, int]]:
    """
    Return sorted (plate, batch) pairs available on disk for *condition*.
    Each pair corresponds to a single image file.
    """
    runs: set[tuple[int, int]] = set()
    esc = re.escape(condition)
    for fpath in glob.glob(os.path.join(img_dir, f"{condition}-*-*_A.JPG.grid.jpg")):
        m = re.match(fr'^{esc}-(\d+)-(\d+)_A\.JPG\.grid\.jpg$', os.path.basename(fpath))
        if m:
            runs.add((int(m.group(1)), int(m.group(2))))
    return sorted(runs)


def _well_positions_1536(source_row: int, source_col: int) -> dict[str, dict[str, int]]:
    """
    Map a 384-well coordinate to the four corresponding 1536-well positions.
    Each 384-well position expands to a 2×2 block of quadruplicates (A–D).
    """
    r = (source_row * 2) - 1
    c = (source_col * 2) - 1
    return {
        'A': {'row': r,     'col': c},
        'B': {'row': r,     'col': c + 1},
        'C': {'row': r + 1, 'col': c},
        'D': {'row': r + 1, 'col': c + 1},
    }


def _init_state(strain_map: pd.DataFrame, conditions: list[str]) -> None:
    """Populate session state keys that are not yet set."""
    defaults = {
        'lookup_mode':      _LOOKUP_BY_ID,
        'active_strain_id': str(strain_map.iloc[0]['ID']) if not strain_map.empty else None,
        'active_strain':    strain_map['GenBank_acc'].dropna().tolist()[0] if not strain_map.empty else None,
        'grid_row':         1,
        'grid_col':         1,
        'condition':        conditions[0] if conditions else None,
        'plate_batch':      None,
        'active_metrics':   DEFAULT_METRICS,
        'results':          None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def run_colony_viewer(config: dict) -> None:
    st.html("""
    <style>
    .cv-banner {
        background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
        border-radius: 12px;
        padding: 1.4rem 2rem;
        margin-bottom: 1.2rem;
    }
    .cv-banner h2 { margin: 0 0 0.3rem; font-size: 1.7rem; font-weight: 700; color: #ffffff; }
    .cv-banner p  { margin: 0; color: rgba(255,255,255,0.85); font-size: 0.92rem; }
    .cv-section-title {
        border-left: 4px solid #0d9488;
        padding: 0.15rem 0 0.15rem 0.7rem;
        margin: 0.2rem 0 0.6rem;
        font-size: 1.5rem;
        font-weight: 700;
    }
    .cv-subsection-title {
        border-left: 3px solid rgba(13,148,136,0.45);
        padding: 0.1rem 0 0.1rem 0.6rem;
        margin: 0.2rem 0 0.4rem;
        font-size: 0.97rem;
        font-weight: 600;
    }
    </style>
    <div class="cv-banner">
        <h2>Colony Viewer</h2>
        <p>Genotype–phenotype browser — link plate images with IRIS morphology and Kleborate genomic data.</p>
    </div>
    """)
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("""
    <style>
    [data-testid="stSidebar"] [data-testid="baseButton-primary"] {
        background-color: #0d9488 !important;
        border-color: #0d9488 !important;
        color: white !important;
    }
    [data-testid="stSidebar"] [data-testid="baseButton-primary"]:hover {
        background-color: #0f766e !important;
        border-color: #0f766e !important;
    }
    </style>
    """, unsafe_allow_html=True)

    img_dir   = config['directories']['image_directory']
    iris_dir  = config['directories']['iris_directory']

    strain_file = config['files']['strain_file']
    if strain_file.endswith('.csv'):
        load_csv.clear()
        strain_map = load_csv(strain_file)
    else:
        load_excel.clear()
        strain_map = load_excel(strain_file)

    conditions = list_conditions(img_dir)
    _init_state(strain_map, conditions)

    def _reset_plate_batch() -> None:
        """Reset plate_batch when condition changes."""
        cur_runs = find_available_runs(img_dir, st.session_state.condition)
        sp = st.session_state.get('strain_plate_num')
        cur_filtered = [pb for pb in cur_runs if pb[0] == sp] if sp is not None else cur_runs
        st.session_state.plate_batch = cur_filtered[0] if cur_filtered else None

    def run_analysis() -> None:
        # run_analysis is called as an on_click callback, which executes BEFORE the
        # page script body (and therefore before the pre-sync block).  We must
        # validate plate_batch against the current condition ourselves.
        _avail = find_available_runs(img_dir, st.session_state.condition)
        if st.session_state.get('plate_batch') not in _avail:
            st.session_state.plate_batch = _avail[0] if _avail else None

        run = st.session_state.plate_batch
        if run is None:
            st.error("No plate/batch available.")
            st.session_state.results = None
            return

        plate_num, batch_num = run

        if st.session_state.lookup_mode == _LOOKUP_BY_ID:
            _acc = st.session_state.get('active_strain')   # GenBank accession (None if NA)
            if _acc and pd.notna(_acc):
                # Has accession — search by accession (unique across all plates)
                strain_row = strain_map[strain_map['GenBank_acc'] == _acc]
            else:
                # No accession — search by grid position + plate
                strain_row = strain_map[
                    (strain_map['Row']    == st.session_state.grid_row) &
                    (strain_map['Column'] == st.session_state.grid_col) &
                    (strain_map['Plate']  == plate_num)
                ]
        else:
            strain_row = strain_map[
                (strain_map['Row']    == st.session_state.grid_row) &
                (strain_map['Column'] == st.session_state.grid_col) &
                (strain_map['Plate']  == plate_num)
            ]

        if strain_row.empty:
            st.error("Strain not found in the coordinate map.")
            st.session_state.results = None
            return

        fname = f"{st.session_state.condition}-{plate_num}-{batch_num}_A.JPG.grid.jpg"
        img_path = os.path.join(img_dir, fname)
        if not os.path.exists(img_path):
            st.warning(f"Image not found: {fname}")
            st.session_state.results = None
            return

        plate_img = load_plate_image(img_path)
        if plate_img is None:
            st.error(f"Could not load image: {img_path}")
            st.session_state.results = None
            return

        iris_stem = os.path.basename(img_path).replace('.JPG.grid.jpg', '.JPG')
        iris_path = os.path.join(iris_dir, f"{iris_stem}.iris")
        measurements = None
        iris_grid_params = None
        if os.path.exists(iris_path):
            try:
                measurements = load_iris(iris_path)
                iris_grid_params = parse_iris_grid(iris_path)
            except Exception as exc:
                st.warning(f"IRIS parse error: {exc}")

        src_r = int(strain_row.iloc[0]['Row'])
        src_c = int(strain_row.iloc[0]['Column'])
        well_map = _well_positions_1536(src_r, src_c)

        img_h, img_w = plate_img.shape[:2]
        if iris_grid_params is not None:
            tl = iris_grid_params['top_left']
            br = iris_grid_params['bottom_right']
            scale_x = img_w / br[0] if br[0] else 1.0
            scale_y = img_h / br[1] if br[1] else 1.0
            grid_origin = (int(round(tl[0] * scale_x)), int(round(tl[1] * scale_y)))
            cell_w = (br[0] - tl[0]) * scale_x / 48
            cell_h = (br[1] - tl[1]) * scale_y / 32
            cell_size = (cell_w, cell_h)
        else:
            grid_origin, cell_size = find_grid_params(plate_img)

        colony_crops = {
            label: extract_colony(
                plate_img,
                pos['row'] - 1, pos['col'] - 1,
                grid_origin=grid_origin, cell_size=cell_size,
            )
            for label, pos in well_map.items()
        }

        genbank_acc_at_run = (
            st.session_state.active_strain
            if st.session_state.lookup_mode == _LOOKUP_BY_ID and pd.notna(st.session_state.active_strain)
            else (strain_row.iloc[0]['GenBank_acc'] if not strain_row.empty else None)
        )
        strain_id_at_run = strain_row.iloc[0]['ID'] if not strain_row.empty else None
        ena_acc_at_run = strain_row.iloc[0].get('ENA_acc') if not strain_row.empty else None
        st.session_state.results = {
            'img_path':     img_path,
            'plate_img':    plate_img,
            'well_map':     well_map,
            'measurements': measurements,
            'colony_crops': colony_crops,
            'grid_origin':  grid_origin,
            'cell_size':    cell_size,
            'genbank_acc':  genbank_acc_at_run,
            'strain_id':    strain_id_at_run,
            'ena_acc':      ena_acc_at_run,
        }

    # ---- Controls panel (on main page) ----
    _clean_tags = _load_condition_clean_tags("data/condition_clean_tags_mapping.csv")

    def _fmt_condition(c: str) -> str:
        key = re.sub(r"[.\-,_%\s]", "", c).lower()
        return _clean_tags.get(key, c.rstrip("-"))

    matched_conditions = [c for c in conditions
                          if re.sub(r"[.\-,_%\s]", "", c).lower() in _clean_tags]
    display_conditions = matched_conditions if matched_conditions else conditions

    # Ensure the stored condition is selectable in the dropdown.
    # A keyed selectbox throws if its session-state value is not in options.
    # Use normalised comparison so minor formatting differences don't cause jumps.
    if st.session_state.get("condition") not in display_conditions:
        _norm = lambda s: re.sub(r"[.\-,_%\s]", "", s or "").lower()
        _cur_norm = _norm(st.session_state.get("condition", ""))
        _best = next(
            (c for c in display_conditions if _norm(c) == _cur_norm),
            None,
        )
        st.session_state.condition = _best if _best else (
            display_conditions[0] if display_conditions else None
        )

    _gwas_back = st.session_state.get("gwas_back")
    if _gwas_back:
        _back_label = _gwas_back.get("label") or _gwas_back["gene"]
        if st.button(f"← Back to GWAS: {_gwas_back['condition']}  |  {_back_label}"):
            st.session_state["gwas_jump_condition"] = _gwas_back["condition"]
            st.session_state["gwas_selected_gene"]  = _gwas_back["gene"]
            st.session_state.page = _gwas_back["page"]
            st.rerun()

    # Pre-sync plate_batch BEFORE any widget renders (Streamlit forbids modifying a
    # widget key after instantiation). Only do this on a GWAS jump so we don't
    # override the user's manual plate selection on every rerun.
    _pre_avail = find_available_runs(img_dir, st.session_state.condition)
    if st.session_state.get('pending_jump'):
        _pre_acc = st.session_state.get('active_strain')
        _pre_sid = st.session_state.get('active_strain_id')
        _pre_hit = pd.DataFrame()
        if _pre_acc and pd.notna(_pre_acc):
            _pre_hit = strain_map[strain_map['GenBank_acc'] == _pre_acc]
        if _pre_hit.empty and _pre_sid:
            _pre_hit = strain_map[strain_map['ID'].astype(str).str.strip() == str(_pre_sid).strip()]
        if not _pre_hit.empty:
            _pre_plate = int(_pre_hit.iloc[0]['Plate'])
            _pre_runs  = [r for r in _pre_avail if r[0] == _pre_plate]
            if _pre_runs:
                st.session_state.plate_batch = _pre_runs[0]
    if st.session_state.get('plate_batch') not in _pre_avail:
        st.session_state.plate_batch = _pre_avail[0] if _pre_avail else None

    st.html('<div class="cv-section-title">Analysis Settings</div>')

    # ── Row 1: condition + plate/batch + lookup (outside form → reactive) ──────
    # These three widgets commit immediately so that changing plate/batch updates
    # the sample list below without needing to click Analyse first.
    _c1, _c2, _c3 = st.columns([3, 2, 2])
    with _c1:
        st.selectbox("Condition", display_conditions, key='condition',
                     on_change=_reset_plate_batch,
                     format_func=_fmt_condition)
    with _c2:
        available_runs = _pre_avail
        if available_runs:
            st.selectbox("Plate / Batch", options=available_runs,
                         format_func=lambda pb: f"Plate {pb[0]}, Batch {pb[1]}",
                         key='plate_batch')
        else:
            st.warning("No images found for this condition.")
    with _c3:
        st.radio("Lookup method", (_LOOKUP_BY_ID, _LOOKUP_BY_POS), key='lookup_mode',
                 horizontal=True)

    # ── Row 2: sample + metrics + Analyse (inside form → atomic submit) ────────
    # Wrapping only the sample selector and Analyse button in a form prevents the
    # race condition where clicking Analyse mid-rerun commits a stale sample value.
    cur_plate_num = st.session_state.plate_batch[0] if st.session_state.plate_batch else None
    strain_plate = None

    with st.form("cv_settings_form", border=False):
        if st.session_state.lookup_mode == _LOOKUP_BY_ID:
            plate_df = (
                strain_map[strain_map['Plate'] == cur_plate_num]
                if cur_plate_num is not None else strain_map
            )
            # Internal keys encode ID|acc_or_NA|row|col for guaranteed uniqueness.
            # NA strains that share an ID with another NA strain get position shown.
            _na_ids = plate_df[plate_df['GenBank_acc'].isna()]['ID'].value_counts()
            _na_dup_ids = set(_na_ids[_na_ids > 1].index)

            plate_labels = [
                f"{row['ID']}|{row['GenBank_acc'] if pd.notna(row.get('GenBank_acc')) else 'NA'}"
                f"|{int(row['Row'])}|{int(row['Column'])}"
                for _, row in plate_df.iterrows()
            ]

            def _display_label(lbl: str) -> str:
                sid, acc, r, c = lbl.split("|")
                if acc != 'NA':
                    return f"{sid} ({acc})"
                if sid in _na_dup_ids:
                    return f"{sid} (NA, R{r}, C{c})"
                return f"{sid} (NA)"

            label_to_idx = {lbl: idx for idx, lbl in zip(plate_df.index, plate_labels)}
            acc_to_label = {
                row['GenBank_acc']: lbl
                for (_, row), lbl in zip(plate_df.iterrows(), plate_labels)
                if pd.notna(row.get('GenBank_acc'))
            }
            pos_to_label: dict[tuple[int, int], str] = {
                (int(row['Row']), int(row['Column'])): lbl
                for (_, row), lbl in zip(plate_df.iterrows(), plate_labels)
            }

            _cur_acc = st.session_state.get('active_strain')
            _cur_row = st.session_state.get('grid_row', 1)
            _cur_col = st.session_state.get('grid_col', 1)
            if _cur_acc and pd.notna(_cur_acc) and _cur_acc in acc_to_label:
                _target_label = acc_to_label[_cur_acc]
            else:
                _target_label = pos_to_label.get(
                    (_cur_row, _cur_col),
                    plate_labels[0] if plate_labels else None,
                )

            _force = (
                st.session_state.get('pending_jump') or
                '_sample_sel' not in st.session_state or
                st.session_state.get('_sample_sel') not in plate_labels
            )
            if _force and _target_label and _target_label in plate_labels:
                st.session_state['_sample_sel'] = _target_label

            selected_label = st.selectbox(
                "Sample (Strain ID / Accession)", plate_labels,
                key='_sample_sel',
                format_func=_display_label,
            )
            selected_row = strain_map.loc[label_to_idx[selected_label]] if selected_label in label_to_idx else None
            if selected_row is not None:
                selected_acc_val = selected_row.get('GenBank_acc') if isinstance(selected_row, pd.Series) else None
                st.session_state.active_strain    = selected_acc_val if pd.notna(selected_acc_val) else None
                st.session_state.active_strain_id = str(selected_row['ID']).strip()
                st.session_state.grid_row         = int(selected_row['Row'])
                st.session_state.grid_col         = int(selected_row['Column'])
                strain_plate                      = int(selected_row['Plate'])
                st.session_state.strain_plate_num = strain_plate
            strain_plate = st.session_state.get('strain_plate_num')
            st.caption(
                f"Position: ({st.session_state.grid_row}, {st.session_state.grid_col})"
                f" · Plate {strain_plate}"
            )
        else:
            st.session_state.strain_plate_num = None
            st.session_state.pop('_sample_sel', None)
            _g1, _g2 = st.columns(2)
            with _g1:
                st.number_input("Row (1–32)",    min_value=1, max_value=32, step=1, key='grid_row')
            with _g2:
                st.number_input("Column (1–48)", min_value=1, max_value=48, step=1, key='grid_col')
            match = strain_map[
                (strain_map['Row'] == st.session_state.grid_row) &
                (strain_map['Column'] == st.session_state.grid_col) &
                (strain_map['Plate'] == cur_plate_num)
            ] if cur_plate_num else pd.DataFrame()
            label = match.iloc[0]['ID'] if not match.empty else "unknown"
            st.caption(f"Strain: **{label}**")

        st.multiselect("Metrics", options=ALL_METRICS, key='active_metrics')
        _form_submitted = st.form_submit_button("Analyse", type="primary")

    # ---- Auto-run on first load or jump from another page only ----
    # Selection changes require the user to click Analyse explicitly.
    if st.session_state.get("pending_jump"):
        st.session_state.pending_jump = False
        run_analysis()
    elif _form_submitted:
        run_analysis()
    elif not st.session_state.results:
        run_analysis()

    # ---- Results ----
    if not st.session_state.results:
        return

    res            = st.session_state.results
    plate_img      = res['plate_img']
    well_map       = res['well_map']
    measurements   = res['measurements']
    colony_crops   = res['colony_crops']
    grid_origin    = res['grid_origin']
    cell_size      = res['cell_size']
    active_metrics = st.session_state.active_metrics

    # Resolve genbank accession from the run that was analysed
    genbank_acc = res.get('genbank_acc')

    kleb_row = None
    strain_id  = res.get('strain_id')
    ena_acc    = res.get('ena_acc')
    kleb = read_tabular(config['files']['kleborate_file'], sep='\t')
    if genbank_acc is not None:
        hit = kleb[kleb['GenBank_acc'] == genbank_acc]
        if not hit.empty:
            kleb_row = hit.iloc[0]
    if kleb_row is None and pd.notna(ena_acc):
        hit = kleb[kleb['ENA_acc'] == ena_acc]
        if not hit.empty:
            kleb_row = hit.iloc[0]
    if kleb_row is None and strain_id is not None:
        hit = kleb[kleb['strain'].str.lower() == str(strain_id).lower()]
        if not hit.empty:
            kleb_row = hit.iloc[0]

    st.divider()

    # ---- 0. Strain Overview — hero cards + automated insights ----
    if kleb_row is not None:
        st.html('<div class="cv-section-title">Strain Genomic Profile</div>')
        c1, c2, c3, c4, c5 = st.columns(5)

        try:
            vir_score = int(kleb_row.get('virulence_score', 0))
        except (ValueError, TypeError):
            vir_score = 0
        try:
            res_score = int(kleb_row.get('resistance_score', 0))
        except (ValueError, TypeError):
            res_score = 0
        try:
            amr_genes = int(kleb_row.get('num_resistance_genes', 0))
        except (ValueError, TypeError):
            amr_genes = 0

        vir_color = "#c0392b" if vir_score >= 4 else "#f39c12" if vir_score >= 2 else "#2ecc71"
        res_color = "#6e2c1d" if res_score >= 2 else "#2ecc71"

        with c1: _hero_card("ST (MLST)",  str(kleb_row.get('ST', '—')))
        with c2: _hero_card("K-type",     str(kleb_row.get('K_type', '—')))
        with c3: _hero_card("Virulence",  f"{vir_score}/5",  bg_color=vir_color, text_color="white")
        with c4: _hero_card("Resistance", f"{res_score}/3",  bg_color=res_color, text_color="white")
        with c5: _hero_card("AMR Genes",  str(amr_genes),    bg_color="#0d9488", text_color="white")

        st.write("")
        st.html('<div class="cv-subsection-title">Automated Analysis</div>')
        if vir_score > 3 and res_score > 2:
            st.error("**Warning: High-risk Hypervirulent & Carbapenem-resistant (Hv-CRKP) profile detected.**")
        elif res_score == 3 and amr_genes > 0:
            colony_size_vals = []
            if measurements is not None:
                for pos in well_map.values():
                    row_hit = measurements[
                        (measurements['row'] == pos['row']) &
                        (measurements['column'] == pos['col'])
                    ]
                    if not row_hit.empty and 'colony size' in row_hit.columns:
                        v = row_hit['colony size'].iloc[0]
                        if pd.notna(v):
                            colony_size_vals.append(float(v))
            avg_size = sum(colony_size_vals) / len(colony_size_vals) if colony_size_vals else None
            if avg_size is not None and avg_size < 2000:
                st.warning("**Potential Fitness Cost Detected.**")
                st.write(f"This strain has a maximum resistance score but shows a reduced mean "
                         f"colony size ({avg_size:.0f} units).")
                st.caption("This supports the hypothesis that heavy AMR gene carriage "
                           "imposes a physiological burden.")
            else:
                st.success("**Standard Profile.** No extreme clinical risks or growth deviations detected.")
        else:
            st.success("**Standard Profile.** No extreme clinical risks or growth deviations detected.")

        st.divider()
    elif genbank_acc is not None:
        display_id = strain_id or genbank_acc or "this strain"
        st.info(f"No genomic data found for **{display_id}**.")

    # ---- 1. Colony images — full width ----
    st.html('<div class="cv-section-title">Colony images and measurements</div>')
    img_cols = st.columns(4)
    for i, (label, pos) in enumerate(well_map.items()):
        with img_cols[i]:
            crop = colony_crops.get(label)
            if crop is not None:
                st.image(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB),
                         caption=f"Rep {label}  ·  R{pos['row']} C{pos['col']}",
                         width=200)
            else:
                st.warning(f"No image for replicate {label}")

    # ---- 2. Metrics table — full width ----
    if active_metrics:
        if measurements is not None:
            def _fmt(v) -> str:
                if v is None or not pd.notna(v):
                    return "—"
                s = f"{float(v):.4f}".rstrip('0').rstrip('.')
                return s

            reps = list(well_map.items())
            th_style = "padding:6px 12px;text-align:center;font-weight:600;border-bottom:2px solid #000;white-space:nowrap;"
            td_style = "padding:5px 12px;text-align:center;border-bottom:1px solid rgba(128,128,128,0.15);"
            td_label = "padding:5px 12px;text-align:left;font-weight:500;border-bottom:1px solid rgba(128,128,128,0.15);white-space:nowrap;"

            header = "".join(f"<th style='{th_style}'>Rep {lbl}</th>" for lbl, _ in reps)
            rows_html = ""
            for metric in active_metrics:
                cells = ""
                for _, pos in reps:
                    row_hit = measurements[
                        (measurements['row'] == pos['row']) &
                        (measurements['column'] == pos['col'])
                    ]
                    v = row_hit[metric].iloc[0] if (not row_hit.empty and metric in row_hit.columns) else None
                    cells += f"<td style='{td_style}'>{_fmt(v)}</td>"
                rows_html += f"<tr><td style='{td_label}'>{metric.title()}</td>{cells}</tr>"

            st.html(
                f"<table style='width:100%;border-collapse:collapse;font-size:0.85rem;'>"
                f"<thead><tr><th style='{th_style}text-align:left;'>Metric</th>{header}</tr></thead>"
                f"<tbody>{rows_html}</tbody></table>"
            )
        else:
            st.info("No IRIS measurements available for this plate.")

    if st.button("Save colony images"):
        out_dir = "saved_colonies"
        os.makedirs(out_dir, exist_ok=True)
        tag = (st.session_state.active_strain
               if st.session_state.lookup_mode == _LOOKUP_BY_ID
               else f"R{st.session_state.grid_row}C{st.session_state.grid_col}")
        cond_tag = st.session_state.condition.replace("/", "_").replace("\\", "_")
        saved = 0
        for rep, img_arr in colony_crops.items():
            if img_arr is not None:
                out_path = os.path.join(out_dir, f"{tag}_{cond_tag}_{rep}.png")
                if cv2.imwrite(out_path, img_arr):
                    saved += 1
        if saved:
            st.success(f"Saved {saved} images to '{out_dir}/'")
        else:
            st.warning("No images to save.")

    # ---- 3. Plate context — collapsible ----
    with st.expander("📍 View Plate Context", expanded=False):
        st.caption(f"Source: {os.path.basename(res['img_path'])}")
        if plate_img is not None:
            overlay = cv2.cvtColor(plate_img, cv2.COLOR_BGR2RGB).copy()
            ox, oy = grid_origin
            cw, ch = cell_size
            for pos in well_map.values():
                r0, c0 = pos['row'] - 1, pos['col'] - 1
                x1 = int(round(ox + c0 * cw))
                y1 = int(round(oy + r0 * ch))
                cv2.rectangle(overlay, (x1, y1),
                              (int(round(x1 + cw)), int(round(y1 + ch))),
                              (0, 0, 255), 4)
            st.image(overlay, caption="Replicate locations highlighted in blue",
                     use_container_width=True)

    st.divider()

    # ---- 3b. Fitness Distribution ----
    _fitness_path = "data/absolute_fitness.csv"
    if os.path.exists(_fitness_path):
        import plotly.graph_objects as go
        from scipy.stats import gaussian_kde, percentileofscore
        import numpy as np

        _fitness_df = _load_fitness_df(_fitness_path)
        _cond_key = re.sub(r"[.\-,_%\s]", "", st.session_state.condition or "").lower()
        _col_map = {re.sub(r"[.\-,_%\s]", "", c).lower(): c for c in _fitness_df.columns}
        _fitness_col = _col_map.get(_cond_key)

        # Resolve isolate ID → fitness value (try strain_id first, then ENA)
        def _resolve_isolate_val(fitness_df, col, s_id, ena):
            if col is None:
                return None, s_id
            for lookup_id in ([s_id] if s_id else []) + ([ena] if ena else []):
                if lookup_id and lookup_id in fitness_df.index:
                    v = fitness_df.loc[lookup_id, col]
                    fv = float(v) if pd.notna(v) and float(v) != 0 else None
                    if fv is not None:
                        return fv, lookup_id
            return None, s_id

        _strain_val, _strain_label = _resolve_isolate_val(
            _fitness_df, _fitness_col, strain_id, res.get("ena_acc")
        )
        _cond_display = _clean_tags.get(_cond_key, st.session_state.condition or "")
        _isolate_display = _strain_label or strain_id or "—"

        st.html('<div class="cv-section-title">Fitness Distribution</div>')
        if not _fitness_col:
            st.info(
                f"No fitness data available for **{_cond_display}**. "
                "This condition has plate images but was not included in the absolute fitness experiment."
            )
        if _fitness_col:
            _vals = _fitness_df[_fitness_col].replace(0, float("nan")).dropna()
            _arr  = _vals.values.astype(float)
            _kde  = gaussian_kde(_arr, bw_method="scott")
            _span = _arr.max() - _arr.min()
            _x    = np.linspace(_arr.min() - 0.05 * _span, _arr.max() + 0.05 * _span, 500)
            _y    = _kde(_x)
            _median = float(np.median(_arr))

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=_x, y=_y, mode="lines",
                line=dict(color="black", width=1.5),
                fill="tozeroy", fillcolor="rgba(180,180,180,0.5)",
                name="Population",
                hovertemplate="Fitness: %{x:.3f}<br>Density: %{y:.4f}<extra></extra>",
            ))
            # Median dotted line (no inline annotation — shown in caption below)
            fig.add_vline(x=_median, line_dash="dot", line_color="black", line_width=1.5)
            if _strain_val is not None:
                _pct = percentileofscore(_arr, _strain_val, kind="rank")
                _iso_density = float(_kde(np.array([_strain_val]))[0])
                fig.add_vline(x=_strain_val, line_color="#e74c3c", line_width=2)
                fig.add_trace(go.Scatter(
                    x=[_strain_val], y=[_iso_density],
                    mode="markers",
                    marker=dict(color="#e74c3c", size=11, symbol="circle",
                                line=dict(color="white", width=1.5)),
                    name=_isolate_display,
                    hovertemplate=(f"<b>{_isolate_display}</b><br>"
                                   f"Fitness: {_strain_val:.3f}<br>"
                                   f"Percentile: {_pct:.0f}th<extra></extra>"),
                ))
            elif strain_id:
                st.caption(f"No fitness data for **{strain_id}** in this condition.")

            fig.update_layout(
                title=dict(
                    text=f"Distribution: {_cond_display}   |   Isolate: {_isolate_display}",
                    font=dict(size=14), x=0, xanchor="left",
                ),
                xaxis_title="Fitness", yaxis_title="Density",
                showlegend=False, height=380,
                plot_bgcolor="white",
                margin=dict(t=60, b=50, l=60, r=30),
                xaxis=dict(gridcolor="rgba(0,0,0,0.08)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0.08)", zeroline=True,
                           zerolinecolor="rgba(0,0,0,0.1)"),
            )
            st.plotly_chart(fig, use_container_width=True)
            # Summary caption below the chart
            if _strain_val is not None:
                st.caption(
                    f"▪ **Median** (dotted): {_median:.3f} &nbsp;&nbsp;"
                    f"▪ **{_isolate_display}** (red): {_strain_val:.3f} &nbsp;&nbsp;"
                    f"▪ Percentile: **{_pct:.0f}th**"
                )

    # ---- 4. Genomics panels — full width ----
    if kleb_row is not None:
        st.divider()
        render_resistance(kleb_row)
        st.divider()
        render_virulence(kleb_row)
        st.divider()
        render_detailed_tables(kleb_row)


colonypicker = run_colony_viewer
