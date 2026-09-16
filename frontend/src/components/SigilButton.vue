<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import type { ArcaneButtonProps } from "@/types/button";
import ArcaneFilterDefs from "./ArcaneFilterDefs.vue";

defineOptions({ inheritAttrs: false });

withDefaults(defineProps<ArcaneButtonProps>(), { type: "button", disabled: false });

const buttonEl = ref<HTMLButtonElement | null>(null);
const emberLayerEl = ref<SVGGElement | null>(null);

const reduceMotion =
  typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// --- Match every sigil line's width to the label wrap's border ---
// The border is authored as a real CSS px width (--sigil-border-width, set
// on .sigil-label-wrap), but each SVG line's stroke-width lives in that
// element's own LOCAL coordinate space — and the ring/circles/triangle and
// the six zodiac glyphs each sit under a *different* nested scale transform
// (the glyphs were traced at a much larger source scale than the ring), so
// one shared stroke-width value can't render as the same on-screen width
// for all of them. Instead, every line's own screen CTM is read individually
// to get its actual local-unit-to-px ratio, and the border's px width is
// divided by that to get the exact local stroke-width *that element* needs
// to render at the same width as the border — regardless of how deeply or
// differently it's nested.
function syncStrokeWidthToBorder() {
  const btn = buttonEl.value;
  if (!btn) return;
  const labelWrap = btn.querySelector<HTMLElement>(".sigil-label-wrap");
  if (!labelWrap) return;

  const borderWidthPx = parseFloat(
    getComputedStyle(labelWrap).getPropertyValue("--sigil-border-width"),
  );
  if (!borderWidthPx) return;

  const lines = btn.querySelectorAll<SVGGraphicsElement>(".sigil-line, .sigil-glyph-line");
  lines.forEach((line) => {
    const ctm = line.getScreenCTM();
    if (!ctm) return;
    const pxPerLocalUnit = Math.hypot(ctm.a, ctm.b);
    if (!pxPerLocalUnit) return;
    const matchedStrokeUnits = borderWidthPx / pxPerLocalUnit;
    line.style.strokeWidth = matchedStrokeUnits.toFixed(3);
  });
}

// Spawns short-lived SVG particles at random points sampled along the
// sigil's static (non-rotating) line elements — getPointAtLength gives an
// accurate point on the real stroke, not a guessed coordinate — then lets a
// CSS animation drift and fade each one before it's removed.
function emberSources(): SVGGeometryElement[] {
  const btn = buttonEl.value;
  if (!btn) return [];
  return Array.from(btn.querySelectorAll<SVGGeometryElement>(".sigil-fixed .sigil-line")).filter(
    (el) => typeof el.getTotalLength === "function",
  );
}

function spawnEmber() {
  const layer = emberLayerEl.value;
  const sources = emberSources();
  if (!layer || !sources.length) return;
  const el = sources[Math.floor(Math.random() * sources.length)]!;
  const len = el.getTotalLength();
  if (!len) return;
  const pt = el.getPointAtLength(Math.random() * len);

  const ember = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  ember.setAttribute("class", "ember");
  ember.setAttribute("cx", String(pt.x));
  ember.setAttribute("cy", String(pt.y));
  ember.setAttribute("r", (0.9 + Math.random() * 1.3).toFixed(2));
  ember.style.transformOrigin = `${pt.x}px ${pt.y}px`;

  const angle = Math.random() * Math.PI * 2;
  const dist = 7 + Math.random() * 16;
  const dx = Math.cos(angle) * dist;
  const dy = Math.sin(angle) * dist - 6; // upward drift, like heat rising
  ember.style.setProperty("--dx", `${dx.toFixed(2)}px`);
  ember.style.setProperty("--dy", `${dy.toFixed(2)}px`);
  const life = 650 + Math.random() * 650;
  ember.style.setProperty("--life", `${life.toFixed(0)}ms`);

  layer.appendChild(ember);
  setTimeout(() => ember.remove(), life + 60);
}

let emberTimer: ReturnType<typeof setInterval> | null = null;

function startEmbers() {
  if (reduceMotion || emberTimer) return;
  emberTimer = setInterval(spawnEmber, 75);
}

function stopEmbers() {
  if (emberTimer) {
    clearInterval(emberTimer);
    emberTimer = null;
  }
  emberLayerEl.value?.querySelectorAll(".ember").forEach((e) => e.remove());
}

onMounted(() => {
  syncStrokeWidthToBorder();

  const btn = buttonEl.value;
  if (!reduceMotion && btn) {
    btn.addEventListener("mouseenter", startEmbers);
    btn.addEventListener("mouseleave", stopEmbers);
    btn.addEventListener("focus", startEmbers);
    btn.addEventListener("blur", stopEmbers);
  }
});

onUnmounted(() => {
  stopEmbers();
  const btn = buttonEl.value;
  btn?.removeEventListener("mouseenter", startEmbers);
  btn?.removeEventListener("mouseleave", stopEmbers);
  btn?.removeEventListener("focus", startEmbers);
  btn?.removeEventListener("blur", stopEmbers);
});
</script>

<template>
  <ArcaneFilterDefs />

  <button ref="buttonEl" v-bind="$attrs" :type="type" :disabled="disabled" class="sigil-btn">
    <span class="sigil-glow"></span>
    <span class="sigil-burst"></span>

    <svg class="sigil-svg" viewBox="0 0 500 500" overflow="visible" aria-hidden="true">
      <g class="sigil-ink" transform="matrix(1,0,0,1,180,180)">
        <g class="sigil-fixed" transform="matrix(2.502433,0,0,2.502433,-105.170318,-105.170318)">
          <!-- fixed radial ticks -->
          <line class="sigil-line" x1="122.00" y1="70.00" x2="130.00" y2="70.00" />
          <line class="sigil-line" x1="115.03" y1="96.00" x2="121.96" y2="100.00" />
          <line class="sigil-line" x1="96.00" y1="115.03" x2="100.00" y2="121.96" />
          <line class="sigil-line" x1="70.00" y1="122.00" x2="70.00" y2="130.00" />
          <line class="sigil-line" x1="44.00" y1="115.03" x2="40.00" y2="121.96" />
          <line class="sigil-line" x1="24.97" y1="96.00" x2="18.04" y2="100.00" />
          <line class="sigil-line" x1="18.00" y1="70.00" x2="10.00" y2="70.00" />
          <line class="sigil-line" x1="24.97" y1="44.00" x2="18.04" y2="40.00" />
          <line class="sigil-line" x1="44.00" y1="24.97" x2="40.00" y2="18.04" />
          <line class="sigil-line" x1="70.00" y1="18.00" x2="70.00" y2="10.00" />
          <line class="sigil-line" x1="96.00" y1="24.97" x2="100.00" y2="18.04" />
          <line class="sigil-line" x1="115.03" y1="44.00" x2="121.96" y2="40.00" />
          <!-- outer + inner rings (fixed in the new sigil design) -->
          <circle class="sigil-line" cx="70" cy="70" r="60" />
          <circle class="sigil-line" cx="70" cy="70" r="52" />
        </g>

        <!-- rotating assembly: the three circles, the triangle that binds
             them, and the six zodiac glyphs, all pure line art -->
        <g class="sigil-ring">
          <g
            class="sigil-circles"
            transform="matrix(2.502433,0,0,2.502433,-105.170318,-105.170318)"
          >
            <circle class="sigil-line" cx="42.86" cy="54.33" r="6.5" />
            <circle class="sigil-line" cx="70" cy="101.33" r="6.5" />
            <circle class="sigil-line" cx="97.14" cy="54.33" r="6.5" />
          </g>

          <g
            class="sigil-triangle"
            transform="matrix(2.502433,0,0,2.502433,-105.170318,-105.170318)"
          >
            <path class="sigil-line" d="M70,36L40.56,87L99.44,87L70,36Z" />
          </g>

          <!-- taurus -->
          <g transform="matrix(-0.037966,-0.30921,0.30921,-0.037966,-341.797099,455.647029)">
            <g transform="matrix(1.229533,0,0,1.229533,-211.728317,-259.442153)">
              <circle
                class="sigil-glyph-line"
                cx="1040.486"
                cy="1159.44"
                r="27.098"
                style="stroke-width: 7.83px; stroke-linecap: butt; stroke-miterlimit: 1.5"
              />
            </g>
            <path
              class="sigil-glyph-line"
              d="M1007.006,1097.114C1012.064,1097.07 1026.809,1097.514 1031.274,1103.669C1039.903,1115.564 1040.709,1131.419 1067.584,1132.342C1094.458,1131.419 1095.265,1115.564 1103.894,1103.669C1108.358,1097.514 1123.104,1097.07 1128.161,1097.114"
              style="stroke-width: 9.63px; stroke-linecap: butt; stroke-miterlimit: 1.5"
            />
          </g>

          <!-- pisces -->
          <g transform="matrix(-0.248801,-0.187485,0.187485,-0.248801,-95.578619,384.636187)">
            <path
              class="sigil-glyph-line"
              d="M146.446,860.052C170.443,831.226 170.842,790.975 146.54,763.711"
              style="stroke-width: 9.63px; stroke-linecap: butt; stroke-miterlimit: 1.5"
            />
            <g transform="matrix(-1,0,0,1,366.72926,0)">
              <path
                class="sigil-glyph-line"
                d="M146.446,860.052C170.443,831.226 170.842,790.975 146.54,763.711"
                style="stroke-width: 9.63px; stroke-linecap: butt; stroke-miterlimit: 1.5"
              />
            </g>
            <path
              class="sigil-glyph-line"
              d="M139.423,811.881L227.253,811.881"
              style="stroke-width: 9.63px; stroke-linecap: butt; stroke-miterlimit: 1.5"
            />
          </g>

          <!-- sagittarius -->
          <g transform="matrix(-0.037966,0.30921,-0.30921,-0.037966,364.808669,-66.313091)">
            <path
              class="sigil-glyph-line"
              d="M504.786,613.164L594.458,523.146"
              style="
                stroke-width: 9.63px;
                stroke-linecap: butt;
                stroke-linejoin: round;
                stroke-miterlimit: 1.5;
              "
            />
            <path
              class="sigil-glyph-line"
              d="M513.199,567.367L550.504,604.907"
              style="
                stroke-width: 9.63px;
                stroke-linecap: butt;
                stroke-linejoin: round;
                stroke-miterlimit: 1.5;
              "
            />
            <path
              class="sigil-glyph-line"
              d="M546.976,523.477L594.458,523.146L594.291,571.66"
              style="stroke-width: 9.63px; stroke-linecap: butt; stroke-miterlimit: 1.5"
            />
          </g>

          <!-- aquarius -->
          <g transform="matrix(0.286767,-0.121725,0.121725,0.286767,-284.414832,-53.601228)">
            <path
              class="sigil-glyph-line"
              d="M828.428,530.368L850.514,504.292L871.35,529.48L892.247,504.024L913.35,529.48L934.113,504.158L955.949,530.149"
              style="
                stroke-width: 9.63px;
                stroke-linecap: butt;
                stroke-linejoin: round;
                stroke-miterlimit: 1.5;
              "
            />
            <g transform="matrix(1,0,0,1,-0,-50.160198)">
              <path
                class="sigil-glyph-line"
                d="M828.428,530.368L850.514,504.292L871.35,529.48L892.247,504.024L913.35,529.48L934.113,504.158L955.949,530.149"
                style="
                  stroke-width: 9.63px;
                  stroke-linecap: butt;
                  stroke-linejoin: round;
                  stroke-miterlimit: 1.5;
                "
              />
            </g>
          </g>

          <!-- leo -->
          <g transform="matrix(-0.248801,0.187485,-0.187485,-0.248801,647.715171,74.059696)">
            <path
              class="sigil-glyph-line"
              d="M1517.145,853.606C1514.525,861.105 1508.119,863.874 1503.602,863.897C1492.897,863.953 1483.343,856.182 1487.721,842.813C1489.98,835.915 1505.032,801.358 1507.32,793.057C1510.649,780.977 1503.489,759.905 1480.559,759.817C1474.879,759.795 1451.274,764.977 1454.371,790.822C1455.723,802.096 1462.637,814.366 1462.637,826.61"
              style="stroke-width: 9.63px; stroke-linecap: butt; stroke-miterlimit: 1.5"
            />
            <g transform="matrix(1.587301,0,0,1.587301,-814.024098,-455.611708)">
              <circle
                class="sigil-glyph-line"
                cx="1423.763"
                cy="807.8"
                r="10.534"
                style="stroke-width: 6.07px; stroke-linecap: butt; stroke-miterlimit: 1.5"
              />
            </g>
          </g>

          <!-- cancer -->
          <g transform="matrix(0.286767,0.121725,-0.121725,0.286767,-328.058068,-415.427995)">
            <g transform="matrix(1,0,0,1,0.065546,1.147228)">
              <path
                class="sigil-glyph-line"
                d="M1733.439,648.749C1772.765,679.247 1827.473,662.66 1836.434,642.195"
                style="stroke-width: 9.63px; stroke-linecap: butt; stroke-miterlimit: 1.5"
              />
            </g>
            <g transform="matrix(1.275183,0,0,1.275183,-464.227814,-158.301113)">
              <circle
                class="sigil-glyph-line"
                cx="1790.153"
                cy="620.462"
                r="16.284"
                style="stroke-width: 7.55px; stroke-linecap: butt; stroke-miterlimit: 1.5"
              />
            </g>
            <g transform="matrix(-1,0,0,-1,3569.938962,1239.847843)">
              <path
                class="sigil-glyph-line"
                d="M1733.439,648.749C1772.765,679.247 1827.473,662.66 1836.434,642.195"
                style="stroke-width: 9.63px; stroke-linecap: butt; stroke-miterlimit: 1.5"
              />
            </g>
            <g transform="matrix(-1.275183,0,0,-1.275183,4034.232322,1399.296185)">
              <circle
                class="sigil-glyph-line"
                cx="1790.153"
                cy="620.462"
                r="16.284"
                style="stroke-width: 7.55px; stroke-linecap: butt; stroke-miterlimit: 1.5"
              />
            </g>
          </g>
        </g>

        <g
          ref="emberLayerEl"
          class="sigil-embers"
          transform="matrix(2.502433,0,0,2.502433,-105.170318,-105.170318)"
        ></g>
      </g>
    </svg>

    <span class="sigil-label-wrap"
      ><span class="sigil-label"><slot /></span
    ></span>
  </button>
</template>

<style scoped>
.sigil-btn {
  position: relative;
  width: 312px;
  height: 312px;
  border: none;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    transform 0.2s ease,
    filter 0.3s ease;
}

.sigil-btn:disabled {
  cursor: default;
  opacity: 0.6;
}

.sigil-glow {
  position: absolute;
  inset: -28px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    var(--arcane-glow, rgba(142, 45, 226, 0.6)) 0%,
    transparent 68%
  );
  opacity: 0;
  filter: blur(1px);
  transition: opacity 0.5s ease;
  pointer-events: none;
}

.sigil-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: visible;
  /* Darkens into whatever's behind the button instead of sitting on top as
     flat color, so the linework reads as ink soaked into paper. Switched
     back to normal blending on hover/focus below — multiply can only ever
     darken, which would muddy the bright arcane glow the ignited state
     relies on. */
  mix-blend-mode: multiply;
}

.sigil-btn:hover:not(:disabled) .sigil-svg,
.sigil-btn:focus-visible:not(:disabled) .sigil-svg {
  mix-blend-mode: normal;
}

.sigil-svg .sigil-line {
  fill: none;
  stroke: var(--ink-soft, #6b5f4f);
  stroke-width: var(--sigil-stroke-width, 1.4);
  stroke-linecap: round;
  opacity: 0.8;
  transition:
    stroke 0.5s ease,
    filter 0.5s ease,
    opacity 0.5s ease;
}

/* The literal stroke-width on each glyph path (straight from sigil4.svg) is
   only the pre-JS fallback — syncStrokeWidthToBorder() overwrites it inline
   once mounted, per element, so every glyph ends up the same on-screen width
   as the ring hairlines and the label border despite sitting under a very
   different nested scale transform. This class only carries color/opacity. */
.sigil-svg .sigil-glyph-line {
  fill: none;
  stroke: var(--ink-soft, #6b5f4f);
  opacity: 0.8;
  transition:
    stroke 0.5s ease,
    filter 0.5s ease,
    opacity 0.5s ease;
}

.sigil-ring {
  transform-origin: 70px 70px;
}

.sigil-burst {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 4px solid var(--arcane-bright, #e3baff);
  opacity: 0;
  pointer-events: none;
}

.sigil-label-wrap {
  --sigil-border-width: 1px;
  position: relative;
  padding: 4.5px 10.5px;
  background-color: var(--page, #f4ecd8);
  border-radius: 6px;
  transition: background-color 0.6s ease;
}

.sigil-label-wrap::before {
  content: "";
  position: absolute;
  inset: 0;
  border: var(--sigil-border-width) solid var(--ink-soft, #6b5f4f);
  border-radius: 6px;
  opacity: 0.8;
  pointer-events: none;
  transition:
    border-color 0.5s ease,
    filter 0.5s ease,
    opacity 0.5s ease;
}

.sigil-label {
  position: relative;
  z-index: 2;
  font-family: "Comic Runes", Georgia, serif;
  font-weight: 400;
  font-size: 1.38rem;
  letter-spacing: 0.6px;
  color: var(--ink-soft, #6b5f4f);
  text-align: center;
  line-height: 1;
  white-space: nowrap;
  transition:
    color 0.5s ease,
    text-shadow 0.5s ease;
}

.sigil-btn:hover,
.sigil-btn:focus-visible {
  outline: none;
}

.sigil-btn:hover:not(:disabled) .sigil-glow,
.sigil-btn:focus-visible:not(:disabled) .sigil-glow {
  opacity: 1;
  animation: sigil-breathe 2.4s ease-in-out infinite;
}

.sigil-btn:hover:not(:disabled) .sigil-line,
.sigil-btn:focus-visible:not(:disabled) .sigil-line {
  stroke: var(--arcane-bright, #e3baff);
  opacity: 1;
}

.sigil-btn:hover:not(:disabled) .sigil-glyph-line,
.sigil-btn:focus-visible:not(:disabled) .sigil-glyph-line {
  stroke: var(--arcane-bright, #e3baff);
  opacity: 1;
}

.sigil-btn:hover:not(:disabled) .sigil-ink,
.sigil-btn:focus-visible:not(:disabled) .sigil-ink {
  filter: url(#arcane-waver) drop-shadow(0 0 4px var(--arcane, #8e2de2))
    drop-shadow(0 0 10px var(--arcane, #8e2de2));
}

.sigil-btn:hover:not(:disabled) .sigil-ring,
.sigil-btn:focus-visible:not(:disabled) .sigil-ring {
  animation: sigil-rotate 7s linear infinite;
}

.sigil-btn:hover:not(:disabled) .sigil-label-wrap,
.sigil-btn:focus-visible:not(:disabled) .sigil-label-wrap {
  background-color: transparent;
}

.sigil-btn:hover:not(:disabled) .sigil-label-wrap::before,
.sigil-btn:focus-visible:not(:disabled) .sigil-label-wrap::before {
  opacity: 0;
}

.sigil-btn:hover:not(:disabled) .sigil-label,
.sigil-btn:focus-visible:not(:disabled) .sigil-label {
  color: var(--arcane-ignited-text, #fff);
  text-shadow:
    0 0 4px var(--arcane-bright, #e3baff),
    0 0 10px var(--arcane, #8e2de2),
    0 0 18px var(--arcane-glow, rgba(142, 45, 226, 0.6));
}

.sigil-btn:active:not(:disabled) {
  transform: scale(0.97);
}

.sigil-btn:active:not(:disabled) .sigil-burst {
  animation: sigil-burst-anim 0.6s ease-out;
}

@keyframes sigil-breathe {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.15);
    opacity: 1;
  }
}

@keyframes sigil-rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes sigil-burst-anim {
  0% {
    opacity: 0.9;
    transform: scale(0.9);
  }
  100% {
    opacity: 0;
    transform: scale(1.7);
  }
}

@media (prefers-reduced-motion: reduce) {
  .sigil-btn:hover .sigil-glow,
  .sigil-btn:focus-visible .sigil-glow {
    animation: none;
  }
  .sigil-btn:hover .sigil-ring,
  .sigil-btn:focus-visible .sigil-ring {
    animation: none;
  }
  .sigil-btn:active .sigil-burst {
    animation: none;
    opacity: 0.6;
  }
  .sigil-btn:hover .sigil-ink,
  .sigil-btn:focus-visible .sigil-ink {
    filter: drop-shadow(0 0 4px var(--arcane, #8e2de2)) drop-shadow(0 0 10px var(--arcane, #8e2de2));
  }
}
</style>

<style>
/* Embers are appended as raw SVG nodes at runtime (see spawnEmber() above),
   not compiled from this component's template, so Vue's scoped-style
   attribute is never stamped onto them — these rules must stay global.
   Scoped to .sigil-btn on the selector itself to avoid leaking elsewhere. */
.sigil-btn .sigil-embers {
  filter: drop-shadow(0 0 3px var(--arcane, #8e2de2))
    drop-shadow(0 0 6px var(--arcane-glow, rgba(142, 45, 226, 0.6)));
}

.sigil-btn .ember {
  pointer-events: none;
  fill: var(--arcane-bright, #e3baff);
  transform-box: view-box;
  animation: sigil-ember-rise var(--life, 800ms) ease-out forwards;
}

@keyframes sigil-ember-rise {
  0% {
    transform: translate(0, 0) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(var(--dx), var(--dy)) scale(0.15);
    opacity: 0;
  }
}
</style>
