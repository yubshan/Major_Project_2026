from constants import TILE_WIDTH, TILE_HEIGHT


def grid_to_screen(row, col):
    """
    Convert grid coordinates (row, col)
    to screen coordinates (x, y)
    using isometric projection.
    """

    x = (col - row) * (TILE_WIDTH // 2)
    y = (col + row) * (TILE_HEIGHT // 2)

    return x, y