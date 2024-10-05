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

from visualize import visualize

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
