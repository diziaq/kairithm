// Hand-built SVG. No chart library, because the repository has no build step and no browser
// dependencies, and three chart forms do not justify introducing either.
//
// Three forms, each picked from the job its data does:
//
//   range     one headline value on a fixed 0-100 scale        -> a position track, not a bar chart
//   gaps      how far each topic sat above or below its level  -> diverging bars, blue <-> red
//   matrix    how many answers landed in each level/band cell  -> heatmap, one hue, more-is-darker
//
// Colours come from the palette slots defined in style.css under `.viz`, which are validated
// against this application's own light and dark surfaces. Marks carry colour; text never does.
// Every chart has a table twin next to it, so no value is reachable only by hovering.

import { clear, make } from "./dom.js";

const NS = "http://www.w3.org/2000/svg";

const WIDTH = 720;
const BAR_HEIGHT = 16; // <= 24, so the row keeps some air
const ROW_HEIGHT = 26;
const CORNER = 4; // rounded data-end, square at the baseline
const RING = 2; // surface ring / surface gap
const TIP_LABEL = 40; // room reserved at a bar tip for its own value label

export function node(tag, attrs = {}, text) {
  const element = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value !== null && value !== undefined) element.setAttribute(key, String(value));
  }
  if (text !== undefined) element.textContent = text;
  return element;
}

function root(height, label) {
  const element = node("svg", {
    viewBox: `0 0 ${WIDTH} ${height}`,
    width: "100%",
    height,
    class: "viz",
    role: "img",
    "aria-label": label,
    preserveAspectRatio: "xMinYMin meet",
  });
  element.style.maxWidth = `${WIDTH}px`;
  return element;
}

// --- the shared hover layer ------------------------------------------------------------------

let tip = null;

function tooltip() {
  if (!tip) {
    tip = make("div", { className: "viz-tip hidden" });
    document.body.appendChild(tip);
  }
  return tip;
}

function hoverable(shape, text) {
  // The hit target is the mark plus its surface gap, never the mark alone.
  shape.addEventListener("mousemove", (event) => {
    const box = tooltip();
    box.textContent = text;
    box.classList.remove("hidden");
    box.style.left = `${event.clientX + 12}px`;
    box.style.top = `${event.clientY + 12}px`;
  });
  shape.addEventListener("mouseleave", () => tooltip().classList.add("hidden"));
  shape.setAttribute("tabindex", "0");
  shape.addEventListener("focus", () => {
    const box = tooltip();
    const rect = shape.getBoundingClientRect();
    box.textContent = text;
    box.classList.remove("hidden");
    box.style.left = `${rect.left}px`;
    box.style.top = `${rect.bottom + 6}px`;
  });
  shape.addEventListener("blur", () => tooltip().classList.add("hidden"));
  return shape;
}

// --- shapes --------------------------------------------------------------------------------

// Rounded on the data-end, square where it meets the baseline.
function barFrom(baseline, end, y, height, corner = CORNER) {
  const radius = Math.min(corner, Math.abs(end - baseline));
  if (radius <= 0) return `M${baseline},${y} H${baseline} V${y + height} H${baseline} Z`;
  if (end >= baseline) {
    return (
      `M${baseline},${y} H${end - radius} A${radius},${radius} 0 0 1 ${end},${y + radius} ` +
      `V${y + height - radius} A${radius},${radius} 0 0 1 ${end - radius},${y + height} ` +
      `H${baseline} Z`
    );
  }
  return (
    `M${baseline},${y} H${end + radius} A${radius},${radius} 0 0 0 ${end},${y + radius} ` +
    `V${y + height - radius} A${radius},${radius} 0 0 0 ${end + radius},${y + height} ` +
    `H${baseline} Z`
  );
}

// --- 1. the range ----------------------------------------------------------------------------

const ANCHORS = [
  [0, "weak"],
  [25, "junior"],
  [50, "mid"],
  [75, "senior"],
  [100, "lead"],
];

export function renderRangeTrack(container, score) {
  clear(container);
  if (score.value === null) return;

  const left = 20;
  const right = WIDTH - 20;
  const span = right - left;
  const y = 30;
  const track = 10;
  const at = (value) => left + (span * value) / 100;

  const svg = root(76, `Range ${score.value} of 100, reading as ${score.label}`);

  // Unfilled track: a lighter step of the fill's own ramp, so state reads across the whole bar.
  svg.appendChild(
    node("rect", { x: left, y, width: span, height: track, rx: track / 2, class: "viz-track" })
  );
  svg.appendChild(
    node("path", {
      d: barFrom(left, at(score.value), y, track, track / 2),
      class: "viz-fill-pos",
    })
  );

  for (const [value, label] of ANCHORS) {
    svg.appendChild(
      node("line", { x1: at(value), y1: y - 6, x2: at(value), y2: y + track + 6, class: "viz-grid" })
    );
    svg.appendChild(
      node(
        "text",
        { x: at(value), y: y + track + 20, class: "viz-axis", "text-anchor": "middle" },
        label
      )
    );
  }

  const marker = node("circle", { cx: at(score.value), cy: y + track / 2, r: 6, class: "viz-marker" });
  svg.appendChild(hoverable(marker, `${score.value} of 100 — reads as ${score.label}`));
  svg.appendChild(
    node(
      "text",
      { x: at(score.value), y: y - 12, class: "viz-value", "text-anchor": "middle" },
      String(score.value)
    )
  );
  container.appendChild(svg);
}

// --- 2. the gaps -----------------------------------------------------------------------------

export function renderGapChart(container, rows) {
  clear(container);
  if (rows.length === 0) return;

  const gutter = 150;
  const plotLeft = gutter + 10;
  const plotRight = WIDTH - 44;
  const centre = (plotLeft + plotRight) / 2;
  const reach = Math.max(1, ...rows.map((row) => Math.abs(row.mean_gap)));
  // Leave room for the value label at the tip: a bar scaled to the full half-width would push
  // its own label into the topic label on the left, or off the canvas on the right.
  const scale = (plotRight - centre - TIP_LABEL) / reach;
  const top = 26;
  const height = top + rows.length * ROW_HEIGHT + 12;

  const svg = root(height, "How far each topic sat above or below the level its questions were set to");

  svg.appendChild(node("line", { x1: centre, y1: top - 8, x2: centre, y2: height - 8, class: "viz-axis-line" }));
  svg.appendChild(
    node("text", { x: centre, y: 14, class: "viz-axis", "text-anchor": "middle" }, "at the level asked")
  );

  rows.forEach((row, index) => {
    const y = top + index * ROW_HEIGHT;
    const gap = row.mean_gap;
    const end = centre + gap * scale;

    svg.appendChild(
      node(
        "text",
        { x: gutter, y: y + BAR_HEIGHT - 3, class: "viz-label", "text-anchor": "end" },
        row.name
      )
    );

    if (gap === 0) {
      // Nothing to draw a bar for. A tick at the baseline says "measured, and it landed here".
      const tick = node("rect", { x: centre - 1, y, width: 3, height: BAR_HEIGHT, class: "viz-zero" });
      svg.appendChild(hoverable(tick, `${row.name}: at the level asked (${row.asked} asked)`));
    } else {
      const bar = node("path", {
        d: barFrom(centre, end, y, BAR_HEIGHT),
        class: gap > 0 ? "viz-fill-pos" : "viz-fill-neg",
      });
      const direction = gap > 0 ? "above" : "below";
      svg.appendChild(
        hoverable(
          bar,
          `${row.name}: ${Math.abs(gap).toFixed(1)} ${Math.abs(gap) === 1 ? "band" : "bands"} ` +
            `${direction} the level asked · deepest ${row.deepest_band} · ${row.asked} asked`
        )
      );
    }

    // Direct label at the tip, so the value is never only in the tooltip.
    const outward = gap >= 0 ? 6 : -6;
    svg.appendChild(
      node(
        "text",
        {
          x: end + outward,
          y: y + BAR_HEIGHT - 3,
          class: "viz-value-small",
          "text-anchor": gap >= 0 ? "start" : "end",
        },
        gap > 0 ? `+${gap.toFixed(1)}` : gap.toFixed(1)
      )
    );
  });

  container.appendChild(svg);
  container.appendChild(gapLegend());
}

function gapLegend() {
  const row = make("p", { className: "viz-legend" });
  row.appendChild(make("span", { className: "viz-key viz-key-neg" }));
  row.appendChild(make("span", { text: " below the level asked " }));
  row.appendChild(make("span", { className: "viz-key viz-key-pos" }));
  row.appendChild(make("span", { text: " above it" }));
  return row;
}

// --- 3. the matrix ---------------------------------------------------------------------------

const RAMP_STEPS = 5;

export function renderBandMatrix(container, matrix, levels, bands) {
  clear(container);
  if (matrix.length === 0) return;

  const gutter = 90;
  const cellW = 88;
  const cellH = 34;
  const top = 34;
  const counts = new Map(matrix.map((cell) => [`${cell.level}:${cell.band}`, cell.count]));
  const busiest = Math.max(...matrix.map((cell) => cell.count));
  const height = top + levels.length * cellH + 10;

  const svg = root(height, "How many answers landed in each question-level and assigned-band pair");

  bands.forEach((band, column) => {
    svg.appendChild(
      node(
        "text",
        { x: gutter + column * cellW + cellW / 2, y: 20, class: "viz-axis", "text-anchor": "middle" },
        band
      )
    );
  });

  levels.forEach((level, rowIndex) => {
    const y = top + rowIndex * cellH;
    svg.appendChild(
      node("text", { x: gutter - 12, y: y + cellH / 2 + 4, class: "viz-label", "text-anchor": "end" }, level)
    );

    bands.forEach((band, column) => {
      const count = counts.get(`${level}:${band}`) || 0;
      const x = gutter + column * cellW;
      // The 2px inset is the surface gap doing the separating; no borders are drawn on marks.
      const cell = node("rect", {
        x: x + RING / 2,
        y: y + RING / 2,
        width: cellW - RING,
        height: cellH - RING,
        rx: 3,
        class: count === 0 ? "viz-cell-empty" : `viz-cell viz-step-${step(count, busiest)}`,
      });
      svg.appendChild(
        hoverable(
          cell,
          count === 0
            ? `no ${band} answer to a ${level} question`
            : `${count} ${band} answer(s) to ${level} question(s)`
        )
      );
      if (count > 0) {
        svg.appendChild(
          node(
            "text",
            {
              x: x + cellW / 2,
              y: y + cellH / 2 + 4,
              "text-anchor": "middle",
              class: step(count, busiest) >= 4 ? "viz-cell-text-high" : "viz-cell-text-low",
            },
            String(count)
          )
        );
      }
    });
  });

  container.appendChild(svg);
  container.appendChild(
    make("p", {
      className: "viz-legend",
      text: "Row: the level the question was set to. Column: the band you assigned. Darker means more answers.",
    })
  );
}

function step(count, busiest) {
  if (busiest <= 1) return 3;
  return Math.max(1, Math.ceil((count / busiest) * RAMP_STEPS));
}

export function clearTooltip() {
  if (tip) tip.classList.add("hidden");
}
