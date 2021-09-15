import streamlit as st

def st_grid(rows: int, cols: int = None):
    """
    Creates a rows x cols grid of containers using st.columns and returns it as a nested list of grid cells.

    Args:
        rows: number of rows in the grid.
        cols: number of columns in the grid. If not provided, a square grid is created with cols = rows.
    """
    if cols is None:
        cols = rows

    return [st.columns(cols) for _ in range(rows)]


def st_indexed_grid(row_idxs: list, col_idxs: list = None):
    """
    Creates a grid of containers using st.columns, returning it as a nested dictionary of grid cells.
    Grid cells can be accessed using the provided indices.The first dimension is reserved for rows, the second for
    columns.
    Grid dimensions are implicitly defined by the number of provided indices.

        Args:
            row_idxs: Indices for rows of the grid (1st axis).
            col_idxs: Indices for columns of the grid (2nd axis). If not provided, a square grid is created with
                col_idxs = row_idxs.
    """
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


def st_indexed_triangle(row_idxs: list, col_idxs: list = None, offset: int = 0, top=True):
    """
    Creates a in indexed grid from the given indices in which only a triangle is accessible.
    Grid dimensions are implicitly defined by the number of provided indices.

    Args:
        row_idxs: Indices for rows of the grid (1st axis).
        col_idxs: Indices for columns of the grid (2nd axis). If not provided, a square grid is created with
            col_idxs = row_idxs.
        offset: Offset from the main diagonal to use for the triangle. If an
        top: If set to true, the top triangle is used, if set to false, the bottom triangle is used.
    """
    if offset < 0:
        raise ValueError('Offset must be a positive integer.')

    if col_idxs is None:
        col_idxs = row_idxs

    n_rows = len(row_idxs) - offset
    n_cols = len(col_idxs) - offset
    grid = st_grid(n_rows, n_cols)

    if top:
        row_slicer = slice(0, n_rows)
        col_slicer = slice(offset, None)
    else:
        row_slicer = slice(offset, None, 1)
        col_slicer = slice(n_cols, None, -1)

    indexed_grid = {}
    for i, row_idx in enumerate(row_idxs[row_slicer]):
        row = grid[i]
        indexed_row = {col_idx: cell for col_idx, cell in zip(col_idxs[col_slicer], row)}
        indexed_grid[row_idx] = indexed_row

    # TODO: Map bottom half of triangle to top half (if top), vice versa (if bottom).

    return indexed_grid

