"""
Experiment 4: GSM Location Update & Call Setup Simulation (HLR / VLR)
---------------------------------------------------------------------
This program simulates:
  1. HLR (Home Location Register) and VLR (Visitor Location Register) databases.
  2. Location Update procedure when a Mobile Station (MS) roams across Location Areas (LAs).
  3. Visual map of Location Areas and subscriber movement.
  4. Sequence diagram of GSM signaling messages during Location Update.
  5. Sequence diagram of Call Setup (Mobile-Originated or Mobile-Terminated).
"""

import ast
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# ==============================================================================
# 1. HELPER FUNCTIONS FOR USER INPUT & DISPLAY
# ==============================================================================

def ask(prompt, default):
    """
    Prompt the user for input with a default fallback.
    Supports integers, floats, and Python lists (e.g. [1, 2, 3, 1] or 1, 2, 3, 1).
    """
    raw = input(f"{prompt} [default {default}]: ").strip()
    if not raw:
        return default

    # If the default is a list, allow entering with or without square brackets
    if isinstance(default, list):
        if not raw.startswith("["):
            raw = f"[{raw}]"

    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        print("  Invalid input format. Using default value.")
        return default


def showdb(imsi, msisdn, serving, vlr):
    """
    Display current contents of HLR and VLR databases.
      - HLR stores permanent subscriber profiles and their current serving LA.
      - VLR stores temporary records of subscribers currently in its area.
    """
    print("\n--- HLR (Home Location Register) Database ---")
    print(f"{'MS':<6}{'IMSI':<18}{'MSISDN':<18}{'Current VLR/LA':<14}")
    print("-" * 56)

    for k in range(len(imsi)):
        print(
            f"{k + 1:<6}"
            f"{imsi[k]:<18}"
            f"{msisdn[k]:<18}"
            f"LA-{serving[k]:<10}"
        )

    print("\n--- VLR (Visitor Location Register) Databases ---")
    for k, subscribers in enumerate(vlr, start=1):
        if subscribers:
            names = ", ".join(f"MS-{sub}" for sub in subscribers)
        else:
            names = "(empty)"
        print(f"  VLR-{k} (LA-{k}): {names}")


# ==============================================================================
# 2. SEQUENCE DIAGRAM VISUALIZER
# ==============================================================================

def drawseq(entities, messages, title):
    """
    Draw a UML-style sequence diagram using Matplotlib.
      - entities: List of network element names (vertical lifelines).
      - messages: List of tuples (source_index, dest_index, message_text).
    """
    n = len(entities)
    k = len(messages)

    # Dynamic figure dimensions based on number of columns and message count
    fig, ax = plt.subplots(
        figsize=(max(10, 1.5 * n + 1.5), max(6, 0.35 * k + 2))
    )

    # Step A: Draw vertical dashed lifeline for each network entity
    for e, entity in enumerate(entities, start=1):
        ax.plot([e, e], [0, -(k + 1)], color="gray", linestyle="--", linewidth=0.8)
        ax.text(
            e, 0.45, entity,
            ha="center", va="bottom",
            fontweight="bold", fontsize=9
        )

    # Step B: Draw horizontal signaling arrows and message descriptions
    for j, (source, destination, message) in enumerate(messages, start=1):
        y = -j  # Each message sits at y = -1, -2, -3, ...

        # Arrow from sender column to receiver column
        ax.annotate(
            "",
            xy=(destination, y),
            xytext=(source, y),
            arrowprops=dict(
                arrowstyle="->",
                color="navy",
                linewidth=1.2
            )
        )

        # Message text positioned at the center of the arrow
        midpoint = (source + destination) / 2
        ax.text(
            midpoint, y + 0.16,
            f"{j}. {message}",
            ha="center", va="bottom",
            fontsize=8,
            color="black"
        )

    # Step C: Configure plot aesthetics
    ax.set_xlim(0.4, n + 0.6)
    ax.set_ylim(-(k + 1), 1)
    ax.set_title(title, pad=20, fontsize=11, fontweight="bold")
    ax.axis("off")

    fig.tight_layout()
    plt.show()


# ==============================================================================
# 3. MAIN SIMULATION
# ==============================================================================

def main():
    print("=" * 60)
    print("   GSM HLR/VLR LOCATION UPDATE & CALL SETUP SIMULATION")
    print("=" * 60)

    # --- Step 1: User Inputs ---
    nLA = int(ask("1. Number of location areas (LAs)", 3))
    nSub = int(ask("2. Number of mobile subscribers", 4))

    if nLA < 1 or nSub < 1:
        raise ValueError("Location areas and subscribers must both be at least 1.")

    # Default initial location: evenly distributed across LAs (e.g. [1, 2, 3, 1])
    default_la = [(k % nLA) + 1 for k in range(nSub)]
    laInit = ask("3. Initial LA for each subscriber (list)", default_la)

    if not isinstance(laInit, list) or len(laInit) != nSub:
        raise ValueError(f"Initial LA input must be a list of length {nSub}.")

    laInit = [int(x) for x in laInit]
    if any(la < 1 or la > nLA for la in laInit):
        raise ValueError(f"Every initial LA must be between 1 and {nLA}.")

    mover = int(ask("4. Index of the moving subscriber (e.g. 1 for MS-1)", 1))
    if mover < 1 or mover > nSub:
        raise ValueError(f"Moving subscriber index must be between 1 and {nSub}.")

    # Default destination LA is the next consecutive location area
    default_dest = (laInit[mover - 1] % nLA) + 1
    laDest = int(ask(f"5. Destination LA of MS-{mover}", default_dest))
    if laDest < 1 or laDest > nLA:
        raise ValueError(f"Destination LA must be between 1 and {nLA}.")

    callType = int(ask("6. Call type (1 = Mobile Originated, 2 = Mobile Terminated)", 2))
    if callType not in (1, 2):
        raise ValueError("Call type must be either 1 or 2.")

    # --- Step 2: Generate Subscriber Identifiers (IMSI and MSISDN) ---
    # IMSI: International Mobile Subscriber Identity (Internal SIM ID: MCC+MNC+MSIN)
    # MSISDN: Mobile Station International Subscriber Directory Number (Dialed phone number)
    imsi = [f"47001{1000 + k:010d}" for k in range(1, nSub + 1)]
    msisdn = [f"+88017{10000000 + 137 * k:08d}" for k in range(1, nSub + 1)]

    # Serving LA tracking list (one entry per subscriber)
    serving = laInit.copy()

    # VLR tracking list (list of subscriber IDs currently in each LA)
    vlr = [[] for _ in range(nLA)]
    for sub_id, la in enumerate(serving, start=1):
        vlr[la - 1].append(sub_id)

    # --- Step 3: Display Databases Before Movement ---
    print("\n" + "=" * 50)
    print("      DATABASE STATE BEFORE LOCATION UPDATE")
    print("=" * 50)
    showdb(imsi, msisdn, serving, vlr)

    # --- Step 4: Perform Location Update ---
    src = serving[mover - 1]  # Source LA
    dst = laDest              # Destination LA

    if src != dst:
        # Subscriber has crossed into a new Location Area:
        vlr[src - 1].remove(mover)    # Remove MS from old VLR
        vlr[dst - 1].append(mover)    # Add MS to new VLR
        serving[mover - 1] = dst      # Update HLR pointer to new LA/VLR

        print(f"\n[EVENT] MS-{mover} moved from LA-{src} to LA-{dst}.")
        print("        -> HLR pointer updated, old VLR purged, new VLR registered.")
    else:
        print(f"\n[EVENT] MS-{mover} remains in LA-{src}. No location update needed.")

    # --- Step 5: Display Databases After Movement ---
    print("\n" + "=" * 50)
    print("      DATABASE STATE AFTER LOCATION UPDATE")
    print("=" * 50)
    showdb(imsi, msisdn, serving, vlr)

    # --- Step 6: 2D Spatial Visualization (LAs and MS Movement) ---
    fig, ax = plt.subplots(figsize=(10, 4))

    # Draw each Location Area as a rectangle box
    for k in range(1, nLA + 1):
        ax.add_patch(
            Rectangle(
                (k - 1, 0), 1, 1,
                facecolor="#dbeafe",
                edgecolor="#1d4ed8",
                linewidth=1.8
            )
        )
        ax.text(
            k - 0.5, 1.07,
            f"LA-{k}\n(MSC/VLR-{k})",
            ha="center", fontweight="bold", fontsize=9, color="#1e3a8a"
        )

    # Place subscribers inside their initial location areas
    # Small formula (k * 0.37) % 1 is just deterministic jitter to scatter dots inside the box
    mover_x = mover_y = None

    for k in range(1, nSub + 1):
        la = laInit[k - 1]
        px = (la - 1) + 0.2 + 0.6 * ((k * 0.37) % 1)
        py = 0.2 + 0.6 * ((k * 0.61) % 1)

        if k == mover:
            # Moving subscriber highlighted as red square
            ax.plot(px, py, "s", color="red", markersize=9, label=f"Moving MS (MS-{mover})")
            mover_x, mover_y = px, py
        else:
            # Stationary subscribers shown as black dots
            ax.plot(px, py, "o", color="black", markersize=6)

        ax.text(px + 0.03, py + 0.03, f"MS-{k}", fontsize=8, fontweight="bold")

    # If moving to a new LA, draw a red arrow showing the trajectory
    if src != dst and mover_x is not None:
        shift_x = dst - src
        ax.annotate(
            "",
            xy=(mover_x + shift_x, mover_y),
            xytext=(mover_x, mover_y),
            arrowprops=dict(
                arrowstyle="->",
                color="red",
                linewidth=2.5,
                shrinkA=5,
                shrinkB=5
            )
        )
        ax.text(
            mover_x + shift_x / 2, mover_y + 0.12,
            f"MS-{mover} Roaming",
            ha="center", color="red", fontsize=8, fontweight="bold"
        )

    ax.set_xlim(-0.1, nLA + 0.1)
    ax.set_ylim(-0.1, 1.35)
    ax.set_title("Location Area Layout and Subscriber Roaming", fontsize=11, fontweight="bold")
    ax.axis("off")
    fig.tight_layout()
    plt.show()

    # --- Step 7: Sequence Diagram for GSM Location Update Procedure ---
    if src != dst:
        entities = [
            "MS",
            "BTS/BSC",
            f"MSC/VLR-{dst}\n(New)",
            "HLR",
            f"MSC/VLR-{src}\n(Old)"
        ]

        messages = [
            (1, 2, "Channel Request (RACH)"),
            (2, 1, "Immediate Assignment (AGCH)"),
            (1, 3, "Location Updating Request (TMSI / Old LAI)"),
            (3, 5, "Send Identification (Old TMSI)"),
            (5, 3, "Identification Response (IMSI, Auth Sets)"),
            (3, 1, "Authentication Request (RAND)"),
            (1, 3, "Authentication Response (SRES)"),
            (3, 4, "Update Location (IMSI, New VLR No.)"),
            (4, 5, "Cancel Location (IMSI)"),
            (5, 4, "Cancel Location Ack"),
            (4, 3, "Insert Subscriber Data (Profile)"),
            (3, 4, "Insert Subscriber Data Ack"),
            (4, 3, "Update Location Ack"),
            (3, 1, "Location Updating Accept (New TMSI)"),
            (1, 3, "TMSI Reallocation Complete"),
            (3, 1, "Channel Release")
        ]

        drawseq(
            entities, messages,
            f"GSM Location Update Signaling Flow: MS-{mover} from LA-{src} to LA-{dst}"
        )

    # --- Step 8: Sequence Diagram for Call Setup ---
    if callType == 1:
        # Mobile-Originated Call (MOC): Mobile user initiates a call to PSTN
        entities = [
            "MS",
            "BTS/BSC",
            f"MSC/VLR-{dst}",
            "GMSC/PSTN",
            "Called Party"
        ]

        messages = [
            (1, 2, "Channel Request (RACH)"),
            (2, 1, "Immediate Assignment (AGCH)"),
            (1, 3, "CM Service Request"),
            (3, 1, "Authentication Request"),
            (1, 3, "Authentication Response"),
            (3, 1, "Ciphering Mode Command"),
            (1, 3, "Setup (Called Number / MSISDN)"),
            (3, 1, "Call Proceeding"),
            (3, 2, "Assignment Request (Traffic Channel TCH)"),
            (2, 3, "Assignment Complete"),
            (3, 4, "IAM (Initial Address Message - ISUP)"),
            (4, 5, "Ringing the Called Party"),
            (4, 3, "ACM (Address Complete Message)"),
            (3, 1, "Alerting (Ringback Tone)"),
            (5, 4, "Called Party Answers"),
            (4, 3, "ANM (Answer Message)"),
            (3, 1, "Connect"),
            (1, 3, "Connect Acknowledge (Call Active)")
        ]

        drawseq(
            entities, messages,
            f"GSM Mobile-Originated Call Setup (MOC): MS-{mover} Calling"
        )

    else:
        # Mobile-Terminated Call (MTC): External caller places call to roaming MS
        entities = [
            "Calling Party",
            "GMSC",
            "HLR",
            f"MSC/VLR-{dst}",
            "BTS/BSC",
            "MS"
        ]

        messages = [
            (1, 2, "IAM (Dialed MSISDN)"),
            (2, 3, "Send Routing Information (MSISDN)"),
            (3, 4, "Provide Roaming Number (IMSI)"),
            (4, 3, "MSRN (Mobile Station Roaming Number)"),
            (3, 2, "Send Routing Info Ack (MSRN)"),
            (2, 4, "IAM (Forward Call using MSRN)"),
            (4, 5, "Paging (All Cells in LA)"),
            (5, 6, "Paging Request (PCH)"),
            (6, 5, "Channel Request (RACH)"),
            (5, 6, "Immediate Assignment (AGCH)"),
            (6, 4, "Paging Response"),
            (4, 6, "Authentication & Ciphering"),
            (4, 6, "Setup"),
            (6, 4, "Call Confirmed"),
            (4, 5, "Assignment Request (Traffic Channel TCH)"),
            (5, 4, "Assignment Complete"),
            (6, 4, "Alerting (Mobile Phone Rings)"),
            (4, 2, "ACM (Address Complete)"),
            (2, 1, "ACM (Ringback to Caller)"),
            (6, 4, "Connect (User Answers)"),
            (4, 2, "ANM (Answer Message)"),
            (2, 1, "ANM (Call Connected)")
        ]

        drawseq(
            entities, messages,
            f"GSM Mobile-Terminated Call Setup (MTC): Call to MS-{mover} in LA-{dst}"
        )


if __name__ == "__main__":
    main()
