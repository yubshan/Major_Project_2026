
import json

from constants import TILE_FLOOR, TILE_WALL, TILE_OBSTACLE


class MapLoader:

    def __init__(self, file_path):
        self.file_path = file_path
        self.map_data = None

    def load_map(self):

        # Read JSON file
        with open(self.file_path, "r") as file:
            data = json.load(file)

        # Check required properties
        required_keys = ["name", "rows", "cols", "tiles"]

        for key in required_keys:
            if key not in data:
                raise ValueError(
                    f"Missing required map property: {key}"
                )

        # Validate map name
        if not isinstance(data["name"], str) or not data["name"].strip():
            raise ValueError("Map name must be a non-empty string")

        rows = data["rows"]
        cols = data["cols"]
        tiles = data["tiles"]

        # Validate dimensions
        if not isinstance(rows, int) or isinstance(rows, bool) or rows <= 0:
            raise ValueError("Rows must be a positive integer")

        if not isinstance(cols, int) or isinstance(cols, bool) or cols <= 0:
            raise ValueError("Columns must be a positive integer")

        # Validate tile array
        if not isinstance(tiles, list):
            raise ValueError("Tiles must be a list")

        if len(tiles) != rows:
            raise ValueError(
                f"Expected {rows} rows, but found {len(tiles)}"
            )

        # Validate each row and tile
        valid_tile_types = (
            TILE_FLOOR,
            TILE_WALL,
            TILE_OBSTACLE
        )

        for row_index, row in enumerate(tiles):

            if not isinstance(row, list):
                raise ValueError(
                    f"Row {row_index} must be a list"
                )

            if len(row) != cols:
                raise ValueError(
                    f"Row {row_index} must contain {cols} tiles"
                )

            for col_index, tile in enumerate(row):

                if not isinstance(tile, int) or isinstance(tile, bool):
                    raise ValueError(
                        f"Invalid tile at row {row_index}, "
                        f"column {col_index}"
                    )

                if tile not in valid_tile_types:
                    raise ValueError(
                        f"Unknown tile type {tile} at row {row_index}, "
                        f"column {col_index}"
                    )

        # Save validated map
        self.map_data = data

        print("Map validation successful!")

        return self.map_data
