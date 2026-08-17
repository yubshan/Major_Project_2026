import heapq


FREE = 0
OCCUPIED = 1
UNKNOWN = 2


def heuristic(a, b):
    
    # Calculate Manhattan distance between two grid cells.
    
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_neighbors(cell):
    
    # Return the four neighboring cells.
    
    row, col = cell

    return [
        (row - 1, col),  # Up
        (row + 1, col),  # Down
        (row, col - 1),  # Left
        (row, col + 1),  # Right
    ]


def a_star(grid, start, goal):
    """
    Find the shortest path from start to goal using A*.

    Returns:
        List of grid cells from start to goal,
        or None if no path exists.
    """

    # Start and goal must be valid grid cells.
    start_row, start_col = start
    goal_row, goal_col = goal

    if not (
        0 <= start_row < grid.data.shape[0]
        and 0 <= start_col < grid.data.shape[1]
    ):
        return None

    if not (
        0 <= goal_row < grid.data.shape[0]
        and 0 <= goal_col < grid.data.shape[1]
    ):
        return None

    # A path cannot start from or end on an occupied cell.
    if grid.get_cell(*start) == OCCUPIED:
        return None

    if grid.get_cell(*goal) == OCCUPIED:
        return None

    open_set = []

    heapq.heappush(
        open_set,
        (0, start)
    )

    came_from = {}

    g_score = {
        start: 0
    }

    f_score = {
        start: heuristic(start, goal)
    }

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor in get_neighbors(current):

            row, col = neighbor

            # Ignore cells outside the grid.
            if not (
                0 <= row < grid.data.shape[0]
                and 0 <= col < grid.data.shape[1]
            ):
                continue

            # Do not move through occupied cells.
            if grid.get_cell(row, col) == OCCUPIED:
                continue

            tentative_g_score = g_score[current] + 1

            if tentative_g_score < g_score.get(neighbor, float("inf")):

                came_from[neighbor] = current

                g_score[neighbor] = tentative_g_score

                f_score[neighbor] = (
                    tentative_g_score
                    + heuristic(neighbor, goal)
                )

                heapq.heappush(
                    open_set,
                    (f_score[neighbor], neighbor)
                )

    return None


def reconstruct_path(came_from, current):
    
    # Reconstruct the path from goal back to start.


    path = [current]

    while current in came_from:
        current = came_from[current]
        path.append(current)

    path.reverse()

    return path