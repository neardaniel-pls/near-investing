# AGENTS.md

Guidance for AI agents (and humans) working on NEAR Investing.

## Project

Streamlit portfolio analysis & optimization tool for European investors.
- Entry point: `app.py` (home page)
- Pages: `pages/1_Dashboard.py` … `pages/5_Simulate.py`
- Logic: `src/` (data, metrics, optimization, portfolio, monte_carlo, rolling, charts, styles, ui, config, export)
- Data flow: fetch once on Home → store in `st.session_state` (`prices`, `returns`, `tickers`, `ticker_names`) → reused across pages.

## Commands

```bash
# Install (first time)
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# Run the app
streamlit run app.py

# Syntax / compile check (no deps needed) — run after every change
python -m compileall app.py pages/ src/

# Tests (need project deps installed)
pytest -q
```

There is no configured linter or type-checker. Prefer `python -m compileall` as the
fast sanity check, and `pytest` for the pure-function logic in `src/`.

## Conventions

- Keep `src/` dependency-free of Streamlit where possible (UI helpers live in `src/ui.py`
  and the pages). Pure numeric logic (`metrics.py`, `monte_carlo.py`, `portfolio.py`,
  `optimization.py`) must be unit-testable without a Streamlit context.
- Metric functions return `np.nan` (never `float("inf")`) on degenerate inputs so they
  don't break tables/charts. See `src/metrics.py`.
- Always re-run `python -m compileall app.py pages/ src/` after edits.
- After logic changes in `src/`, run the relevant `tests/`.

## Testing notes

- Tests use **synthetic** price data (no network) so they run offline and fast.
- `yfinance`-dependent functions (`fetch_prices`, `fetch_ticker_names`) are NOT covered
  by unit tests; verify manually via the app.
