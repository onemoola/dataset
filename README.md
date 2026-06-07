# Dataseka Public Datasets (`onemoola/dataset`)

Public dataset repository for the [Dataseka](https://dataseka.com/) platform.

This repository houses the ingestion, transformation, and processing pipelines used to structure public data into clean,
unified formats for the Dataseka platform - built for speed, reproducibility, and strict data quality.

---

## 🛠️ Tech Stack

Built on a modern, high-performance Python data stack:

- **Runtime:** Python >= 3.13
- **Package Management:** [uv](https://github.com/astral-sh/uv) — fast, reproducible dependency resolution
- **Data Processing:** [Polars](https://pola.rs/) & FastExcel — multi-threaded, memory-efficient ETL
- **Notebooks:** [Marimo](https://marimo.io/) — reactive, git-friendly data exploration and pipeline orchestration
- **Network & Validation:** HTTPX (HTTP/2) for fast ingestion and Pydantic for strict data validation
- **Code Quality:** Ruff (linting/formatting) and Mypy (strict type checking)

---

## 📂 Project Structure

The repository is organised by geographic region or data domain. The primary package is currently `south_africa/`.

```
.
├── pyproject.toml              # Project configuration, dependencies, and tool settings
├── README.md
└── south_africa/               # South African data pipelines
    ├── data/                   # Target directory for raw downloads and processed exports (git-ignored)
    ├── ingestions/             # Modules for fetching raw data from source (e.g., Stats SA) using HTTPX
    ├── tools/                  # Shared utilities, helper functions, and text normalisation tools
    └── transformations/        # Polars-based adapter modules that clean and shape the data
```

> Marimo notebooks orchestrating the pipeline will typically reside at the root of the regional folder or within
> specific task folders, importing directly from these modules.

---

## 🚀 Getting Started

### 1. Prerequisites

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) to manage dependencies.

### 2. Installation

Clone the repository and sync the environment:

```bash
git clone https://github.com/onemoola/dataset.git
cd dataset

# Create a virtual environment and install all dependencies from the lockfile
uv sync
```

### 3. Running the Pipelines

Launch the Marimo interactive notebook environment directly via `uv`:

```bash
# Open the Marimo editor in your browser to run or modify pipelines
uv run marimo edit
```

---

## 🧑‍💻 Development & Code Quality

This project enforces strict coding standards to ensure pipeline reliability. Before committing, ensure all checks pass.

### Linting & Formatting (Ruff)

```bash
# Check for linting errors
uv run ruff check .

# Automatically fix fixable errors (e.g., unused imports, formatting)
uv run ruff check --fix .
```

### Static Type Checking (Mypy)

```bash
uv run mypy .
```