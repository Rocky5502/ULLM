# Generated manuscript artifacts

Files in this directory are machine-generated from audited experiment outputs. The committed `.tex` files contain **TBD placeholders only** so the manuscript compiles before paid API execution.

After all frozen runs pass `scripts/audit_run.py`, `scripts/analyze_frozen.ps1` (or the POSIX equivalent) regenerates the result CSVs, figures, and these LaTeX tables. Numerical cells must never be hand-edited in `paper/main.tex`.

The generator is `scripts/make_paper_tables.py`. The compact RQ3 operating point is fixed in `configs/experiment.yaml`; the full threshold sweep remains in the processed CSV/figures.
