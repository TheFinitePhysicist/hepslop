# [The script that generated this repository](generate.py)

**Author:** The Physics Community

**Date:** October 9, 2026

Every file in this repository outside this directory, apart from the top-level README, was produced by `generate.py` from the probabilistic context-free grammar in [`grammar/`](grammar/). The generator is deterministic: running it again with the same seed reproduces the repository.

## Running it

```
python generate.py
```

It needs Python 3 with numpy and matplotlib, and a TeX installation with pdflatex and bibtex.

## Files

- `generate.py`: families, titles, withdrawals, revisions, compile jobs and the index files
- `slop/grammar.py`: the grammar engine
- `slop/tex.py`: LaTeX sources, and the breakage for papers that do not compile
- `slop/pdfs.py`: corrupted PDFs, figures and compilation
- `slop/indexes.py`: READMEs, the manuscript map, the history and the Lean stub
- `grammar/*.txt`: the grammar, one production per line
