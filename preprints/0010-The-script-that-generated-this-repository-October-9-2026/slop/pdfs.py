import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# byte sequences a repair tool could latch onto
PDF_KEYWORDS = [b"obj", b"trailer", b"xref", b"endstream", b"%%EOF", b"Catalog"]

# fixed build date so every compile is byte-identical
SOURCE_DATE = "1791504000"

# built-in style sheets, sizes and legend corners drawn per figure
STYLES = ["default", "classic", "bmh", "ggplot", "seaborn-v0_8-whitegrid", "seaborn-v0_8-darkgrid", "seaborn-v0_8-ticks", "seaborn-v0_8-colorblind", "tableau-colorblind10", "fast"]
FIGURE_SIZES = [(6.0, 4.5), (5.0, 5.0), (7.0, 4.0), (6.0, 6.0), (6.5, 4.0)]
LEGEND_LOCATIONS = ["upper right", "lower right", "center right", "lower center"]

# parameter scans with plain-text legend labels
SCAN_SETS = [("R", ["0.4", "0.8", "1.2"]), ("beta", ["0.5", "1", "2"]), ("zcut", ["0.05", "0.1", "0.2"]), ("N", ["2", "3", "4"])]

# extra method names for bar and box charts
EXTRA_METHODS = ["BDT", "DNN", "PFN", "LundNet", "ParT"]

# colormaps for the heatmap
COLORMAPS = ["viridis", "magma", "cividis", "Blues", "inferno", "plasma"]


# header, an open stream and random bytes with nothing to repair
def corrupted_pdf(rng, minimum_bytes, maximum_bytes):

    size = rng.randint(minimum_bytes, maximum_bytes)
    header = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Length " + str(3 * size).encode() + b" /Filter /FlateDecode >>\nstream\n"

    # redraw until no keyword appears in the noise
    body = rng.randbytes(size)
    while any(keyword in body for keyword in PDF_KEYWORDS):
        body = rng.randbytes(size)

    return header + body


# one meaningless curve on the unit interval
def curve(shape, parameters):

    first, second = parameters
    x = np.linspace(0.001, 1.0, 400)

    # four shapes that look like physics
    if shape == "sudakov":
        y = np.exp(-first * np.log(x) ** 2 / (4.0 * second))
    elif shape == "peak":
        y = x ** first * np.exp(-5.0 * second * x)
        y = y / y.max()
    elif shape == "roc":
        y = 1.0 - (1.0 - x) ** (first + 1.0)
    else:
        y = 1.0 + 0.2 * np.sin(5.0 * first * x) * np.exp(-second * x)

    return x, y


# samples on the unit interval that look like an event-shape distribution
def samples(generator, spec, count):

    first, second = spec["parameters"]
    values = generator.gamma(1.0 + first, 0.08 * second, count)
    return values[values < 1.0]


# normalized histogram with poisson errors
def normalized_histogram(points, bins):

    counts, edges = np.histogram(points, bins=bins, range=(0.0, 1.0))
    widths = np.diff(edges)
    norm = counts.sum() * widths
    return (edges[:-1] + edges[1:]) / 2, counts / norm, np.sqrt(counts) / norm, widths


# axis labels from the spec
def label_axes(ax, spec):

    ax.set_xlabel(spec["x_label"])
    ax.set_ylabel(spec["y_label"])


# one smooth curve
def draw_curve(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    x, y = curve(spec["shape"], spec["parameters"])
    ax.plot(x, y, label=spec["legend"])
    label_axes(ax, spec)
    return fig, ax


# histogram as points with error bars
def draw_histogram(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    centers, values, errors, widths = normalized_histogram(samples(generator, spec, 4000), 25)
    ax.errorbar(centers, values, yerr=errors, xerr=widths / 2, fmt="o", label=spec["legend"])
    label_axes(ax, spec)
    return fig, ax


# filled step histogram with its outline
def draw_filled(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    points = samples(generator, spec, 6000)
    ax.hist(points, bins=30, range=(0.0, 1.0), density=True, histtype="stepfilled", alpha=0.35, color="C1")
    ax.hist(points, bins=30, range=(0.0, 1.0), density=True, histtype="step", color="C1", label=spec["legend"])
    label_axes(ax, spec)
    return fig, ax


# stacked components of one distribution
def draw_stack(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    components = [np.clip(generator.normal(0.2 + 0.25 * index, 0.08 + 0.04 * index, 3000 - 800 * index), 0.0, 1.0) for index in range(3)]
    ax.hist(components, bins=30, range=(0.0, 1.0), stacked=True, histtype="stepfilled", alpha=0.7, label=spec["legends"])
    label_axes(ax, spec)
    return fig, ax


# central curve with an uncertainty band
def draw_band(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    x, y = curve(spec["shape"], spec["parameters"])
    spread = 0.08 * np.abs(y) * (1.0 + 2.0 * x)
    ax.fill_between(x, y - spread, y + spread, alpha=0.3, color="C2", label="Uncertainty")
    ax.plot(x, y, color="C2", label=spec["legend"])
    label_axes(ax, spec)
    return fig, ax


# the same shape for three parameter values
def draw_scan(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    name, values = SCAN_SETS[generator.integers(len(SCAN_SETS))]
    first, second = spec["parameters"]
    for index, value in enumerate(values):
        x, y = curve(spec["shape"], [first * (1.0 + 0.4 * index), second])
        ax.plot(x, y, label=name + " = " + value)
    label_axes(ax, spec)
    return fig, ax


# background rejection against signal efficiency for three taggers
def draw_taggers(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    efficiency = np.linspace(0.02, 1.0, 300)
    for index, name in enumerate(spec["legends"]):
        ax.plot(efficiency, efficiency ** -(1.0 + spec["parameters"][0] * (0.5 + 0.4 * index)), label=name)
    ax.set_yscale("log")
    ax.set_xlabel("Signal Efficiency")
    ax.set_ylabel("Background Rejection")
    return fig, ax


# Lund-plane style density with a colorbar
def draw_heatmap(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    x, y = np.meshgrid(np.linspace(0.0, 6.0, 60), np.linspace(-3.0, 5.0, 60))
    first, second = spec["parameters"]
    density = np.exp(-((x - 1.5 * first) ** 2 / 4.0 + (y - second) ** 2 / 3.0)) + 0.05 * generator.random(x.shape)
    mesh = ax.pcolormesh(x, y, density, shading="auto", cmap=COLORMAPS[generator.integers(len(COLORMAPS))])
    fig.colorbar(mesh, ax=ax, label="Emission Density")
    ax.set_xlabel(r"$\ln(1/\Delta)$")
    ax.set_ylabel(r"$\ln(k_T/\mathrm{GeV})$")
    return fig, ax


# histogram over a pull panel
def draw_ratio(spec, generator, size):

    fig, (top, bottom) = plt.subplots(2, 1, figsize=size, sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    centers, values, errors, widths = normalized_histogram(samples(generator, spec, 5000), 20)
    top.errorbar(centers, values, yerr=errors, xerr=widths / 2, fmt="o", label=spec["legend"])
    top.set_ylabel(spec["y_label"])

    # residuals against a smoothed copy of the same histogram
    smooth = np.convolve(values, np.ones(3) / 3.0, mode="same")
    pulls = np.divide(values - smooth, errors, out=np.zeros_like(values), where=errors > 0)
    bottom.errorbar(centers, pulls, yerr=np.ones_like(pulls), fmt="o", color="black")
    bottom.axhline(0.0, color="gray")
    bottom.set_ylabel("Pull")
    bottom.set_xlabel(spec["x_label"])
    return fig, top


# one metric per method
def draw_bars(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    methods = list(spec["legends"]) + EXTRA_METHODS[:2]
    values = 0.82 + 0.15 * generator.random(len(methods))
    ax.bar(methods, values, color=["C" + str(index) for index in range(len(methods))])
    ax.set_ylim(0.75, 1.0)
    ax.set_ylabel("AUC")
    return fig, ax


# two panels with different observables
def draw_panels(spec, generator, size):

    fig, (left, right) = plt.subplots(1, 2, figsize=(size[0] * 1.5, size[1] * 0.8))
    x, y = curve(spec["shape"], spec["parameters"])
    left.plot(x, y, label=spec["legend"])
    label_axes(left, spec)

    # second panel holds a histogram of a different quantity
    right.hist(samples(generator, spec, 4000), bins=25, range=(0.0, 1.0), density=True, histtype="step", color="C3")
    right.set_xlabel("$z$")
    right.set_ylabel("Density")
    return fig, left


# measured points with error bars
def draw_scatter(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    x, y = curve(spec["shape"], spec["parameters"])
    picks = np.linspace(20, 380, 12).astype(int)
    errors = 0.03 + 0.05 * generator.random(len(picks))
    ax.errorbar(x[picks], y[picks] + errors * generator.normal(size=len(picks)), yerr=errors, fmt="s", label=spec["legend"])
    label_axes(ax, spec)
    return fig, ax


# likelihood contours around a best fit
def draw_contour(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    center_x = 0.112 + 0.012 * generator.random()
    center_y = 0.3 + 0.5 * generator.random()
    x, y = np.meshgrid(np.linspace(0.105, 0.13, 200), np.linspace(0.0, 1.2, 200))
    correlation = 0.8 * generator.random() - 0.4
    chi_squared = ((x - center_x) / 0.004) ** 2 + ((y - center_y) / 0.15) ** 2 + 2.0 * correlation * (x - center_x) * (y - center_y) / (0.004 * 0.15)
    ax.contour(x, y, chi_squared, levels=[2.3, 6.18, 11.8])
    ax.plot([center_x], [center_y], marker="*", linestyle="none", label="Best fit")
    ax.set_xlabel(r"$\alpha_s(m_Z)$")
    ax.set_ylabel(r"$\Omega_1$ [GeV]")
    return fig, ax


# spread of a metric per method
def draw_boxes(spec, generator, size):

    fig, ax = plt.subplots(figsize=size)
    methods = list(spec["legends"]) + EXTRA_METHODS[2:4]
    data = [generator.normal(0.85 + 0.03 * index, 0.02 + 0.01 * generator.random(), 200) for index in range(len(methods))]
    ax.boxplot(data, tick_labels=methods)
    ax.set_ylabel(spec["y_label"])
    return fig, ax


# every figure kind the tex builder can ask for
FIGURE_KINDS = {"curve": draw_curve, "histogram": draw_histogram, "filled": draw_filled, "stack": draw_stack, "band": draw_band, "scan": draw_scan, "taggers": draw_taggers, "heatmap": draw_heatmap, "ratio": draw_ratio, "bars": draw_bars, "panels": draw_panels, "scatter": draw_scatter, "contour": draw_contour, "boxes": draw_boxes}


# real figure pdf from a spec
def render_figure(spec, path):

    generator = np.random.default_rng(spec["seed"])
    style = STYLES[generator.integers(len(STYLES))]
    size = FIGURE_SIZES[generator.integers(len(FIGURE_SIZES))]
    with plt.style.context(style):
        fig, ax = FIGURE_KINDS[spec["kind"]](spec, generator, size)

        # stamp block in the top-left corner of the main panel
        ax.text(0.05, 0.94, spec["stamp_title"], transform=ax.transAxes, fontweight="bold", va="top")
        ax.text(0.05, 0.86, spec["stamp_detail"], transform=ax.transAxes, va="top")

        # legend only when something is labeled
        if ax.get_legend_handles_labels()[1]:
            ax.legend(loc=LEGEND_LOCATIONS[generator.integers(len(LEGEND_LOCATIONS))])

        # no creation date so reruns are identical
        fig.tight_layout()
        fig.savefig(path, metadata={"CreationDate": None})

    plt.close(fig)


# one tex tool run inside the scratch build
def run_tool(command, directory, environment):

    return subprocess.run(command, cwd=directory, env=environment, stdin=subprocess.DEVNULL, capture_output=True, timeout=180)


# pdflatex, bibtex and two more passes in a scratch copy
def compile_manuscript(build_directory, main_name, output_pdf):

    stem = Path(main_name).stem
    environment = dict(os.environ, SOURCE_DATE_EPOCH=SOURCE_DATE, FORCE_SOURCE_DATE="1")
    with tempfile.TemporaryDirectory() as scratch:

        # copy so no aux files land in the repo
        work = Path(scratch) / "build"
        shutil.copytree(build_directory, work)
        latex = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", main_name]
        run_tool(latex, work, environment)
        run_tool(["bibtex", stem], work, environment)
        run_tool(latex, work, environment)
        final = run_tool(latex, work, environment)

        # a failed final pass is a bug in the generator
        pdf_path = work / (stem + ".pdf")
        if final.returncode != 0 or not pdf_path.exists():
            log_lines = (work / (stem + ".log")).read_text(errors="replace").splitlines()
            raise RuntimeError(str(build_directory) + "\n" + "\n".join(log_lines[-40:]))

        shutil.copyfile(pdf_path, output_pdf)


# figures then compile, for the worker pool
def build_working(job):

    figure_directory = Path(job["build_directory"]) / "figures"
    figure_directory.mkdir(parents=True, exist_ok=True)
    for spec in job["figures"]:
        render_figure(spec, figure_directory / (spec["name"] + ".pdf"))

    compile_manuscript(job["build_directory"], job["main_name"], job["output_pdf"])
    return job["output_pdf"]
