import re

import matplotlib.patches as patches
import matplotlib.pyplot as plt


def visualize(output: str):
    in_location_pattern = re.compile(
        r"in_location\(s1_loc\(location\((\d+),(\d+)\)\),location\((\d+),(\d+)\),(\d+)\)"
    )
    side_points_towards_pattern = re.compile(
        r"side_points_towards\(s1_loc\(location\((\d+),(\d+)\)\),(\d+),(\w+),(\d+)\)"
    )
    has_edge_pattern = re.compile(
        r"has_edge\(s1_loc\(location\((\d+),(\d+)\)\),edge_descriptor\((\d+),(inny|outy)\),(\d+)\)"
    )

    # Initialize data structures
    solutions = {}
    edges_per_piece = {}

    # Process each fact and update the appropriate data structures
    for fact in output.split():
        if in_location_pattern.match(fact):
            m = in_location_pattern.match(fact)
            assert m is not None
            piece_x, piece_y, loc_x, loc_y, solution_idx = map(int, m.groups())
            piece = f"s1_loc(location({piece_x},{piece_y}))"
            if solution_idx not in solutions:
                solutions[solution_idx] = {}
            if piece not in solutions[solution_idx]:
                solutions[solution_idx][piece] = {"location": None, "sides": {}}
            solutions[solution_idx][piece]["location"] = (loc_x, loc_y)

        elif side_points_towards_pattern.match(fact):
            m = side_points_towards_pattern.match(fact)
            assert m is not None
            piece_x, piece_y, side, direction, solution_idx = m.groups()
            piece = f"s1_loc(location({piece_x},{piece_y}))"
            side = int(side)
            solution_idx = int(solution_idx)
            if solution_idx not in solutions:
                solutions[solution_idx] = {}
            if piece not in solutions[solution_idx]:
                solutions[solution_idx][piece] = {"location": None, "sides": {}}
            solutions[solution_idx][piece]["sides"][side] = direction

        elif has_edge_pattern.match(fact):
            m = has_edge_pattern.match(fact)
            assert m is not None
            piece_x, piece_y, edge_type, polarity, side = m.groups()
            piece = f"s1_loc(location({piece_x},{piece_y}))"
            edge_type = int(edge_type)
            side = int(side)
            if piece not in edges_per_piece:
                edges_per_piece[piece] = {}
            edges_per_piece[piece][side] = {"E": edge_type, "P": polarity}

    # Edge colors mapping
    edge_colors = {
        1: "red",
        2: "green",
        3: "blue",
        4: "cyan",
        5: "magenta",
        6: "yellow",
        7: "orange",
        8: "purple",
        9: "brown",
        10: "pink",
        11: "gray",
        12: "olive",
        13: "lightblue",
        14: "darkgreen",
        15: "darkred",
        16: "darkblue",
        17: "darkcyan",
        18: "darkmagenta",
        19: "gold",
        20: "darkorange",
    }

    # Create a figure for side-by-side layouts
    fig, axes = plt.subplots(
        1, len(solutions), figsize=(6 * len(solutions), 6)
    )  # Dynamically adjust the number of columns

    if len(solutions) == 1:
        axes = [axes]  # Ensure axes is always a list

    for idx, (solution_idx, pieces_in_solution) in enumerate(sorted(solutions.items())):
        ax = axes[idx]  # Access the left or right axis
        # Build grid
        grid = [[None for _ in range(5)] for _ in range(5)]
        for piece, data in pieces_in_solution.items():
            location = data["location"]
            sides = data["sides"]  # mapping from Side to Direction
            edges = edges_per_piece.get(piece, {})
            # Build mapping from Direction to Edge Descriptor
            direction_to_edge = {}
            for side, direction in sides.items():
                edge = edges.get(side, None)
                direction_to_edge[direction] = (
                    edge  # edge is {'E': edge_type, 'P': polarity} or None
                )
            # Store in grid
            loc_x, loc_y = location
            grid[loc_y - 1][loc_x - 1] = {"Piece": piece, "edges": direction_to_edge}
        # Now, grid is built. We can proceed to render the grid
        # Draw each cell
        for y in range(5):
            for x in range(5):
                cell = grid[y][x]
                if cell is None:
                    continue
                piece = cell["Piece"]
                edges = cell["edges"]  # mapping from Direction to edge descriptor
                # Draw the square
                rect = patches.Rectangle(
                    (x, y), 1, 1, linewidth=1, edgecolor="black", facecolor="white"
                )
                ax.add_patch(rect)
                # Draw the piece identifier (abbreviated)
                match = re.match(r"s1_loc\(location\((\d+),(\d+)\)\)", piece)
                s1_x, s1_y = match.groups()
                ax.text(
                    x + 0.5,
                    y + 0.5,
                    f"{s1_x},{s1_y}",
                    ha="center",
                    va="center",
                    fontsize=8,
                )
                # Draw the edges
                for direction in ["north", "east", "south", "west"]:
                    edge = edges.get(direction, None)
                    if edge:
                        # Draw the edge
                        edge_type = edge["E"]
                        polarity = edge["P"]  # 'inny' or 'outy'
                        # Map edge type to a color
                        color = edge_colors.get(edge_type, "black")
                        # Determine positions for the edge line and label
                        if direction == "north":
                            x_start, y_start = x, y + 1
                            x_end, y_end = x + 1, y + 1
                            label_x, label_y = x + 0.5, y + 1.05
                            rotation = 0
                            arrow_direction = (
                                (0, 0.1) if polarity == "outy" else (0, -0.1)
                            )
                        elif direction == "east":
                            x_start, y_start = x + 1, y
                            x_end, y_end = x + 1, y + 1
                            label_x, label_y = x + 1.05, y + 0.5
                            rotation = 90
                            arrow_direction = (
                                (0.1, 0) if polarity == "outy" else (-0.1, 0)
                            )
                        elif direction == "south":
                            x_start, y_start = x, y
                            x_end, y_end = x + 1, y
                            label_x, label_y = x + 0.5, y - 0.05
                            rotation = 0
                            arrow_direction = (
                                (0, -0.1) if polarity == "outy" else (0, 0.1)
                            )
                        elif direction == "west":
                            x_start, y_start = x, y
                            x_end, y_end = x, y + 1
                            label_x, label_y = x - 0.05, y + 0.5
                            rotation = 90
                            arrow_direction = (
                                (-0.1, 0) if polarity == "outy" else (0.1, 0)
                            )
                        # Draw the edge
                        ax.plot(
                            [x_start, x_end], [y_start, y_end], color=color, linewidth=2
                        )
                        # Draw the edge label (optional)
                        edge_label = f"{edge_type}"
                        ax.text(
                            label_x,
                            label_y,
                            edge_label,
                            color=color,
                            ha="center",
                            va="center",
                            rotation=rotation,
                            fontsize=8,
                        )
                        # Draw the arrow to indicate 'inny' or 'outy'
                        arrow_x = x_start + (x_end - x_start) / 2
                        arrow_y = y_start + (y_end - y_start) / 2
                        dx, dy = arrow_direction
                        ax.arrow(
                            arrow_x,
                            arrow_y,
                            dx,
                            dy,
                            head_width=0.1,
                            head_length=0.1,
                            fc=color,
                            ec=color,
                            length_includes_head=True,
                        )

        # Set limits and configure the axis
        ax.set_xlim(0, 5)
        ax.set_ylim(0, 5)
        ax.set_aspect("equal")
        ax.set_title(f"Solution {solution_idx}")
        ax.invert_yaxis()  # Invert y-axis to match grid coordinates
        ax.axis("off")  # Turn off the axis

    # Display the side-by-side plot
    plt.tight_layout()
    plt.show()
