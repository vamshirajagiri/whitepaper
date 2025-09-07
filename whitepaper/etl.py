# whitepaper/etl.py
import pandas as pd
import numpy as np
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from typing import List
import os
from .utils import calculate_file_hash, extract_hash_from_filename

console = Console()

# Thresholds & settings
MISSING_THRESHOLD = 0.5  # Drop columns with >50% missing
QUALITY_WARNING_THRESHOLD = 5  # Score below which dataset is flagged
CLEANED_DIR = Path("cleaned-dataset")

CLEANED_DIR.mkdir(exist_ok=True)

def calculate_quality(df: pd.DataFrame) -> float:
    """Return a dataset quality score out of 10"""
    total_cells = df.size
    missing = df.isna().sum().sum()
    duplicates = df.duplicated().sum()
    quality = max(0, 10 * (1 - ((missing + duplicates) / total_cells)))
    return round(quality, 1)

def flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Flag numeric outliers using IQR method"""
    outlier_flags = {}
    for col in df.select_dtypes(include=np.number).columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = df[(df[col] < lower) | (df[col] > upper)][col].count()
        outlier_flags[col] = outliers
    return outlier_flags

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Perform ETL cleaning on DataFrame"""
    # Drop columns with >50% missing (collect first to avoid mutating while iterating)
    threshold = int(len(df) * MISSING_THRESHOLD)
    cols_to_drop = [col for col in df.columns if df[col].isna().sum() > threshold]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    # Impute missing values using non-chained assignments to avoid pandas chained-assignment warnings
    for col in df.select_dtypes(include=np.number).columns:
        df[col] = df[col].fillna(df[col].median())
    for col in df.select_dtypes(include="object").columns:
        fill_val = df[col].mode()[0] if not df[col].mode().empty else ""
        df[col] = df[col].fillna(fill_val)
        df[col] = df[col].str.strip().str.lower()

    # Remove exact duplicates (functional style)
    df = df.drop_duplicates()

    return df

def etl_file(file_path: Path, detailed=True, overwrite=False):
    """ETL for single dataset with rich terminal output and hash-based caching"""
    try:
        df = pd.read_excel(file_path) if file_path.suffix in [".xls", ".xlsx"] else pd.read_csv(file_path)
    except Exception as e:
        console.print(f"[red]Failed to read {file_path.name}: {e}[/red]")
        return None

    # Calculate hash of original file
    current_hash = calculate_file_hash(file_path)

    # Check for existing cleaned files with matching hash (only if not in overwrite mode)
    if not overwrite:
        base_name = file_path.stem
        existing_cleaned_files = list(CLEANED_DIR.glob(f"{base_name}_cleaned_*.csv"))

        for existing_file in existing_cleaned_files:
            stored_hash = extract_hash_from_filename(existing_file.name)
            if stored_hash == current_hash[:8]:
                console.print(f"[yellow]✔ Skipping ETL, no changes detected for {file_path.name}[/yellow]")
                return None

    # Check if file is already cleaned and warn user
    is_already_cleaned = "_cleaned" in file_path.stem
    if is_already_cleaned:
        console.print(f"[yellow]⚠️ Warning: {file_path.name} appears to be already cleaned![/yellow]")
        console.print("[yellow]As per your request, re-processing and saving with incremental numbering...[/yellow]")

    # Pre-ETL summary
    missing = df.isna().sum().sum()
    duplicates = df.duplicated().sum()
    rows, cols = df.shape
    quality_before = calculate_quality(df)

    if detailed:
        console.print(Panel(f"🤖 ETL Agent starting for [bold]{file_path.name}[/bold]\n"
                            f"Rows: {rows} | Columns: {cols}\n"
                            f"Missing values: {missing} | Duplicates: {duplicates}\n"
                            f"Quality score: {quality_before}/10",
                            title="Dataset Summary", border_style="cyan"))

    # Progress bar for ETL
    steps = ["Reading", "Cleaning Missing Values", "Deduplication", "Outlier Detection", "Saving"]
    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"[cyan]Processing {file_path.name}...", total=len(steps))
        for step in steps:
            progress.update(task, description=f"[magenta]{step}[/magenta]")
            # simulate processing time for UX feel
            if step == "Outlier Detection":
                outliers = flag_outliers(df)
            elif step == "Saving":
                # Use hash-based naming convention
                if overwrite:
                    # Overwrite mode: keep latest cleaned version
                    cleaned_file = CLEANED_DIR / f"{file_path.stem}_cleaned_latest.csv"
                else:
                    # Hash-based naming: create unique version for each hash
                    cleaned_file = CLEANED_DIR / f"{file_path.stem}_cleaned_{current_hash[:8]}.csv"

                df.to_csv(cleaned_file, index=False)
                console.print(f"[green]✅ Successfully cleaned and saved: {cleaned_file.name}[/green]")
            else:
                df = clean_dataframe(df)
            progress.advance(task, 1)

    # After ETL summary
    quality_after = calculate_quality(df)
    outlier_counts = flag_outliers(df)
    if detailed:
        table = Table(title="Data Quality Metamorphosis")
        table.add_column("Metric", style="bold cyan")
        table.add_column("Before", justify="center")
        table.add_column("After", justify="center")
        table.add_row("Missing values", str(missing), str(df.isna().sum().sum()))
        table.add_row("Duplicates", str(duplicates), str(df.duplicated().sum()))
        table.add_row("Outliers flagged", str(sum(outlier_counts.values())), str(sum(outlier_counts.values())))
        table.add_row("Quality Score", str(quality_before), str(quality_after))
        console.print(table)

    # Red flag if quality low
    if quality_after < QUALITY_WARNING_THRESHOLD:
        console.print(Panel(f"⚠️ Dataset [bold]{file_path.name}[/bold] has low quality after ETL.\n"
                            f"Consider reviewing before policymaking.", style="bold red"))

    return df

def etl_files(paths: List[Path], overwrite=False):
    """ETL multiple files with multi-file UX handling"""
    detailed = True if len(paths) <= 7 else False
    for path in paths:
        etl_file(path, detailed=detailed, overwrite=overwrite)
