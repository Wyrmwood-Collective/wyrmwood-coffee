<script setup lang="ts">
import { useRoute } from "vue-router";

defineProps<{
  tabs: {
    to: string;
    label: string;
    colour: string;
    ink: string;
    top: string;
    z: number;
    extZ: number;
  }[];
}>();

const route = useRoute();
</script>

<template>
  <nav aria-label="Main">
    <!-- buried: the real link, its root covered by the layer above it -->
    <RouterLink
      v-for="tab in tabs"
      :key="tab.to"
      :to="tab.to"
      class="tab"
      :style="{ '--c': tab.colour, '--c-ink': tab.ink, top: tab.top, zIndex: tab.z }"
    >
      {{ tab.label }}
    </RouterLink>

    <!-- on-top copy, faded in only for the active section (3.2 Active tab) -->
    <div
      v-for="tab in tabs"
      :key="tab.to + '-ext'"
      class="tab-ext"
      :class="{ 'tab-ext-active': route.path === tab.to }"
      :style="{ '--c': tab.colour, '--c-ink': tab.ink, top: tab.top, zIndex: tab.extZ }"
      aria-hidden="true"
    >
      {{ tab.label }}
    </div>
  </nav>
</template>

<style scoped>
.tab,
.tab-ext {
  position: absolute;
  left: calc(-1 * var(--tab-w));
  height: var(--tab-h);
  border: none;
  background-color: var(--c);
  color: var(--c-ink);
  text-shadow: 0 0 0.7px rgba(0, 0, 0, 0.22);
  font-family: var(--tab-font);
  font-size: var(--tab-size);
  font-weight: var(--tab-weight);
  letter-spacing: var(--tab-tracking);
  padding: 0 0 0 11px;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  display: flex;
  align-items: center;
}

/* the weave, laid over everything — fabric and lettering alike, so the ink
   reads as sitting in the cloth rather than printed on top of it */
.tab::before,
.tab-ext::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("@/assets/finals/cloth.jpg");
  background-size: var(--cloth-scale) var(--cloth-scale);
  mix-blend-mode: overlay;
  opacity: var(--ink-weave);
  border-radius: inherit;
  pointer-events: none;
}

/* buried flag */
.tab {
  width: var(--tab-w);
  cursor: pointer;
  border-radius: 3px 0 0 3px;
  text-decoration: none;
  filter: drop-shadow(1px 2px 2px rgba(0, 0, 0, 0.3));
  transition:
    transform 0.18s ease,
    filter 0.18s ease;
}

.tab:hover {
  transform: translateX(-4px);
  filter: drop-shadow(1px 2px 2px rgba(0, 0, 0, 0.3)) brightness(1.07);
}

/* the on-top copy — laps onto the page, fades in/out */
.tab-ext {
  width: calc(var(--tab-w) + var(--tab-overlap));
  background-image: linear-gradient(
    90deg,
    rgba(58, 40, 22, 0) calc(var(--tab-w) - 10px),
    rgba(58, 40, 22, 0.13) calc(var(--tab-w) + 3px),
    rgba(58, 40, 22, 0.1) 100%
  );
  border-radius: 3px 2px 2px 3px;
  opacity: 0;
  pointer-events: none;
  filter: drop-shadow(2px 2px 2.5px rgba(0, 0, 0, 0.24));
  transition: opacity 0.3s ease;
}

.tab-ext-active {
  opacity: 1;
}

/* running stitch holding the tab to the page — active tab only */
.tab-ext::after {
  content: "";
  position: absolute;
  top: 7px;
  bottom: 7px;
  left: calc(var(--tab-w) + 13px);
  width: 2.5px;
  background: repeating-linear-gradient(
    to bottom,
    var(--thread) 0px,
    var(--thread) var(--stitch-len),
    transparent var(--stitch-len),
    transparent calc(var(--stitch-len) + var(--stitch-gap))
  );
  filter: drop-shadow(0.5px 1px 0.6px rgba(0, 0, 0, 0.5));
  pointer-events: none;
}
</style>
