# Why it is needed: When an ultrasonic sensor reports an obstacle 50cm away, the mapping engine needs to
#  know which grid cells are completely Free (the empty air the sensor ray shot through) and which specific cell is
#  Occupied (where the ray hit the wall).

def bresenham_line(start, end):
    
    #extracts the coordinates
    row1, col1 = start
    row2, col2 = end

    cells = []

    #calculates how far the robot needs to move
    drow = abs(row2 - row1)
    dcol = abs(col2 - col1)

    #determines the direction
    row_step = 1 if row1 < row2 else -1
    col_step = 1 if col1 < col2 else -1

    error = dcol - drow

    row = row1
    col = col1

    while True:
        cells.append((row, col))

        if row == row2 and col == col2:
            break

        double_error = 2 * error

        if double_error > -drow:
            error -= drow
            col += col_step

        if double_error < dcol:
            error += dcol
            row += row_step

    return cells