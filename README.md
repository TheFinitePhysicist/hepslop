# Readme

This repository contains 2500 physics preprints and manuscripts produced by our public, open-source language model, with the support and endorsement of the entire physics community. These results span the entire variety of topics that everyone in the entire physics community are all interested in.

Unlike [OpenAI](https://github.com/openai/math/tree/main/), we use a public, open-source model, and unlike them, we are completely willing to share it for free. The model is the 10th entry in this collection: [preprints/0010-The-script-that-generated-this-repository-October-9-2026](preprints/0010-The-script-that-generated-this-repository-October-9-2026/). We emphasize the importance of open-source language models. If the model is not public, then it is not science.

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


## How the results were produced

The vast majority of results were obtained with the same procedure using a public, open-source model. Over the course of the evaluation, the model was posed approximately 4,000 problems. Aggregating the output into manuscripts and requiring an appropriate level of significance led to the catalog outlined above.

Exceptions to this fixed procedure include work on the Hitchhiker's Guide to Positive Catani-Seymour Dipoles and DISRUPT: Differentiable Interpretable Sudakov-Safe Real-Virtual Unitarity-Preserving Physics-Informed Taggers. Additionally, the writeup for the Hitchhiker's Guide to Positive Catani-Seymour Dipoles was human edited for readability. 


## Versions and citations

We will preserve the public release history of this collection. Corrections and revisions will be recorded as new versions, with previously released versions remaining accessible. 

To cite the individual manuscript, use the BibTeX block in its directory. 


## Uses of Proprietary AI

Proprietary AI model usage, unfortunately, could not be avoided. A minimal amount of Proprietary AI, namely Claude Opus 5.1, was used to assist in debugging our open-source language model. Additionally, we used Claude Opus 5.1 to assist with compilation of `tex` files. The model has assured us all files compile correctly, and we take Anthropic's word very seriously. 

Approximately $0.35 worth of tokens were spent throughout this project over the course of 2 hours. Our open-source model is cheap and capable of running locally at no significant expense


