import re
import textwrap

# author and repository in every citation
AUTHOR = "The Physics Community"
BIB_AUTHOR = "{The Physics Community}"
REPOSITORY_URL = "https://github.com/TheFinitePhysicist/hepslop"

# width of the manuscript numbers
NUMBER_WIDTH = 4

# XeLaTeX preamble for the overview and the reasoning summary
XELATEX_LINES = [r"\documentclass[11pt]{article}", r"\usepackage{fontspec}", r"\usepackage{unicode-math}", r"\setmainfont{TeX Gyre Pagella}", r"\setmathfont{TeX Gyre Pagella Math}", r"\usepackage[margin=1in]{geometry}", r"\usepackage{hyperref}"]


# lines joined into file text
def to_text(lines):

    return "\n".join(lines) + "\n"


# raw inline math in titles turned into GitHub math
def markdown_math(text):

    return re.sub(r"\$([^$`]+)\$", r"$`\1`$", text)


# zero-padded manuscript number
def number_text(number):

    return str(number).zfill(NUMBER_WIDTH)


# bibtex block for one manuscript
def citation_lines(manuscript):

    key = "TPC:" + manuscript["directory"]
    link = REPOSITORY_URL + "/blob/main/preprints/" + manuscript["directory"] + "/" + manuscript["pdf_name"]
    lines = ["@misc{" + key + ",", "  author = {" + BIB_AUTHOR + "},", "  title = {{" + manuscript["title"] + "}},"]
    lines.append("  howpublished = {hepslop preprint")
    lines.append("                  \\href{" + link + "}{" + key + "}},")
    lines.extend(["  year = {2026}", "}"])
    return lines


# readme with citation and optional version note
def manuscript_readme(manuscript):

    lines = ["# [" + manuscript["title"] + "](" + manuscript["pdf_name"] + ")", "", "**Author:** " + AUTHOR, "", "**Date:** " + manuscript["date_text"], "", "## Citation", "", "```bibtex"]
    lines.extend(citation_lines(manuscript))
    lines.append("```")

    # superseded editions stay linked
    previous = manuscript.get("previous")
    if previous is not None:
        lines.extend(["", "## Version note", "", "This version " + manuscript["fix"] + "; see the [previous version](../" + previous["directory"] + "/" + previous["pdf_name"] + ")."])

    return to_text(lines)


# notice left in place of a withdrawn manuscript
def withdrawn_readme(manuscript, reason, withdrawal_date, revision):

    link = REPOSITORY_URL + "/blob/" + revision + "/preprints/" + manuscript["directory"] + "/manuscript.pdf"
    lines = ["# [Withdrawal notice: " + manuscript["title"] + "](manuscript.pdf)", "", AUTHOR + "  ", "**Withdrawn on " + withdrawal_date + ".**", ""]
    lines.append("In this manuscript, " + reason + ". The remaining argument does not establish the stated result, and the manuscript has been withdrawn.")
    lines.extend(["", "## Archived manuscript", "", "The withdrawn manuscript is preserved at [this revision](" + link + ").", "", "Repository revision: `" + revision + "`."])
    return to_text(lines)


# one table body holding a single cell
def table_cell(content_lines):

    return ["<tbody><tr>", "<td>", ""] + content_lines + ["", "</td>", "</tr></tbody>"]


# one page of the manuscript map, links relative to the contents directory
def contents_page(items, first, last):

    lines = ["# Manuscripts " + number_text(first) + " to " + number_text(last), "", "[Back to the manuscript map](../CONTENTS.md)", "", "<table>", "<thead><tr><th>Manuscript</th></tr></thead>"]
    for item in items:
        number = number_text(item["number"])

        # the generator links its script
        directory = item.get("script_directory")
        if directory is not None:
            script_link = "../preprints/" + directory + "/generate.py"
            lines.extend(table_cell(["**" + number + ".** [generate.py](" + script_link + ")", "", "The probabilistic context-free grammar in [grammar/](../preprints/" + directory + "/grammar/) and the script [generate.py](" + script_link + ") produced the manuscripts in this repository."]))
            continue

        # one cell per manuscript with its abstract
        link = "../preprints/" + item["directory"] + "/" + item["pdf_name"]
        lines.extend(table_cell(["**" + number + ".** [" + markdown_math(item["title"]) + "](" + link + ")", "", item["abstract_markdown"]]))

    lines.append("</table>")
    return to_text(lines)


# manuscript map split into pages of a fixed size, keyed by relative path
def contents_files(items, manuscript_count, page_size):

    files = {}
    lines = ["# Physics manuscript collection", "", "**" + str(manuscript_count) + " manuscripts.**", "", "[**Read the overview PDF**](overview.pdf).", "", "## Manuscript map", "", "Each manuscript is followed by its abstract. Paper titles link directly to PDFs.", ""]
    for start in range(0, len(items), page_size):

        # one page and its line in the index
        chunk = items[start:start + page_size]
        first = chunk[0]["number"]
        last = chunk[-1]["number"]
        name = "contents/" + number_text(first) + "-" + number_text(last) + ".md"
        files[name] = contents_page(chunk, first, last)
        lines.append("- [Manuscripts " + number_text(first) + " to " + number_text(last) + "](" + name + ")")

    files["CONTENTS.md"] = to_text(lines)
    return files


# top-level readme for a fresh build
def readme_markdown(manuscript_count, traces, exceptions, script_directory, parameter_count):

    lines = ["# Readme", "", "This repository contains physics manuscripts and supporting proof artifacts produced by a public, open-source model. ", ""]
    lines.extend(["Unlike OpenAI, we DO use a public, open-source model, and unlike them, we are completely willing to be real scientists and share it for free. The model is the 10th entry in this collection: [preprints/" + script_directory + "](preprints/" + script_directory + "/), all " + str(parameter_count) + " parameters of it.", ""])
    lines.extend(["As part of model development, we evaluate our models on open research problems. We expanded these evaluations after performance on our existing physics evaluations saturated. Some outputs build upon earlier results produced by the models.", ""])
    lines.extend(["This collection includes results at different stages of verification. ", ""])
    lines.extend(["Some of the unformalized results could have issues. We will endeavor to fix any such issues quickly.", "We are also exploring community-hosted repositories for these materials. ", ""])

    # navigation
    lines.extend(["## Navigating the collection", "", "The current catalog contains " + str(manuscript_count) + " manuscripts.", ""])
    lines.append("- Start with the [overview](overview.pdf) for descriptions of the manuscripts.")
    lines.append("- Use the [manuscript map](CONTENTS.md) to find individual papers and their supporting materials.")
    lines.append("- The [`preprints/`](preprints/) directory contains PDFs, source files, and manuscript-specific citation and build instructions.")
    lines.append("- The [Lean library](lean/README.md) describes the available formal proofs.")
    lines.extend(["- Updates to the repo are described in the [history](history.md).", ""])

    # reasoning summaries table
    lines.extend(["### Reasoning summaries", "", "We are also releasing abridged summaries of the model's reasoning, covering the following results:", "", "| Manuscript | Subject |", "|---|---|"])
    for number, subject, file_name in traces:
        lines.append("| " + number_text(number) + " | [" + markdown_math(subject) + "](reasoning_traces/" + file_name + ") |")
    lines.extend(["", ""])

    # production and citation sections
    lines.extend(["## How the results were produced", "", "The vast majority of results were obtained with the same procedure using a public, open-source model. Over the course of the evaluation, the model was posed approximately 4,000 problems. Aggregating the output into manuscripts and requiring an appropriate level of significance led to the catalog outlined above.", ""])
    lines.extend(["Exceptions to this fixed procedure include work on " + exceptions[0] + " and " + exceptions[1] + ". Additionally, the writeup for " + exceptions[0] + " was human edited for readability. ", "", ""])
    lines.extend(["## Versions and citations", "", "We will preserve the public release history of this collection. Corrections and revisions will be recorded as new versions, with previously released versions remaining accessible. ", "", "To cite the individual manuscript, use the BibTeX block in its directory. "])
    return to_text(lines)


# withdrawals, fixes and the formalization count
def history_markdown(withdrawn_titles, withdrawal_reason, fixes, updated_count, manuscript_count):

    lines = ["# History", "", "For any withdrawn papers, their README files explain the gap and link to the retracted manuscript. For any updated papers, previously published editions remain accessible through the version notes in their README.", "", "## October 7, 2026", "", "**Withdrawals**", ""]
    lines.extend(["In “" + withdrawn_titles[0] + "” " + withdrawal_reason + " and the construction used by two dependent papers. As a result, we have withdrawn the following three manuscripts:", ""])
    lines.extend(["- " + title for title in withdrawn_titles])
    lines.extend(["", "The withdrawn papers now carry notices explaining the gap and linking to the archived manuscripts.", "", "**Fixes**", ""])

    # one bullet per revised manuscript
    lines.extend(["We have revised " + str(len(fixes)) + " other manuscripts with proof repairs, corrected statements, clearer hypotheses and dependencies. The changes include:", ""])
    for title, phrase in fixes:
        lines.append("- " + markdown_math(title) + ": " + phrase + ".")

    # downstream updates and formalizations
    lines.extend(["", "Also, as a consequence of these fixes we updated " + str(updated_count) + " additional manuscripts to cite the revised editions of companion papers. These changes update references and version dates.", ""])
    lines.extend(["**Additional Formalizations**", "", "We have added an additional 0 formalizations and 0 other additions covering supporting results. This brings the total percentage of main results formalized to 0 / " + str(manuscript_count) + " = 0%."])
    return to_text(lines)


# lean directory with nothing in it but its readme
def lean_files(manuscript_count):

    return {"lean/README.md": to_text(["# Lean library", "", "Unlike OpenAI, we have only uploaded Lean proofs that have undergone rigorous review by the community."])}


# overview of every manuscript, with no end of document
def overview_tex(items):

    lines = list(XELATEX_LINES)
    lines.extend([r"\title{Overview of the physics manuscript collection}", r"\author{" + AUTHOR + "}", r"\date{October 9, 2026}", r"\begin{document}", r"\maketitle", ""])
    for item in items:
        summary = item["abstract_markdown"].replace("$`", "$").replace("`$", "$")
        lines.append(r"\subsection*{" + number_text(item["number"]) + ". " + item["title"] + "}")
        lines.extend(textwrap.wrap(summary, width=72, break_on_hyphens=False, break_long_words=False))
        lines.append("")

    return to_text(lines)


# reasoning summary that never reaches the end of the document
def trace_tex(title, paragraphs):

    lines = list(XELATEX_LINES)
    lines.extend([r"\title{Reasoning summary: " + title + "}", r"\author{" + AUTHOR + "}", r"\begin{document}", r"\maketitle", ""])
    for paragraph in paragraphs:
        lines.extend(textwrap.wrap(paragraph, width=72, break_on_hyphens=False, break_long_words=False))
        lines.append("")

    return to_text(lines)
