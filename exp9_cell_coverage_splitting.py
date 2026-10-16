"""
Experiment 9: Analysis of Cell Coverage, Cell Radius, and Cell Splitting
-------------------------------------------------------------------------
This program simulates and analyzes:
  1. Maximum Cell Radius (R) based on Path Loss and Receiver Sensitivity.
  2. Cell Coverage Area (Hexagonal Cell Model: A = 2.598 * R^2).
  3. Total number of cells required to cover a service area.
  4. Cell Splitting: Halving cell radius (R/2) to increase capacity by 4x.
  5. Required transmit power reduction for split cells to avoid interference.
  6. Graphical analysis: Coverage vs Distance & Cell Splitting Geometry.
"""

import numpy as np
import matplotlib.pyplot as plt


# ==============================================================================
# 1. HELPER FUNCTION FOR USER INPUTS
# ==============================================================================

def ask(prompt, default):
    """Read numeric input with an automatic default value."""
    val = input(f"{prompt} [default {default}]: ").strip()
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        print("  Invalid input. Using default:", default)
        return default


# ==============================================================================
# 2. INPUT PARAMETERS
# ==============================================================================

print("=" * 65)
print(" EXPERIMENT 9: CELL COVERAGE, RADIUS & CELL SPLITTING ANALYSIS")
print("=" * 65)

Pt = ask("1. Base station transmit power Pt (dBm)", 43.0)        # 20 Watts = 43 dBm
Pmin = ask("2. Receiver sensitivity threshold Pmin (dBm)", -95.0) # Minimum signal
fc = ask("3. Carrier frequency fc (MHz)", 900.0)                 # GSM 900
n = ask("4. Path loss exponent n (3.0 to 4.0)", 3.8)            # Urban/Suburban
total_area = ask("5. Total service area (sq km)", 150.0)         # City area in km^2

# Validation
if Pt <= Pmin:
    raise ValueError("Transmit power Pt must be greater than receiver sensitivity Pmin.")
if fc <= 0 or n <= 0 or total_area <= 0:
    raise ValueError("Frequency, path loss exponent, and area must be positive.")


# ==============================================================================
# 3. CELL RADIUS AND COVERAGE CALCULATIONS (ORIGINAL CELL)
# ==============================================================================

# Reference distance d0 = 100 meters = 0.1 km
d0 = 0.1

# Free-space path loss at d0 using standard formula: PL0 = 20*log10(d0) + 20*log10(fc) + 32.44
PL0 = 20 * np.log10(d0) + 20 * np.log10(fc) + 32.44

# Maximum allowed path loss at cell boundary: PL_max = Pt - Pmin
PL_max = Pt - Pmin

# Solving PL_max = PL0 + 10*n*log10(R / d0) for cell radius R:
R = d0 * (10 ** ((PL_max - PL0) / (10 * n)))  # Radius in km

# Hexagonal cell coverage area: A = (3 * sqrt(3) / 2) * R^2 ≈ 2.598 * R^2
A_cell = 2.598 * (R ** 2)

# Number of cells required to cover total service area
num_cells = int(np.ceil(total_area / A_cell))


# ==============================================================================
# 4. CELL SPLITTING CALCULATIONS (MICROCELLS: R' = R / 2)
# ==============================================================================

# In cell splitting, radius is halved to handle high traffic density
R_split = R / 2.0
A_split = 2.598 * (R_split ** 2)
num_cells_split = int(np.ceil(total_area / A_split))

# Power reduction: To maintain same boundary signal without creating interference:
# Pt_new = Pt - 10 * n * log10(R / R_split) = Pt - 10 * n * log10(2)
power_reduction_dB = 10 * n * np.log10(2)
Pt_split = Pt - power_reduction_dB

# Capacity gain factor
capacity_gain = A_cell / A_split  # exactly 4x


# ==============================================================================
# 5. DISPLAY NUMERICAL RESULTS
# ==============================================================================

print("\n" + "=" * 55)
print("             SUMMARY OF RESULTS")
print("=" * 55)
print(f"Path loss at reference d0 ({d0*1000:.0f} m) : {PL0:.2f} dB")
print(f"Maximum allowable path loss       : {PL_max:.2f} dB")
print("-" * 55)
print("--- [ORIGINAL MACROCELL] ---")
print(f"  * Cell Radius (R)               : {R:.3f} km")
print(f"  * Cell Coverage Area            : {A_cell:.3f} sq km")
print(f"  * Cells needed for {total_area} sq km  : {num_cells} cells")
print(f"  * Base Station Transmit Power   : {Pt:.2f} dBm")
print("-" * 55)
print("--- [AFTER CELL SPLITTING (R / 2)] ---")
print(f"  * New Cell Radius (R')          : {R_split:.3f} km (halved)")
print(f"  * New Coverage Area             : {A_split:.3f} sq km (1/4th)")
print(f"  * Cells needed for {total_area} sq km  : {num_cells_split} cells (4x)")
print(f"  * Required Transmit Power       : {Pt_split:.2f} dBm (reduced by {power_reduction_dB:.2f} dB)")
print(f"  * System Capacity Multiplier    : {capacity_gain:.1f}x Increase")
print("=" * 55)


# ==============================================================================
# 6. GRAPHICAL ANALYSIS & VISUALIZATION
# ==============================================================================

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# --- Plot 1: Received Signal Strength vs Distance ---
d = np.linspace(d0, R * 1.25, 400)

# Path loss and received power curves
Pr_orig = Pt - (PL0 + 10 * n * np.log10(d / d0))
Pr_split = Pt_split - (PL0 + 10 * n * np.log10(d / d0))

ax1.plot(d, Pr_orig, "b-", linewidth=2, label=f"Original Cell (Pt = {Pt:.0f} dBm)")
ax1.plot(d, Pr_split, "g--", linewidth=2, label=f"Split Cell (Pt = {Pt_split:.1f} dBm)")
ax1.axhline(Pmin, color="red", linestyle=":", linewidth=1.5, label=f"Sensitivity Pmin ({Pmin:.0f} dBm)")

# Mark radii on plot
ax1.axvline(R, color="blue", linestyle="-.", alpha=0.7, label=f"Original Radius R ({R:.2f} km)")
ax1.axvline(R_split, color="green", linestyle="-.", alpha=0.7, label=f"Split Radius R/2 ({R_split:.2f} km)")

ax1.set_xlabel("Distance from Base Station (km)", fontsize=10)
ax1.set_ylabel("Received Signal Power Pr (dBm)", fontsize=10)
ax1.set_title("Cell Coverage vs Distance", fontsize=11, fontweight="bold")
ax1.set_ylim(Pmin - 15, Pt + 5)
ax1.grid(True, linestyle="--", alpha=0.6)
ax1.legend(loc="upper right", fontsize=8)

# --- Plot 2: Cell Splitting Geometry (Hexagonal Cells) ---
def plot_hexagon(ax, cx, cy, rad, color, label=None, linestyle="-", fill=False):
    angles = np.linspace(0, 2 * np.pi, 7)
    x = cx + rad * np.cos(angles)
    y = cy + rad * np.sin(angles)
    ax.plot(x, y, color=color, linewidth=2, linestyle=linestyle, label=label)
    if fill:
        ax.fill(x, y, color=color, alpha=0.08)

# Draw original macrocell (Radius R)
plot_hexagon(ax2, 0, 0, R, color="blue", label=f"Original Cell (Radius R = {R:.2f} km)", fill=True)
ax2.plot(0, 0, "b^", markersize=9, label="Original Base Station")

# Draw split microcells (Radius R/2) inside the macrocell
# Center microcell
plot_hexagon(ax2, 0, 0, R_split, color="green", linestyle="--", label=f"Split Microcell (Radius R/2 = {R_split:.2f} km)")
ax2.plot(0, 0, "g.", markersize=8)

# Surrounding 6 microcells at distance sqrt(3) * R_split
dist_split = np.sqrt(3) * R_split
for i in range(6):
    angle = np.pi / 6 + i * (np.pi / 3)
    sx = dist_split * np.cos(angle)
    sy = dist_split * np.sin(angle)
    plot_hexagon(ax2, sx, sy, R_split, color="green", linestyle="--")
    ax2.plot(sx, sy, "g.", markersize=8)

ax2.set_title("Hexagonal Cell Splitting Geometry", fontsize=11, fontweight="bold")
ax2.set_xlabel("East-West Distance (km)", fontsize=10)
ax2.set_ylabel("North-South Distance (km)", fontsize=10)
ax2.set_aspect("equal")
ax2.grid(True, linestyle="--", alpha=0.4)
ax2.legend(loc="upper right", fontsize=8)

plt.tight_layout()
plt.show()
