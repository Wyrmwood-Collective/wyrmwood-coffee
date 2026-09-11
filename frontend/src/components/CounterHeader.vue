<script setup lang="ts">
// Three objects resting on the counter, not a header bar — no bar, no
// background, no border (§1). They are siblings of .book inside .stage
// (§2/port target #1), positioned individually, not a flex row.

defineProps<{
  wordmark: string;
  userName: string;
}>();

const emit = defineEmits<{
  signOut: [];
}>();

function handleSignOut() {
  emit("signOut");
}
</script>

<template>
  <div class="counter-header">
    <div class="slate">
      <div class="slate-text">
        <span class="line">
          <span class="slate-label">Logged in as</span>
          <span class="slate-name">{{ userName }}</span>
        </span>
        <button class="chalkbtn" type="button" @click="handleSignOut">Sign out →</button>
      </div>
    </div>
  </div>

  <div class="coins" aria-hidden="true"></div>

  <div class="letterhead">
    <span class="mark">{{ wordmark }}</span>
    <span class="rule"></span>
  </div>
</template>

<style scoped>
/* Objects resting on the counter, above the book: the book slides
   underneath as it scrolls, which keeps sign-out reachable at any scroll
   position. A plain positioning frame, not a flex row (§2) — it was flex
   when there were three children in it; now that only the slate lives
   here, flex space-between would misplace things. */
.counter-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: var(--book-top);
  z-index: 51;
  pointer-events: none;
}

.counter-header > * {
  pointer-events: auto;
}

/* --- letterhead: a sheet of stationery slipped under the book (§3). --- */
.letterhead {
  position: absolute;
  z-index: 1;
  left: var(--paper-left);
  top: calc(var(--book-top) - var(--paper-peek));
  width: var(--paper-w);
  height: 460px;
  transform: rotate(-0.7deg);
  transform-origin: top center;
  border-radius: 1px;
  background-image:
    repeating-linear-gradient(
      90deg,
      rgba(120, 96, 54, 0.045) 0px,
      rgba(120, 96, 54, 0.045) 1px,
      transparent 1px,
      transparent 4px
    ),
    repeating-linear-gradient(
      0deg,
      rgba(120, 96, 54, 0.03) 0px,
      rgba(120, 96, 54, 0.03) 1px,
      transparent 1px,
      transparent 26px
    ),
    linear-gradient(168deg, #fbf6e9 0%, #f6efdd 55%, #efe6d0 100%);
  box-shadow:
    0 7px 16px -7px rgba(0, 0, 0, 0.55),
    0 1px 2px rgba(0, 0, 0, 0.18),
    inset 0 0 0 1px rgba(120, 96, 54, 0.1);
}

.letterhead .mark {
  display: block;
  margin-top: 23px;
  text-align: center;
  font-family: "My Soul", var(--tab-font);
  font-size: 48px;
  letter-spacing: 0.15em;
  color: #4a3a1e;
}

.letterhead .rule {
  display: block;
  width: 54%;
  margin: 12px auto 0;
  height: 0;
  border-top: 1px solid rgba(74, 58, 30, 0.32);
  box-shadow: 0 2px 0 -1px rgba(74, 58, 30, 0.16);
}

/* --- coins: one image, kept as shot (§4). --- */
.coins {
  position: absolute;
  /* half the counter strip, NOT 50% of .stage — the stage can be several
     screens tall, which would put these far down the page. */
  top: calc(var(--book-top) * 0.5);
  left: 56%;
  z-index: 2;
  transform: translateY(-50%) rotate(-1.5deg);
  width: var(--coins-w);
  aspect-ratio: 640 / 319;
  background: var(--coins-img) center / contain no-repeat;
  filter: drop-shadow(2px 4px 4px rgba(0, 0, 0, 0.45));
  pointer-events: none;
}

/* --- slate: session identity, flush to the top-right corner so the
   viewport itself crops it (§5). --- */
.slate {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 0;
  width: var(--slate-w);
  height: var(--slate-h);
  transform: translateY(-10px) rotate(-2deg);
}

/* An explicit box inset from the raw riven edges (§5.1) — the element's
   box and the stone's own drawn edge are not the same rectangle, so text
   padded to the element renders on bare wood beside the slate. */
.slate-text {
  position: absolute;
  left: var(--slate-pad-l);
  right: var(--slate-pad-r);
  bottom: var(--slate-pad-b);
  text-align: left;
}

.slate::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  background: var(--slate-img) left bottom / cover no-repeat;
  /* follows the irregular stone edge, not the box — must live on ::before,
     not .slate, or it also outlines the chalk text (§5). */
  filter: drop-shadow(-7px 7px 9px rgba(0, 0, 0, 0.5));
}

.slate .line,
.slate .chalkbtn {
  display: block;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-transform: uppercase;
}

.slate-label {
  font-size: 9.5px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(245, 243, 233, 0.8);
  margin-right: 6px;
}

.slate-name {
  font-family: var(--tab-font);
  font-size: 15px;
  color: rgba(241, 239, 229, 0.92);
  text-shadow: 0 0 2px rgba(255, 255, 255, 0.16);
}

.chalkbtn {
  width: 75%;
  margin-top: 3px;
  text-align: right;
  font-family: inherit;
  font-size: 11.5px;
  letter-spacing: 0.05em;
  background: none;
  border: 0;
  padding: 0;
  cursor: pointer;
  color: rgba(245, 243, 233, 0.87);
  text-decoration: underline dotted;
  text-underline-offset: 3px;
  text-shadow: 0 0 2px rgba(255, 255, 255, 0.14);
}

.chalkbtn:hover {
  color: rgba(245, 243, 233, 0.95);
  text-decoration: underline solid;
}

.chalkbtn:focus-visible {
  outline: 1px solid rgba(233, 231, 221, 0.6);
  outline-offset: 2px;
}

@media (max-width: 600px) {
  .slate-name {
    font-size: 13px;
  }
}
</style>
