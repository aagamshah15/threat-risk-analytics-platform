from matplotlib import pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def box(ax, x, y, w, h, text):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1
    )
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=10)

def arrow(ax, x1, y1, x2, y2, text=None):
    arr = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->", mutation_scale=12, linewidth=1)
    ax.add_patch(arr)
    if text:
        ax.text((x1+x2)/2, (y1+y2)/2 + 0.02, text, ha="center", va="bottom", fontsize=9)

def main():
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()

    # Layers
    box(ax, 0.05, 0.70, 0.25, 0.20, "Public Sources\n\n• CISA KEV (CSV)\n• URLhaus (feed)")
    box(ax, 0.37, 0.74, 0.25, 0.14, "ELT (Python)\nBatch job")
    box(ax, 0.70, 0.70, 0.25, 0.20, "MinIO (S3)\nBronze Lake\nParquet snapshots")

    box(ax, 0.70, 0.40, 0.25, 0.20, "Postgres\nRaw schema\nraw.* landing tables")
    box(ax, 0.37, 0.40, 0.25, 0.20, "dbt Core\nTransforms + Tests")
    box(ax, 0.05, 0.40, 0.25, 0.20, "Postgres\nStaging + Marts\nstaging.*, marts.*")

    box(ax, 0.37, 0.10, 0.25, 0.16, "Dashboards (Phase 2)\nTableau/Metabase/etc")

    # Arrows
    arrow(ax, 0.30, 0.80, 0.37, 0.80, "extract")
    arrow(ax, 0.62, 0.81, 0.70, 0.80, "land bronze")
    arrow(ax, 0.50, 0.74, 0.83, 0.60, "load raw")
    arrow(ax, 0.70, 0.50, 0.62, 0.50, "dbt reads raw")
    arrow(ax, 0.37, 0.50, 0.30, 0.50, "staging/marts")
    arrow(ax, 0.50, 0.40, 0.50, 0.26, "curated tables")

    ax.text(0.5, 0.95, "Threat & Risk Analytics Platform — Phase 1 Architecture",
            ha="center", va="center", fontsize=14)

    fig.savefig("docs/architecture.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()

