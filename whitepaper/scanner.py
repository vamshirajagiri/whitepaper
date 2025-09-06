# whitepaper/scanner.py
from pathlib import Path
import pandas as pd
import numpy as np
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich import box
from .utils import console

def _read_table(path: Path):
    """Read CSV or Excel into a DataFrame with sensible defaults."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)
    return pd.read_excel(path, engine="openpyxl")

def analyze_file(path: Path) -> dict:
    """Read & analyze a single file; returns analysis dict or raises."""
    df = _read_table(path)
    rows, cols = df.shape

    missing_per_col = df.isna().sum()
    total_missing = int(missing_per_col.sum())

    duplicates = int(df.duplicated().sum())

    # Numeric outlier counts (IQR)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    outliers_iqr = {}
    for col in numeric_cols:
        s = df[col].dropna().astype(float)
        if s.empty:
            outliers_iqr[col] = 0
            continue
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0 or np.isnan(iqr):
            outliers_iqr[col] = 0
        else:
            mask = (s < (q1 - 1.5 * iqr)) | (s > (q3 + 1.5 * iqr))
            outliers_iqr[col] = int(mask.sum())

    total_outliers = sum(outliers_iqr.values())

    # Detect columns with mixed inferred types (helpful flag)
    mixed_cols = []
    for col in df.columns:
        nonnull = df[col].dropna()
        if nonnull.empty:
            continue
        kind = pd.api.types.infer_dtype(nonnull, skipna=True)
        if "mixed" in kind:
            mixed_cols.append(col)

    # Simple quality score (0.5 - 10) — tunable
    quality = 10.0
    if rows > 0 and cols > 0:
        missing_ratio = total_missing / (rows * cols)
        dup_ratio = duplicates / max(1, rows)
        outlier_ratio = total_outliers / max(1, rows)

        quality -= missing_ratio * 8   # missing heavy penalty
        quality -= dup_ratio * 3
        quality -= outlier_ratio * 2

    quality = max(0.5, min(10.0, round(quality, 1)))

    top_missing = (missing_per_col[missing_per_col > 0].sort_values(ascending=False).head(8).to_dict())

    return {
        "file": path.name,
        "size_bytes": path.stat().st_size,
        "rows": int(rows),
        "cols": int(cols),
        "total_missing": int(total_missing),
        "missing_per_col": {k: int(v) for k, v in top_missing.items()},
        "duplicates": int(duplicates),
        "numeric_cols_count": len(numeric_cols),
        "outliers_iqr": outliers_iqr,
        "total_outliers": int(total_outliers),
        "mixed_type_cols": mixed_cols,
        "quality": float(quality),
    }

def pretty_print(analysis: dict):
    """Pretty print analysis dict using rich panels/tables."""
    file = analysis["file"]
    size_mb = analysis["size_bytes"] / (1024 * 1024)
    header = f"📊 {file} — {size_mb:.2f}MB | Rows: {analysis['rows']} | Columns: {analysis['cols']}"

    body = (
        f"🕳️ Missing values: {analysis['total_missing']}\n"
        f"🗑️ Duplicates: {analysis['duplicates']}\n"
        f"⚠️ Outliers (IQR): {analysis['total_outliers']}\n"
        f"⭐ Quality: {analysis['quality']}/10\n"
    )
    console.print(Panel(body, title=header, subtitle="Scan result", expand=False, box=box.ROUNDED))

    if analysis["missing_per_col"]:
        t = Table(title="Top columns by missing values", show_header=True, header_style="bold magenta")
        t.add_column("Column", style="dim")
        t.add_column("Missing", justify="right")
        for col, miss in analysis["missing_per_col"].items():
            t.add_row(str(col), str(miss))
        console.print(t)

    if analysis["mixed_type_cols"]:
        console.print(Panel("\n".join(analysis["mixed_type_cols"]), title="Mixed-type columns detected", style="yellow"))

    # show numeric outliers summary
    out_map = {k: v for k, v in analysis["outliers_iqr"].items() if v > 0}
    if out_map:
        t2 = Table(title="Numeric outliers (IQR) — column: count", show_header=True)
        t2.add_column("Column")
        t2.add_column("Outliers", justify="right")
        sorted_out = sorted(out_map.items(), key=lambda x: x[1], reverse=True)
        for col, ct in sorted_out[:8]:
            t2.add_row(str(col), str(ct))
        console.print(t2)

    console.print("\n")

def scan_files(paths: list[Path]):
    """Scan multiple files with rich progress and print per-file reports + final summary."""
    results = []
    total = len(paths)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Scanning datasets...", total=total)
        for p in paths:
            progress.update(task, description=f"🔎 Reading {p.name}")
            with console.status(f"Reading {p.name}", spinner="dots"):
                try:
                    analysis = analyze_file(p)
                except Exception as e:
                    console.print(f"[red]❌ Failed to read {p.name}: {e}")
                    analysis = {"file": p.name, "error": str(e)}
            if "error" in analysis:
                console.print(Panel(f"Error analyzing {p.name}: {analysis['error']}", style="red"))
            else:
                pretty_print(analysis)
                results.append(analysis)
            progress.advance(task)

    if results:
        avg_quality = round(sum(r["quality"] for r in results) / len(results), 1)
        s = Table(show_header=False, box=box.SIMPLE)
        s.add_column("Metric")
        s.add_column("Value")
        s.add_row("Scanned files", str(len(results)))
        s.add_row("Avg quality", f"{avg_quality}/10")
        console.print(Panel(s, title="WHITEPAPER SUMMARY", box=box.DOUBLE))

    return results
