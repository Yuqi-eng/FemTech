#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------
# FEMTech / BSRP coordinate mapping
#
# Prevent / iMG coordinate system:
#   +X = anterior
#   +Y = right
#   +Z = inferior
#
# Native BSRP mesh coordinate system:
#   +X = left
#   +Y = inferior
#   +Z = posterior
#
# Therefore the FEMTech mesh transformation is:
#   X_mesh = -Y_Prevent
#   Y_mesh =  Z_Prevent
#   Z_mesh = -X_Prevent
# ----------------------------------------------------------------------

MESH_TRANSFORMATION = ["-y", "z", "-x"]

REQUIRED_COLUMNS = [
    "T.ms",
    "PAA.X.radsec^2",
    "PAA.Y.radsec^2",
    "PAA.Z.radsec^2",
    "PAV.X.radsec",
    "PAV.Y.radsec",
    "PAV.Z.radsec",
    "PLA.X.msec^2",
    "PLA.Y.msec^2",
    "PLA.Z.msec^2",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)

def read_csv(csv_path: Path) -> pd.DataFrame:
    """Read comma- or tab-delimited Prevent data."""
    try:
        df = pd.read_csv(csv_path, sep=None, engine="python")
    except Exception as exc:
        fail(f"Could not read '{csv_path}': {exc}")

    # Remove accidental whitespace from headers
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]

    if missing:
        fail(
            "Missing required columns:\n  "
            + "\n  ".join(missing)
            + "\n\nAvailable columns:\n  "
            + "\n  ".join(df.columns)
        )

    return df

def validate_data(df: pd.DataFrame) -> None:
    """Check numeric data, time ordering, and sampling."""

    for col in REQUIRED_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in REQUIRED_COLUMNS:
        if df[col].isna().any():
            n_bad = int(df[col].isna().sum())
            fail(f"Column '{col}' contains {n_bad} invalid/NaN values.")

    if len(df) < 2:
        fail("At least two time samples are required.")

    t = df["T.ms"].to_numpy()

    if not all(t[i + 1] > t[i] for i in range(len(t) - 1)):
        fail("T.ms must be strictly increasing.")

    dt = t[1:] - t[:-1]

    if (dt <= 0).any():
        fail("Time contains non-positive intervals.")

    median_dt = float(pd.Series(dt).median())

    if median_dt <= 0:
        fail("Invalid median timestep.")

    sampling_frequency = 1000.0 / median_dt

    print(f"Samples:       {len(df)}")
    print(f"Start time:    {t[0]:.6f} ms")
    print(f"End time:      {t[-1]:.6f} ms")
    print(f"Median dt:     {median_dt:.6f} ms")
    print(f"Approx. rate:  {sampling_frequency:.2f} Hz")

def get_initial_angular_velocity(df: pd.DataFrame) -> list[float]:
    """
    Take the measured angular velocity at the first sample.

    Prevent units:
        rad/s
    """
    return [
        float(df["PAV.X.radsec"].iloc[0]),
        float(df["PAV.Y.radsec"].iloc[0]),
        float(df["PAV.Z.radsec"].iloc[0]),
    ]

def build_input_json(
    df: pd.DataFrame,
    mesh: str,
    uid: str,
    player_name: str,
    player_position: str,
) -> dict:
    """Build the exact nested structure expected by ex5."""

    # FEMTech's time-history branch converts these values from ms to s
    # internally, so keep the original Prevent times in milliseconds.
    t = [float(x) for x in df["T.ms"]]

    # Linear acceleration: m/s^2
    linear_x = [float(x) for x in df["PLA.X.msec^2"]]
    linear_y = [float(x) for x in df["PLA.Y.msec^2"]]
    linear_z = [float(x) for x in df["PLA.Z.msec^2"]]

    # Angular acceleration: rad/s^2
    angular_x = [float(x) for x in df["PAA.X.radsec^2"]]
    angular_y = [float(x) for x in df["PAA.Y.radsec^2"]]
    angular_z = [float(x) for x in df["PAA.Z.radsec^2"]]

    # Measured initial angular velocity: rad/s
    initial_omega = get_initial_angular_velocity(df)

    simulation = {
        "mesh": mesh,

        "linear-acceleration": {
            "xt": t,
            "xv": linear_x,
            "yt": t,
            "yv": linear_y,
            "zt": t,
            "zv": linear_z,
        },

        "angular-acceleration": {
            "xt": t,
            "xv": angular_x,
            "yt": t,
            "yv": angular_y,
            "zt": t,
            "zv": angular_z,
        },

        # Requires the corresponding modification to ex5.cpp.
        "initial-angular-velocity": initial_omega,

        "maximum-time": t[-1],

        "mesh-transformation": MESH_TRANSFORMATION,
    }

    return {
        "uid": uid,
        "player": {
            "name": player_name,
            "position": player_position,
        },
        "simulation": simulation,
    }


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Convert filtered Prevent Biometrics acceleration data "
            "to FEMTech ex5 input.json."
        )
    )

    parser.add_argument(
        "csv",
        type=Path,
        help="Filtered Prevent CSV file.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("input.json"),
        help="Output JSON file. Default: input.json",
    )

    parser.add_argument(
        "--mesh",
        default="coarse_brain.inp",
        help="FEMTech mesh filename. Default: coarse_brain.inp",
    )

    parser.add_argument(
        "--uid",
        default="prevent_impact",
        help="Impact UID stored in the JSON.",
    )

    parser.add_argument(
        "--player-name",
        default="unknown",
        help="Player name stored in the JSON.",
    )

    parser.add_argument(
        "--player-position",
        default="unknown",
        help="Player position stored in the JSON.",
    )

    args = parser.parse_args()

    if not args.csv.exists():
        fail(f"CSV file does not exist: {args.csv}")

    print(f"Input:  {args.csv}")
    print(f"Output: {args.output}")
    print()

    df = read_csv(args.csv)

    validate_data(df)

    output = build_input_json(
        df=df,
        mesh=args.mesh,
        uid=args.uid,
        player_name=args.player_name,
        player_position=args.player_position,
    )

    try:
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
            f.write("\n")
    except Exception as exc:
        fail(f"Could not write '{args.output}': {exc}")

    omega0 = output["simulation"]["initial-angular-velocity"]

    print()
    print("Initial angular velocity:")
    print(f"  X = {omega0[0]:.6f} rad/s")
    print(f"  Y = {omega0[1]:.6f} rad/s")
    print(f"  Z = {omega0[2]:.6f} rad/s")

    print()
    print("Mesh transformation:")
    print(f"  {output['simulation']['mesh-transformation']}")

    print()
    print(
        "Simulation end time: "
        f"{output['simulation']['maximum-time']:.6f} ms"
    )

    print()
    print(f"Saved: {args.output}")

if __name__ == "__main__":
    main()
