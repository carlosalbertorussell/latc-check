"""Figures 1-3 for Paper C, built only from the committed result files.

Inputs: paperC/results/<ID>/{runs.csv,summary.md,manifest.json}, copied byte for byte
from the run branches listed in paperC/figures/SOURCES.csv (their git blob hashes are
checked here). Outputs, all in paperC/figures/:

  fig1_official_coverage.{pdf,png}   fig1_data.csv
  fig2_coverage_vs_n.{pdf,png}       fig2_data.csv
  fig3_c2_generated.{pdf,png}        fig3_data.csv
  fig_checks.csv                     every cross-check, with its result

Every plotted number is checked against the values the paper prints (Tables 2 and 3
and the text) and against each table's harness summary.md. Any failed check is printed
and the script exits with status 1 after writing all outputs; the data are never
adjusted to fit the paper.

Run from the repository root with the pinned environment of requirements.lock:
    python paperC/figures/make_figures.py
"""

import csv
import hashlib
import math
import re
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "paperC" / "results"
OUT = ROOT / "paperC" / "figures"

TABLES = ["FR-PF", "FR-AF-1", "FR-AF-2", "FR-AF-3",
          "FR-APL-1", "FR-APL-2", "FR-APL-3", "FR-APL-4", "FR-APL-5",
          "US-121-1", "US-121-2", "NZ-SLP", "NZ-AS", "NZ-SPS"]
CONTROL = "CTRL-NUR"
NO_OFFICIAL = {"FR-APL-4", "FR-APL-5"}
SIZES = [10, 20, 50, 100, 200, 500, 1000]
SOURCES = ["UNIFORM", "ZIPF"]

# Values printed in the paper. Table 2: C1 valid coverage and C2 spurious share,
# OFFICIAL examples, as written in the table.
TABLE2 = {
    "FR-PF": ("0.6%", "66.7%"),
    "FR-AF-1": ("0.01%", "25.0%"),
    "FR-AF-2": ("0.9%", "0%"),
    "FR-AF-3": ("<0.01%", "0%"),
    "FR-APL-1": ("0.6%", "35.3%"),
    "FR-APL-2": ("<0.01%", "2.9%"),
    "FR-APL-3": ("0.03%", "0%"),
    "US-121-1": ("50%", "80.0%"),
    "US-121-2": ("1.0%", "84.4%"),
    "NZ-SLP": ("100%", "0%"),
    "NZ-AS": ("<0.01%", "43.8%"),
    "NZ-SPS": ("0.06%", "18.8%"),
}
# Table 3: C1 mean valid coverage at n = 10, uniform / Zipf.
TABLE3 = {
    "FR-PF": ("53.8", "45.7"),
    "FR-AF-1": ("24.4", "20.7"),
    "FR-AF-2": ("33.7", "30.1"),
    "FR-AF-3": ("44.3", "47.6"),
    "NZ-SLP": ("94.2", "90.8"),
}
# Text: C1 mean valid coverage at n = 10 as a closed range in percent (both sources),
# and NZ-SLP complete seeds at n = 10.
TEXT_RANGES = {"NZ-AS": (73.5, 74.5), "NZ-SPS": (49.5, 58.5)}
TEXT_COMPLETE = {("NZ-SLP", "UNIFORM"): 23, ("NZ-SLP", "ZIPF"): 20}

# Okabe-Ito colours; each pair also differs in line style, marker and grey level.
BLUE, ORANGE, VERMILION, SKY, YELLOW = "#0072B2", "#E69F00", "#D55E00", "#56B4E9", "#F0E442"
GREY = "#555555"
CM = 1 / 2.54

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 7,
    "axes.titlesize": 7,
    "axes.labelsize": 7,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.minor.width": 0.4,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.dpi": 300,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

CHECKS = []


def check(name, ok, observed, expected):
    CHECKS.append({"check": name, "observed": observed, "expected": expected,
                   "result": "pass" if ok else "FAIL"})


def git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def load_runs(table):
    with open(RESULTS / table / "runs.csv", newline="") as f:
        return list(csv.DictReader(f))


def one(runs, source, condition):
    rows = [r for r in runs if r["source"] == source and r["condition"] == condition]
    assert len(rows) == 1, (source, condition, len(rows))
    return rows[0]


def percentile(xs, p):
    """Hyndman and Fan type 7, as PROTOCOL.md section 8 defines it."""
    xs = sorted(xs)
    h = (len(xs) - 1) * p
    lo = math.floor(h)
    hi = xs[lo + 1] if lo + 1 < len(xs) else xs[lo]
    return xs[lo] + (h - lo) * (hi - xs[lo])


def summary_official(table):
    """OFFICIAL rows of summary.md: condition -> {column: string}."""
    text = (RESULTS / table / "summary.md").read_text()
    lines = text.splitlines()
    i = next(k for k, ln in enumerate(lines) if ln.startswith("| source | condition |"))
    header = [c.strip() for c in lines[i].strip("|").split("|")]
    out = {}
    for ln in lines[i + 2:]:
        if not ln.startswith("|"):
            break
        cells = dict(zip(header, (c.strip() for c in ln.strip("|").split("|"))))
        if cells["source"] == "OFFICIAL":
            out[cells["condition"]] = cells
    return out


def summary_seeded(table, metric):
    """(condition, source, n) -> (mean, median, p2.5, p97.5) as strings from summary.md."""
    text = (RESULTS / table / "summary.md").read_text()
    block = text.split(f"### {metric}\n", 1)[1].split("\n### ", 1)[0]
    out = {}
    for ln in block.splitlines():
        m = re.match(r"\| (C\d) \| (UNIFORM|ZIPF) \| (\d+) \| \d+ \| (\S+) \| (\S+) \| (\S+) \| (\S+) \|", ln)
        if m:
            out[(m[1], m[2], int(m[3]))] = m.group(4, 5, 6, 7)
    return out


def matches_printed(value_pct, printed):
    """Does a percentage agree with the paper's printed string at its own precision?"""
    s = printed.rstrip("%")
    if s.startswith("<"):
        return 0 < value_pct < float(s[1:])
    if float(s) == 0:
        return value_pct == 0
    decimals = len(s.split(".")[1]) if "." in s else 0
    return abs(value_pct - float(s)) <= 0.5 * 10 ** -decimals + 1e-12


def fmt_pct(v):
    """Two significant figures, no exponent."""
    if v == 0:
        return "0%"
    if v >= 10:
        return f"{v:.0f}%"
    digits = max(0, 1 - math.floor(math.log10(v)))
    return f"{v:.{digits}f}%"


def save(fig, stem):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{stem}.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.02,
                    metadata={"CreationDate": None} if ext == "pdf" else None)
    plt.close(fig)


def write_csv(name, rows):
    with open(OUT / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------- inputs

def verify_sources():
    with open(OUT / "SOURCES.csv", newline="") as f:
        for r in csv.DictReader(f):
            got = git_blob(ROOT / r["file"])
            check(f"source blob {r['file']} = {r['branch']}@{r['commit']}",
                  got == r["git_blob"], got, r["git_blob"])


# ---------------------------------------------------------------- figure 1

def figure1(runs):
    rows = []
    for t in TABLES:
        official = [r for r in runs[t] if r["source"] == "OFFICIAL"]
        if t in NO_OFFICIAL:
            check(f"{t} has no OFFICIAL runs", not official, len(official), 0)
            continue
        c1 = one(runs[t], "OFFICIAL", "C1")
        v = float(c1["valid_coverage"])
        size_v = int(one(runs[t], "FULL", "C1")["size"])
        cov = int(c1["covered_valid"])
        check(f"fig1 {t} covered_valid/|V| = valid_coverage", abs(cov / size_v - v) < 1e-12,
              f"{cov}/{size_v}", c1["valid_coverage"])
        summ = summary_official(t)["C1"]["valid_coverage"]
        check(f"fig1 {t} C1 OFFICIAL valid_coverage vs summary.md", f"{v:.4f}" == summ, f"{v:.4f}", summ)
        check(f"fig1 {t} C1 OFFICIAL valid_coverage vs Table 2", matches_printed(100 * v, TABLE2[t][0]),
              f"{100 * v:.6g}%", TABLE2[t][0])
        rows.append({
            "table": t, "n_official_rows": int(c1["n_examples"]),
            "valid_space": size_v, "covered_valid": cov,
            "valid_coverage_pct": repr(100 * v),
            "latc_reported_missing": int(c1["reported_missing"]),
            "latc_generated_rows": int(c1["workload"]),
            "latc_reported_no_missing_case": int(int(c1["reported_missing"]) <= 0
                                                 and int(c1["workload"]) == 0),
            "table2_printed": TABLE2[t][0],
        })
    rows.sort(key=lambda r: (float(r["valid_coverage_pct"]), r["table"]))
    write_csv("fig1_data.csv", rows)

    floor, top = 1e-3, 100.0
    fig, ax = plt.subplots(figsize=(8.5 * CM, 7.2 * CM))
    for i, r in enumerate(rows):
        v = float(r["valid_coverage_pct"])
        below = v < floor
        x = floor if below else v
        none_reported = r["latc_reported_no_missing_case"] == 1
        ax.plot([floor, x], [i, i], color="#BBBBBB", lw=0.6, zorder=1)
        ax.plot(x, i, marker="<" if below else "o", ms=4.6, mec=BLUE, mew=1.0,
                mfc="white" if none_reported else BLUE, ls="none", zorder=3)
        label = f"{fmt_pct(v)}  ({r['covered_valid']:,}/{r['valid_space']:,})"
        if v > 5:
            ax.annotate(label, (x, i), xytext=(-5, 0), textcoords="offset points",
                        ha="right", va="center", fontsize=6)
        else:
            ax.annotate(label, (x, i), xytext=(5, 0), textcoords="offset points",
                        ha="left", va="center", fontsize=6)
    ax.axvline(floor, color=GREY, lw=0.6, ls=(0, (2, 2)), zorder=0)
    ax.set_xscale("log")
    ax.set_xlim(floor / 1.6, top * 1.6)
    ax.set_xticks([1e-3, 1e-2, 1e-1, 1, 10, 100])
    ax.set_xticklabels(["≤0.001%", "0.01%", "0.1%", "1%", "10%", "100%"])
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r["table"] for r in rows])
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", which="major", color="#E5E5E5", lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("C1 valid coverage with the official examples (log scale)")
    handles = [
        Line2D([], [], marker="o", ls="none", mfc=BLUE, mec=BLUE, ms=4.6, label="LATC reported missing cases"),
        Line2D([], [], marker="o", ls="none", mfc="white", mec=BLUE, mew=1.0, ms=4.6,
               label="LATC reported no missing case"),
        Line2D([], [], marker="<", ls="none", mfc="none", mec=GREY, mew=1.0, ms=4.6,
               label="below 0.001%, drawn at the floor"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.42, -0.2), ncol=1,
              frameon=False, handletextpad=0.3, borderaxespad=0)
    save(fig, "fig1_official_coverage")
    return rows


# ---------------------------------------------------------------- figure 2

def figure2(runs):
    panels = TABLES + [CONTROL]
    rows = []
    stats = {}
    for t in panels:
        summ = summary_seeded(t, "valid_coverage")
        for s in SOURCES:
            for n in SIZES:
                rr = [r for r in runs[t] if r["source"] == s and r["condition"] == "C1" and r["size"] == str(n)]
                assert sorted(int(r["seed"]) for r in rr) == list(range(30)), (t, s, n)
                xs = [float(r["valid_coverage"]) for r in rr]
                mean, lo, hi = statistics.fmean(xs), percentile(xs, 0.025), percentile(xs, 0.975)
                k = sum(int(r["complete"]) for r in rr)
                sm = summ[("C1", s, n)]
                ok = (f"{mean:.4f}", f"{lo:.4f}", f"{hi:.4f}") == (sm[0], sm[2], sm[3])
                check(f"fig2 {t} {s} n={n} C1 mean/p2.5/p97.5 vs summary.md", ok,
                      f"{mean:.4f}/{lo:.4f}/{hi:.4f}", f"{sm[0]}/{sm[2]}/{sm[3]}")
                stats[(t, s, n)] = (mean, lo, hi, k)
                rows.append({"table": t, "source": s, "n": n, "seeds": len(xs),
                             "mean_valid_coverage_pct": repr(100 * mean),
                             "p2_5_pct": repr(100 * lo), "p97_5_pct": repr(100 * hi),
                             "complete_runs": k})
        if t in TABLE3:
            for s, printed in zip(SOURCES, TABLE3[t]):
                m = 100 * stats[(t, s, 10)][0]
                check(f"fig2 {t} {s} n=10 C1 mean vs Table 3", matches_printed(m, printed), f"{m:.4f}", printed)
        if t in TEXT_RANGES:
            a, b = TEXT_RANGES[t]
            for s in SOURCES:
                m = 100 * stats[(t, s, 10)][0]
                check(f"fig2 {t} {s} n=10 C1 mean vs text", a <= m <= b, f"{m:.4f}", f"[{a}, {b}]")
    for (t, s), k in TEXT_COMPLETE.items():
        got = stats[(t, s, 10)][3]
        check(f"fig2 {t} {s} n=10 C1 complete seeds vs text", got == k, f"{got}/30", f"{k}/30")
    write_csv("fig2_data.csv", rows)

    style = {"UNIFORM": dict(color=BLUE, ls="-", marker="o", label="Uniform"),
             "ZIPF": dict(color=VERMILION, ls=(0, (3, 1.5)), marker="s", label="Zipf")}
    hatch = {"UNIFORM": None, "ZIPF": "/////"}
    ncol = 4
    nrow = math.ceil((len(panels) + 1) / ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(17.8 * CM, 16.0 * CM), sharex=True, sharey=True)
    axes = axes.ravel()
    for ax, t in zip(axes, panels):
        for s in SOURCES:
            mean = [100 * stats[(t, s, n)][0] for n in SIZES]
            lo = [100 * stats[(t, s, n)][1] for n in SIZES]
            hi = [100 * stats[(t, s, n)][2] for n in SIZES]
            st = style[s]
            ax.fill_between(SIZES, lo, hi, color=st["color"], alpha=0.16, lw=0)
            if hatch[s]:
                ax.fill_between(SIZES, lo, hi, facecolor="none", edgecolor=st["color"], alpha=0.45,
                                hatch=hatch[s], lw=0)
            ax.plot(SIZES, mean, color=st["color"], ls=st["ls"], lw=1.0, marker=st["marker"], ms=2.4,
                    mew=0, zorder=3)
        title = "Nursery (control)" if t == CONTROL else t
        ax.set_title(title, loc="left", pad=2, fontweight="bold" if t == CONTROL else "normal")
        ax.text(0.98, 0.04, complete_note(stats, t), transform=ax.transAxes, ha="right", va="bottom",
                fontsize=5.4, color="#333333", linespacing=1.15)
        ax.set_xscale("log")
        ax.set_xlim(8.5, 1180)
        ax.set_ylim(0, 103)
        ax.set_xticks(SIZES)
        ax.set_xticklabels(["10", "", "50", "", "", "500", ""])
        ax.minorticks_off()
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.grid(color="#E5E5E5", lw=0.5)
        ax.set_axisbelow(True)
    for ax in axes[len(panels):]:
        ax.axis("off")
    leg_ax = axes[len(panels)]
    handles = [
        Line2D([], [], color=BLUE, ls="-", marker="o", ms=3, lw=1.0, label="Uniform, mean of 30 seeds"),
        Patch(facecolor=BLUE, alpha=0.16, lw=0, label="Uniform, 2.5th–97.5th percentile"),
        Line2D([], [], color=VERMILION, ls=(0, (3, 1.5)), marker="s", ms=3, lw=1.0, label="Zipf, mean of 30 seeds"),
        Patch(facecolor="#F7D9CC", edgecolor=VERMILION, hatch="/////", lw=0, label="Zipf, 2.5th–97.5th percentile"),
    ]
    leg_ax.legend(handles=handles, loc="upper left", frameon=False, borderaxespad=0, handlelength=2.4)
    leg_ax.text(0, 0.38, "Panel note: complete runs (all valid\ncases covered, no spurious row)\n"
                "as uniform/Zipf seeds out of 30.", transform=leg_ax.transAxes, fontsize=6, va="top")
    for ax in axes[(nrow - 1) * ncol - 1:]:
        ax.tick_params(labelbottom=True)
    fig.supxlabel("Number of random examples n (log scale)", fontsize=7, y=0.005)
    fig.supylabel("C1 valid coverage (%)", fontsize=7, x=0.005)
    fig.tight_layout(pad=0.4, h_pad=0.6, w_pad=0.4)
    save(fig, "fig2_coverage_vs_n")
    return rows


def complete_note(stats, t):
    counts = [(n, stats[(t, "UNIFORM", n)][3], stats[(t, "ZIPF", n)][3]) for n in SIZES]
    if all(u == 0 and z == 0 for _, u, z in counts):
        return "no complete run"
    parts = []
    for i, (n, u, z) in enumerate(counts):
        if u == 30 and z == 30 and all(uu == 30 and zz == 30 for _, uu, zz in counts[i:]):
            parts.append(f"n ≥ {n}: all")
            break
        if u or z:
            parts.append(f"n = {n}: {u}/{z}")
    return "complete runs\n" + "\n".join(parts)


# ---------------------------------------------------------------- figure 3

def figure3(runs):
    rows = []
    for t in TABLES:
        if t in NO_OFFICIAL:
            continue
        c2 = one(runs[t], "OFFICIAL", "C2")
        g = int(c2["workload"])
        exc, rej = int(c2["spurious_excluded"]), int(c2["spurious_rejected"])
        valid = g - exc - rej
        share = (exc + rej) / g if g else 0.0
        check(f"fig3 {t} C2 spurious recomputed vs runs.csv", abs(share - float(c2["spurious_share"])) < 1e-12
              and exc + rej == int(c2["spurious"]), repr(share), c2["spurious_share"])
        summ = summary_official(t)["C2"]
        check(f"fig3 {t} C2 OFFICIAL spurious_share vs summary.md", f"{share:.4f}" == summ["spurious_share"],
              f"{share:.4f}", summ["spurious_share"])
        check(f"fig3 {t} C2 OFFICIAL spurious_share vs Table 2", matches_printed(100 * share, TABLE2[t][1]),
              f"{100 * share:.6g}%", TABLE2[t][1])
        rows.append({"table": t, "generated_rows": g, "valid": valid, "excluded": exc, "rejected": rej,
                     "valid_pct": repr(100 * valid / g), "excluded_pct": repr(100 * exc / g),
                     "rejected_pct": repr(100 * rej / g), "spurious_share_pct": repr(100 * share),
                     "table2_printed": TABLE2[t][1]})
    rows.sort(key=lambda r: (float(r["spurious_share_pct"]), r["table"]))
    write_csv("fig3_data.csv", rows)

    parts = [("valid", "Valid", BLUE, None), ("excluded", "EXCLUDED", ORANGE, None),
             ("rejected", "REJECTED", YELLOW, "////")]
    fig, ax = plt.subplots(figsize=(17.8 * CM, 7.0 * CM))
    for i, r in enumerate(rows):
        left = 0.0
        for key, _, colour, h in parts:
            w = float(r[f"{key}_pct"])
            if w > 0:
                ax.barh(i, w, left=left, height=0.68, color=colour, edgecolor="black", lw=0.4, hatch=h)
            left += w
        ax.text(109.5, i, f"{r['generated_rows']:,}", va="center", ha="right", fontsize=6.5)
        ax.text(119.5, i, f"{float(r['spurious_share_pct']):.1f}%", va="center", ha="right", fontsize=6.5)
    ax.text(109.5, len(rows) - 0.45, "generated\nrows", va="bottom", ha="right", fontsize=6.5)
    ax.text(119.5, len(rows) - 0.45, "spurious\nshare", va="bottom", ha="right", fontsize=6.5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r["table"] for r in rows])
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlim(0, 120)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_bounds(0, 100)
    ax.set_xlabel("Share of the rows C2 generates from the official examples")
    handles = [Patch(facecolor=c, edgecolor="black", lw=0.4, hatch=h, label=lab) for _, lab, c, h in parts]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.01), ncol=3, frameon=False,
              borderaxespad=0, handlelength=1.6)
    save(fig, "fig3_c2_generated")
    return rows


def main():
    verify_sources()
    runs = {t: load_runs(t) for t in TABLES + [CONTROL]}
    figure1(runs)
    figure2(runs)
    figure3(runs)
    write_csv("fig_checks.csv", CHECKS)
    failed = [c for c in CHECKS if c["result"] != "pass"]
    print(f"checks passed: {len(CHECKS) - len(failed)}/{len(CHECKS)}")
    for c in failed:
        print(f"MISMATCH: {c['check']}: data {c['observed']}, paper {c['expected']}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
