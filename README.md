# Readme

This repository contains physics manuscripts and supporting proof artifacts produced by a public, open-source model. 

Unlike OpenAI, we use a public, open-source model, and unlike them, we are completely willing to share it for free. The model is the 10th entry in this collection: [preprints/0010-The-script-that-generated-this-repository-October-9-2026](preprints/0010-The-script-that-generated-this-repository-October-9-2026/).

As part of model development, we evaluate our models on open research problems. We expanded these evaluations after performance on our existing physics evaluations saturated. Some outputs build upon earlier results produced by the models.

This collection includes results at different stages of verification. 

Though unlikely, some of the unformalized results could have issues. We will endeavor to fix any such issues quickly.
We are also exploring community-hosted repositories for these materials. 

## Navigating the collection

The current catalog contains over 2000 manuscripts.

- Start with the [overview](overview.pdf) for descriptions of the manuscripts.
- Use the [manuscript map](CONTENTS.md) to find individual papers and their supporting materials.
- The [`preprints/`](preprints/) directory contains PDFs, source files, and manuscript-specific citation and build instructions.
- The [Lean library](lean/README.md) describes the available formal proofs. Unlike OpenAI, we have endeavored to only upload formal proofs that have already been certified by the community.
- Updates to the repo are described in the [history](history.md).

### Reasoning summaries

We are also releasing abridged summaries of the model's reasoning, covering the following results:

| Manuscript | Subject |
|---|---|
| 0185 | [Attention Is All You Need for Nuisance Parameters](reasoning_traces/attention-is-all-you-need-for-nuisance-parameters.pdf) |
| 0422 | [Embeddings for Free](reasoning_traces/embeddings-for-free.pdf) |
| 0539 | [Are Mellin Moments Finite?](reasoning_traces/are-mellin-moments-finite.pdf) |
| 0944 | [SYNERGY: Scalable Yang-Mills Neural Equivariant Robust Generative Yields](reasoning_traces/synergy-scalable-yang-mills-neural-equivariant-robust-genera.pdf) |
| 0980 | [HYPERSCALE: Hadronic Yang-Mills Positive Energy-Weighted Renormalized Soft Collinear Attention-Based Logarithmic Emissions](reasoning_traces/hyperscale-hadronic-yang-mills-positive-energy-weighted-reno.pdf) |
| 1617 | [The Hitchhiker's Guide to Positive Catani-Seymour Dipoles](reasoning_traces/the-hitchhikers-guide-to-positive-catani-seymour-dipoles.pdf) |
| 1853 | [When Do Soft Drop Observables Become Logarithmically Divergent?](reasoning_traces/when-do-soft-drop-observables-become-logarithmically-diverge.pdf) |
| 2006 | [DISRUPT: Differentiable Interpretable Sudakov-Safe Real-Virtual Unitarity-Preserving Physics-Informed Taggers](reasoning_traces/disrupt-differentiable-interpretable-sudakov-safe-real-virtu.pdf) |
| 2093 | [A Two-Loop Message-Passing Neural Network for Signal Regions in Higgs Boson Production in Gluon Fusion](reasoning_traces/a-two-loop-message-passing-neural-network-for-signal-regions.pdf) |
| 2164 | [Glauber Modes from Splitting Functions](reasoning_traces/glauber-modes-from-splitting-functions.pdf) |


## How the results were produced

The vast majority of results were obtained with the same procedure using a public, open-source model. Over the course of the evaluation, the model was posed approximately 4,000 problems. Aggregating the output into manuscripts and requiring an appropriate level of significance led to the catalog outlined above.

Exceptions to this fixed procedure include work on the Hitchhiker's Guide to Positive Catani-Seymour Dipoles and DISRUPT: Differentiable Interpretable Sudakov-Safe Real-Virtual Unitarity-Preserving Physics-Informed Taggers. Additionally, the writeup for the Hitchhiker's Guide to Positive Catani-Seymour Dipoles was human edited for readability. 


## Versions and citations

We will preserve the public release history of this collection. Corrections and revisions will be recorded as new versions, with previously released versions remaining accessible. 

To cite the individual manuscript, use the BibTeX block in its directory. 
