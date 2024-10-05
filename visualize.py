import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import matplotlib.patches as patches
import matplotlib.pyplot as plt


@dataclass
class EdgeDescriptor:
    edge_type: int  # E
    polarity: str   # 'inny' or 'outy'


@dataclass
class Piece:
    piece_id: str
    location: Optional[Tuple[int, int]] = None  # (loc_x, loc_y)
    sides: Dict[int, str] = field(default_factory=dict)  # Side number to Direction mapping
    edges: Dict[int, EdgeDescriptor] = field(default_factory=dict)  # Side number to EdgeDescriptor


@dataclass
class Solution:
    solution_idx: int
    pieces: Dict[str, Piece] = field(default_factory=dict)  # piece_id to Piece object


def extract_coordinates(piece_id: str) -> Tuple[int, int]:
    match = re.match(r"s1_loc\(location\((\d+),(\d+)\)\)", piece_id)
    if match:
        x_str, y_str = match.groups()
        return int(x_str), int(y_str)
    else:
        raise ValueError(f"Invalid piece_id format: {piece_id}")


def visualize(output: str) -> None:
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
    solutions: Dict[int, Solution] = {}

    # Process each fact and update the appropriate data structures
    for fact in output.split():
        if in_location_pattern.match(fact):
            m = in_location_pattern.match(fact)
            assert m is not None
            piece_x_str, piece_y_str, loc_x_str, loc_y_str, solution_idx_str = m.groups()
            piece_id = f"s1_loc(location({piece_x_str},{piece_y_str}))"
            loc_x, loc_y = int(loc_x_str), int(loc_y_str)
            solution_idx = int(solution_idx_str)
            if solution_idx not in solutions:
                solutions[solution_idx] = Solution(solution_idx)
            solution = solutions[solution_idx]
            if piece_id not in solution.pieces:
                solution.pieces[piece_id] = Piece(piece_id)
            piece = solution.pieces[piece_id]
            piece.location = (loc_x, loc_y)

        elif side_points_towards_pattern.match(fact):
            m = side_points_towards_pattern.match(fact)
            assert m is not None
            piece_x_str, piece_y_str, side_str, direction, solution_idx_str = m.groups()
            piece_id = f"s1_loc(location({piece_x_str},{piece_y_str}))"
            side = int(side_str)
            solution_idx = int(solution_idx_str)
            if solution_idx not in solutions:
                solutions[solution_idx] = Solution(solution_idx)
            solution = solutions[solution_idx]
            if piece_id not in solution.pieces:
                solution.pieces[piece_id] = Piece(piece_id)
            piece = solution.pieces[piece_id]
            piece.sides[side] = direction

        elif has_edge_pattern.match(fact):
            m = has_edge_pattern.match(fact)
            assert m is not None
            piece_x_str, piece_y_str, edge_type_str, polarity, side_str = m.groups()
            piece_id = f"s1_loc(location({piece_x_str},{piece_y_str}))"
            edge_type = int(edge_type_str)
            side = int(side_str)
            # Since 'has_edge' facts do not have a solution index, we'll assume that edge descriptors are the same across all solutions.
            # We'll need to add the edge descriptors to all pieces in all solutions.
            for solution in solutions.values():
                if piece_id not in solution.pieces:
                    solution.pieces[piece_id] = Piece(piece_id)
                piece = solution.pieces[piece_id]
                piece.edges[side] = EdgeDescriptor(edge_type, polarity)

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
    num_solutions = len(solutions)
    fig, axes = plt.subplots(
        1, num_solutions, figsize=(6 * num_solutions, 6)
    )  # Dynamically adjust the number of columns

    if num_solutions == 1:
        axes = [axes]  # Ensure axes is always a list

    for idx, (solution_idx, solution) in enumerate(sorted(solutions.items())):
        ax = axes[idx]  # Access the corresponding axis
        # Build grid
        grid: List[List[Optional[Piece]]] = [[None for _ in range(5)] for _ in range(5)]
        for piece_id, piece in solution.pieces.items():
            if piece.location is None:
                continue  # Skip pieces without location
            loc_x, loc_y = piece.location
            grid[loc_y - 1][loc_x - 1] = piece
        # Now, grid is built. We can proceed to render the grid
        # Draw each cell
        for y in range(5):
            for x in range(5):
                piece = grid[y][x]
                if piece is None:
                    continue
                # Draw the square
                rect = patches.Rectangle(
                    (x, y), 1, 1, linewidth=1, edgecolor="black", facecolor="white"
                )
                ax.add_patch(rect)
                # Draw the piece identifier (coordinates)
                s1_x, s1_y = extract_coordinates(piece.piece_id)
                ax.text(
                    x + 0.5,
                    y + 0.5,
                    f"{s1_x},{s1_y}",
                    ha="center",
                    va="center",
                    fontsize=8,
                )
                # Build mapping from Direction to EdgeDescriptor
                direction_to_edge: Dict[str, Optional[EdgeDescriptor]] = {}
                for side, direction in piece.sides.items():
                    edge = piece.edges.get(side, None)
                    direction_to_edge[direction] = edge  # EdgeDescriptor or None

                # Draw the edges
                for direction in ["north", "east", "south", "west"]:
                    edge = direction_to_edge.get(direction, None)
                    if edge:
                        # Draw the edge
                        edge_type = edge.edge_type
                        polarity = edge.polarity  # 'inny' or 'outy'
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
                        else:
                            continue  # Invalid direction
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
