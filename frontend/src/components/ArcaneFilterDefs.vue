<script lang="ts">
// Shared across every LinkButton/SigilButton instance — an SFC's <script>
// block (as opposed to <script setup>) runs once per module load, not once
// per component instance, so this flag is set exactly once no matter how
// many buttons of either kind end up on the page. Only the first one injects
// the SVG filter the hover "waver"/"wriggle" effect references; the rest
// just point at its id.
let filterDefsInjected = false;
</script>

<script setup lang="ts">
const renderFilterDefs = !filterDefsInjected;
filterDefsInjected = true;
</script>

<template>
  <svg v-if="renderFilterDefs" width="0" height="0" style="position: absolute" aria-hidden="true">
    <defs>
      <filter id="arcane-waver" x="-40%" y="-40%" width="180%" height="180%">
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
</template>
