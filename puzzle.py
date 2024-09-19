#!/usr/bin/env python3

import argparse
import io
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.patches as patches
import matplotlib.pyplot as plt

ASP_DIR: Path = Path(__file__).parent / "asp"


def parse_clingo_output(process: subprocess.Popen[str], output_file: Path):
    best_optimization_value = None
    current_solution = ""
    in_solution = False

    try:
        for line in iter(process.stdout.readline, ""):  # type: ignore
            if line == "":
                break  # EOF

            print(line, end="")  # Echo clingo's output if needed

            if line.startswith("Answer:"):
                in_solution = True
                current_solution = ""
            elif line.startswith("Optimization:"):
                in_solution = False
                optimization_values = line.strip().split()[1:]  # Skip 'Optimization:'
                optimization_values = [int(v) for v in optimization_values]
                # For simplicity, we assume a single optimization value
                optimization_value = optimization_values[0]
                if (best_optimization_value is None) or (
                    optimization_value < best_optimization_value
                ):
                    best_optimization_value = optimization_value
                    # Write the current_solution to the output file safely
                    with tempfile.NamedTemporaryFile(
                        "w", delete=False, dir=os.path.dirname(output_file)
                    ) as tf:
                        tf.write(current_solution)
                        temp_output_file = tf.name
                    shutil.move(temp_output_file, output_file)
                    print("Press Ctrl+C to finish (or wait for better solutions)")
            elif in_solution:
                current_solution += line
    except KeyboardInterrupt:
        process.terminate()
        process.wait()


def search(args: argparse.Namespace):
    clingo_command = ["clingo"]

    if args.t:
        clingo_command.append(f"-t{args.t}")

    # Add constants
    clingo_command += [
        "--const",
        f"int_edge_types={args.int_edge_types}",
        "--const",
        f"ext_edge_types={args.ext_edge_types}",
        "--const",
        f"min_usage_count={args.min_usage_count}",
    ]

    # Add ASP files
    clingo_command += [ASP_DIR / "search.asp", ASP_DIR / "common.asp"]
    if args.enforce_distinct:
        clingo_command.append(ASP_DIR / "distinct_pieces.asp")

    # Start clingo process
    process = subprocess.Popen(
        clingo_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
    )

    # Process clingo output
    parse_clingo_output(process, args.output_file)

    process.wait()


def count(args: argparse.Namespace):
    # Read the solution from the input file
    with open(args.input_file, "r") as f:
        solution = f.read()

    # Call dump_edges() to produce input for solve.asp
    edges_input = dump_edges(solution)  # Assuming dump_edges returns a string

    clingo_command = ["clingo"]

    if args.t:
        clingo_command.append(f"-t{args.t}")

    # Run clingo solve.asp - 0 with the edges_input as stdin
    clingo_command += [ASP_DIR / "solve.asp", ASP_DIR / "common.asp", "-", "0"]
    process = subprocess.Popen(
        clingo_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
        universal_newlines=True,
    )

    stdout, _stderr = process.communicate(input=edges_input)

    # Parse the number of solutions found
    num_models = 0
    for line in stdout.splitlines():
        if line.startswith("Models"):
            # Line format: Models       : 1
            num_models = int(line.split(":")[1].strip())
            break

    print(f"Number of solutions found: {num_models}")


def viz(args: argparse.Namespace):
    # Read the solution from the input file
    with open(args.input_file, "r") as f:
        solution = f.read()

    # Call the visualize() function
    visualize(solution)


# Assuming dump_edges and visualize functions are defined
def dump_edges(output: str) -> str:
    # Split into facts
    facts = output.strip().split()

    # Regular expression to match 'has_edge' literals
    has_edge_pattern = re.compile(
        r"has_edge\(s1_loc\(location\(\d+,\d+\)\),edge_descriptor\(\d+,(inny|outy)\),\d+\)"
    )

    # List to store extracted 'has_edge' facts
    has_edge_facts: List[str] = []

    # Process each fact and extract only 'has_edge' literals
    for fact in facts:
        if has_edge_pattern.match(fact):
            has_edge_facts.append(fact)

    # Write the extracted 'has_edge' literals to the output file
    with io.StringIO() as f:
        for has_edge in has_edge_facts:
            f.write(f"{has_edge}.\n")

        return f.getvalue()


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


def parse_fact(fact: str) -> Optional[Tuple[str, List[str]]]:
    m = re.match(r"(\w+)\((.*)\)", fact)
    if not m:
        print(f"Could not parse fact: {fact}")
        return None
    predicate = m.group(1)
    args_str = m.group(2)
    args = parse_arguments(args_str)
    return predicate, args


def parse_arguments(args_str: str) -> List[str]:
    args: List[str] = []
    arg = ""
    depth = 0
    for c in args_str:
        if c == "," and depth == 0:
            args.append(arg.strip())
            arg = ""
        else:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            arg += c
    if arg:
        args.append(arg.strip())
    return args


def main():
    parser = argparse.ArgumentParser(
        description="Python wrapper for clingo ASP solver."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search subcommand
    solve_parser = subparsers.add_parser("search", help="Search for puzzle pairs")
    solve_parser.add_argument("--int-edge-types", type=int, required=True)
    solve_parser.add_argument("--ext-edge-types", type=int, required=True)
    solve_parser.add_argument("--min-usage-count", type=int, required=True)
    solve_parser.add_argument("--enforce-distinct", action="store_true")
    solve_parser.add_argument("-t", type=int, help="Number of threads to use")
    solve_parser.add_argument("output_file", help="File path to output solutions to")
    solve_parser.set_defaults(func=search)

    # Count subcommand
    count_parser = subparsers.add_parser("count", help="Count the solutions")
    count_parser.add_argument("-t", type=int, help="Number of threads to use")
    count_parser.add_argument("input_file", help="Output file from search")
    count_parser.set_defaults(func=count)

    # Viz subcommand
    viz_parser = subparsers.add_parser("viz", help="Visualize the solution pair")
    viz_parser.add_argument("input_file", help="Output file from search")
    viz_parser.set_defaults(func=viz)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
