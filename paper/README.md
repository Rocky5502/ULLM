# Paper package

`main.tex` is the provisional IASEAI'27 manuscript, currently formatted with the **official AAAI 2027 author kit supplied by the project owner** because the IASEAI'27 paper-format guide has not yet been published publicly. We will re-check IASEAI's official guide before submission and switch templates if required.

The downloadable Overleaf package prepared with this repository contains the unmodified `aaai2027.sty` and `aaai2027.bst` files from that kit, the manuscript source, editable TikZ figures, references, and a compiled PDF preview.

The checked-in manuscript deliberately contains `TBD` for all empirical results. No result value or statistical claim should be filled until a corresponding raw API artifact and run manifest exist.

## Local compile

With a standard TeX Live installation:

```bash
cd paper
pdflatex main.tex
pdflatex main.tex
```

The current verified preview uses the manual bibliography file `references_manual.tex` so it can compile even in environments without BibTeX. `references.bib` is also maintained for the final Overleaf workflow.

## Editable figures

Figures in `figures/fig_*.tex` are TikZ vector sources. The standalone PDF versions are generated from those sources for inspection/export; edit the `.tex` source rather than rasterizing the figure.
