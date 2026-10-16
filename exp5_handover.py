import numpy as np
import matplotlib.pyplot as plt


def ask(prompt, default):
    """Read numeric input, falling back to the default."""
    value = input(f"{prompt} [default {default}]: ").strip()
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        print("Invalid input. Using default:", default)
        return default


# 1. INPUT PARAMETERS
D = ask("Distance between the two base stations (km)", 2)
fc = ask("Carrier frequency (MHz)", 900)
Pt = ask("BS transmit power (dBm)", 43)
n = ask("Path loss exponent", 3.5)
sigma = ask("Shadowing standard deviation (dB)", 4)
dcorr = ask("Shadowing decorrelation distance (m)", 50)
H = ask("Handover hysteresis margin (dB)", 5)
Smin = ask("Minimum usable signal (dBm)", -100)
vkmh = ask("Mobile speed (km/h)", 60)
Ts = ask("Measurement interval (s)", 0.5)
seed = int(ask("Random seed", 1))

if D <= 0 or fc <= 0 or n <= 0 or dcorr <= 0 or Ts <= 0:
    raise ValueError("Distance, frequency, path-loss exponent, "
                     "decorrelation distance, and Ts must be positive.")

if sigma < 0 or vkmh < 0 or H < 0:
    raise ValueError("Sigma, speed, and hysteresis must be non-negative.")

rng = np.random.default_rng(seed)

# 2. DISTANCE AND PATH LOSS
d0 = 0.1  # Reference distance in km = 100 m

PL0 = 20 * np.log10(d0) + 20 * np.log10(fc) + 32.44

v = vkmh / 3.6
stepM = v * Ts
step_km = stepM / 1000

# Generate mobile positions
if step_km > 0:
    x = np.arange(0, D + step_km * 0.5, step_km)
    x = x[x <= D + 1e-12]

    if len(x) == 0 or x[-1] < D - 1e-12:
        x = np.append(x, D)
else:
    x = np.array([0.0])

K = len(x)

# 3. CORRELATED SHADOW FADING
a = np.exp(-stepM / dcorr)

s1 = np.zeros(K)
s2 = np.zeros(K)

s1[0] = sigma * rng.standard_normal()
s2[0] = sigma * rng.standard_normal()

for k in range(1, K):
    s1[k] = (
        a * s1[k - 1]
        + np.sqrt(1 - a**2) * sigma * rng.standard_normal()
    )

    s2[k] = (
        a * s2[k - 1]
        + np.sqrt(1 - a**2) * sigma * rng.standard_normal()
    )

# 4. RECEIVED SIGNAL STRENGTH
m1 = Pt - PL0 - 10 * n * np.log10(np.maximum(x, d0) / d0)

m2 = Pt - PL0 - 10 * n * np.log10(
    np.maximum(D - x, d0) / d0
)

P1 = m1 + s1
P2 = m2 + s2

# 5. HANDOVER WITHOUT HYSTERESIS
serveA = np.where(P2 > P1, 2, 1)

# 6. HANDOVER WITH HYSTERESIS
serveH = np.zeros(K, dtype=int)
serving = 1

for k in range(K):
    if serving == 1 and P2[k] > P1[k] + H:
        serving = 2

    elif serving == 2 and P1[k] > P2[k] + H:
        serving = 1

    serveH[k] = serving

# Detect handover events
hoA = np.flatnonzero(np.diff(serveA) != 0) + 1
hoH = np.flatnonzero(np.diff(serveH) != 0) + 1

# Serving base station signal
PsA = np.where(serveA == 1, P1, P2)
PsH = np.where(serveH == 1, P1, P2)

# 7. DISPLAY RESULTS
print(f"\nPath loss at d0 = {d0:.1f} km        : {PL0:.2f} dB")
print(f"Ideal handover point (no fading): {D / 2:.3f} km")
print(f"Handovers, no hysteresis        : {len(hoA)}")
print(f"Handovers, {H:.1f} dB hysteresis    : {len(hoH)}")
print(f"Outage samples, no hysteresis   : "
      f"{100 * np.mean(PsA < Smin):.2f} %")
print(f"Outage samples, hysteresis      : "
      f"{100 * np.mean(PsH < Smin):.2f} %")

if len(hoH) > 0:
    print(f"First hysteresis handover at    : {x[hoH[0]]:.3f} km")

# 8. PLOT RESULTS
fig, axes = plt.subplots(3, 1, figsize=(12, 10))
fig.patch.set_facecolor("white")

# Plot 1: Received signal strengths
ax = axes[0]

ax.plot(x, P1, "b", linewidth=1.1, label="BS1 RSS")
ax.plot(x, P2, "r", linewidth=1.1, label="BS2 RSS")
ax.plot(x, m1, "b--", label="BS1 mean")
ax.plot(x, m2, "r--", label="BS2 mean")
ax.axhline(Smin, color="black", linestyle=":",
           linewidth=1.3, label="Minimum signal")

for i, k in enumerate(hoH):
    ax.axvline(
        x[k],
        color="green",
        linewidth=1.2,
        label="Hysteresis handover" if i == 0 else None
    )

ax.grid(True)
ax.legend(loc="upper right")
ax.set_xlabel("Distance from BS1 (km)")
ax.set_ylabel("RSS (dBm)")
ax.set_title("Received signal strength from both base stations")

# Plot 2: Serving base station
ax = axes[1]

ax.step(x, serveA, where="post", color="magenta",
        linewidth=1.3, label="No hysteresis")

ax.step(x, serveH + 0.05, where="post", color="black",
        linewidth=1.3, label=f"Hysteresis {H:.1f} dB")

ax.set_ylim(0.7, 2.4)
ax.set_yticks([1, 2])
ax.set_yticklabels(["BS1", "BS2"])
ax.grid(True)
ax.legend(loc="upper right")
ax.set_xlabel("Distance from BS1 (km)")
ax.set_ylabel("Serving BS")
ax.set_title(
    f"Serving base station ({len(hoA)} vs {len(hoH)} handovers)"
)

# Plot 3: Signal received from the serving base station
ax = axes[2]

ax.plot(x, PsA, "m", label="No hysteresis")
ax.plot(x, PsH, "k", linewidth=1.2, label="With hysteresis")
ax.axhline(Smin, color="red", linestyle=":",
           linewidth=1.3, label="Minimum signal")

ax.grid(True)
ax.legend(loc="upper right")
ax.set_xlabel("Distance from BS1 (km)")
ax.set_ylabel("RSS of serving BS (dBm)")
ax.set_title("Signal level seen by the mobile")

plt.tight_layout()
plt.show()
