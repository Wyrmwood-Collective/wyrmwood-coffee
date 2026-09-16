<script setup lang="ts">
import type { ArcaneButtonProps } from "@/types/button";
import ArcaneFilterDefs from "./ArcaneFilterDefs.vue";

defineOptions({ inheritAttrs: false });

withDefaults(defineProps<ArcaneButtonProps>(), { type: "button", disabled: false });
</script>

<template>
  <ArcaneFilterDefs />
  <button v-bind="$attrs" :type="type" :disabled="disabled" class="link-button">
    <slot />
  </button>
</template>

<style scoped>
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

/* Ultraviolet "waver": an SVG turbulence/displacement filter (see
   ArcaneFilterDefs.vue) distorts the glyph outlines the way the sigil's ink
   does on hover, paired with the same arcane glow. */
.link-button:hover:not(:disabled),
.link-button:focus-visible:not(:disabled) {
  color: var(--arcane-ignited-text, #fff);
  text-decoration: none;
  filter: url(#arcane-waver);
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
