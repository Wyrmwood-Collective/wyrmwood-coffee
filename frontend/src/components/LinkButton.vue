<script lang="ts">
// Shared across every LinkButton instance — an SFC's <script> block (as
// opposed to <script setup>) runs once per module load, not once per
// component instance, so this flag is set exactly once no matter how many
// buttons end up on the page. Only the first one injects the SVG filter the
// hover "waver" effect references; the rest just point at its id.
let filterDefsInjected = false;
</script>

<script setup lang="ts">
defineOptions({ inheritAttrs: false });

withDefaults(
  defineProps<{
    type?: "button" | "submit" | "reset";
    disabled?: boolean;
  }>(),
  { type: "button", disabled: false },
);

const renderFilterDefs = !filterDefsInjected;
filterDefsInjected = true;
</script>

<template>
  <svg v-if="renderFilterDefs" width="0" height="0" style="position: absolute" aria-hidden="true">
    <defs>
      <filter id="link-button-waver" x="-40%" y="-40%" width="180%" height="180%">
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.025 0.1"
          numOctaves="2"
          seed="4"
          result="noise"
        >
          <animate
            attributeName="baseFrequency"
            values="0.025 0.1;0.06 0.05;0.015 0.15;0.05 0.09;0.025 0.1"
            dur="2.2s"
            repeatCount="indefinite"
          />
        </feTurbulence>
        <feDisplacementMap
          in="SourceGraphic"
          in2="noise"
          scale="6"
          xChannelSelector="R"
          yChannelSelector="G"
        />
      </filter>
    </defs>
  </svg>
  <button v-bind="$attrs" :type="type" :disabled="disabled" class="link-button">
    <slot />
  </button>
</template>

<style scoped>
/* Comic Runes — CC BY-ND, credited in src/assets/media-sources.md. */
@font-face {
  font-family: "Comic Runes";
  src: url("@/assets/fonts/ComicRunes.otf") format("opentype");
}

.link-button {
  background: none;
  border: none;
  /*border-bottom: 2px solid var(--ink-soft, #6b5f4f);*/
  padding: 0;
  margin-left: 14px;
  font: inherit;
  font-family: "Comic Runes", Georgia, serif;
  font-size: 1.3em;
  letter-spacing: 0.03em;
  color: var(--ink-soft, #6b5f4f);
  /*text-decoration: underline solid;*/
  text-underline-offset: 3px;
  cursor: pointer;
  transition:
    color 0.3s ease,
    text-shadow 0.3s ease;
}

.link-button:disabled {
  cursor: default;
  opacity: 0.6;
}

/* Ultraviolet "waver": an SVG turbulence/displacement filter (see the
   #link-button-waver defs above) distorts the glyph outlines the way the
   sigil's ink does on hover, paired with the same arcane glow. */
.link-button:hover:not(:disabled),
.link-button:focus-visible:not(:disabled) {
  color: #fff;
  text-decoration: none;
  filter: url(#link-button-waver);
  text-shadow:
    0 0 4px var(--arcane-bright, #e3baff),
    0 0 10px var(--arcane, #8e2de2),
    0 0 18px var(--arcane-glow, rgba(142, 45, 226, 0.6));
}

@media (prefers-reduced-motion: reduce) {
  .link-button:hover:not(:disabled),
  .link-button:focus-visible:not(:disabled) {
    filter: none;
  }
}
</style>
