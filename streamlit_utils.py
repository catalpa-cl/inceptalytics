import streamlit as st


def st_grid(rows: int, cols: int = None):
    if cols is None:
        cols = rows

    return [st.columns(cols) for _ in range(rows)]


def st_indexed_grid(row_idxs: list, col_idxs: list = None):
    if col_idxs is None:
        col_idxs = row_idxs

    n_rows = len(row_idxs)
    n_cols = len(col_idxs)
    grid = st_grid(n_rows, n_cols)

    indexed_grid = {}
    for i, row_idx in enumerate(row_idxs):
        row = grid[i]
        indexed_row = {col_idx: cell for col_idx, cell in zip(col_idxs, row)}
        indexed_grid[row_idx] = indexed_row

    return indexed_grid


def st_indexed_triangle(row_idxs: list, col_idxs: list = None, top=True):
    if col_idxs is None:
        col_idxs = row_idxs

    n_rows = len(row_idxs) - 1
    n_cols = len(col_idxs) - 1
    grid = st_grid(n_rows, n_cols)

    if top:
        row_slicer = slice(0, -1)
        col_slicer = slice(1, None)
    else:
        row_slicer = slice(1, None, -1)
        col_slicer = slice(-1, None, -1)

    indexed_grid = {}
    for i, row_idx in enumerate(row_idxs[row_slicer]):
        row = grid[i]
        indexed_row = {col_idx: cell for col_idx, cell in zip(col_idxs[col_slicer], row)}
        indexed_grid[row_idx] = indexed_row

    return indexed_grid

