<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useSession } from "@/composables/useSession";
import AppSidebar from "@/components/AppSidebar.vue";
import CounterHeader from "@/components/CounterHeader.vue";

// The counter header (letterhead, coins, slate) is ported below. The
// wordmark/user name/sign-out handler are props/emit — everything else
// about the header is presentation, owned by CounterHeader.vue.
defineProps<{
  wordmark: string;
  userName: string;
}>();

const emit = defineEmits<{
  signOut: [];
}>();

// Port target #1: buildBook() becomes this computed setup instead of
// imperative DOM generation.
// Port target #7 (SCROLLING.md §7): a ResizeObserver drives layout(),
// belt-and-braces with an explicit call on mount and on route change — not
// a locally scrolling content box (that was tried in the reference and
// rejected, see SCROLLING.md §4). The whole book moves through a fixed
// viewport via real document scroll; only .stage's height is JS-driven.

const FAN_FIRST = 11;
const FAN_RATIO = 0.82;
const RISE_FIRST = 2.9;
const RISE_RATIO = 0.84;
const FILLER_LAYERS = 2;
const Z_BASE = 10;

const { can } = useSession();
const route = useRoute();

/** Pick ink that stays legible on whatever colour the cloth is dyed. */
function inkOn(hex: string): string {
  const c = hex.replace("#", "");
  const ch = (i: number) => parseInt(c.substr(i, 2), 16) / 255;
  const lin = (v: number) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
  const luminance = 0.2126 * lin(ch(0)) + 0.7152 * lin(ch(2)) + 0.0722 * lin(ch(4));
  return luminance > 0.25 ? "#2b2420" : "rgba(255,255,255,0.94)";
}

const sections = computed(() => {
  const items = [{ to: "/dashboard", label: "My Profile", colour: "#7c8b6f" }];
  if (can("listEmployees")) {
    items.push({ to: "/employees", label: "Team Roster", colour: "#4f7086" });
  }
  if (can("createEmployee")) {
    items.push({ to: "/signup", label: "New Employee", colour: "#c08a3e" });
  }
  return items;
});

// One layer per section, plus a few filler sheets deeper in the stack for
// depth past the last tab. Gaps shrink with depth (3.3 The fan).
const layers = computed(() => {
  const n = sections.value.length + FILLER_LAYERS;
  const out: { off: number; rise: number; z: number }[] = [];
  let off = 0;
  let rise = 0;
  for (let i = 0; i < n; i++) {
    off += FAN_FIRST * Math.pow(FAN_RATIO, i);
    rise += RISE_FIRST * Math.pow(RISE_RATIO, i);
    out.push({
      off: Math.round(off * 10) / 10,
      rise: Math.round(rise * 10) / 10,
      z: Z_BASE + (n - 1 - i) * 2,
    });
  }
  return out;
});

// Non-null: layers always has at least FILLER_LAYERS (>=1) more entries than
// sections, so index 0 here and index i below (i < sections.value.length)
// are always in bounds.
const zTop = computed(() => layers.value[0]!.z + 2);
const zExt = computed(() => zTop.value + 2);

// Tabs are buried one z-slot under their own layer (3.1 Tab burial) — the
// layer's paper covers the tab's root; only the exposed length past the
// layer's offset pokes out to the left.
const tabs = computed(() =>
  sections.value.map((s, i) => ({
    to: s.to,
    label: s.label,
    colour: s.colour,
    ink: inkOn(s.colour),
    top: `calc(var(--tab-top) + ${i} * (var(--tab-h) + var(--tab-gap)))`,
    z: layers.value[i]!.z - 1,
    extZ: zExt.value,
  })),
);

const stageEl = ref<HTMLElement | null>(null);
const bookEl = ref<HTMLElement | null>(null);
const contentEl = ref<HTMLElement | null>(null);

// SCROLLING.md §2 — the whole of layout(). Sizes .book so its foot always
// sits below the fold at maximum scroll, and .stage to exactly that
// maximum scroll range so it becomes the document height.
function layout() {
  if (!stageEl.value || !bookEl.value || !contentEl.value) {
    return;
  }

  const vh = window.innerHeight;
  const bookTop = bookEl.value.offsetTop;

  const insetBottomVh =
    parseFloat(getComputedStyle(stageEl.value).getPropertyValue("--content-inset-bottom")) || 0;
  const insetBottom = (insetBottomVh / 100) * vh;

  // Scroll-independent: content's bottom edge relative to the book's own
  // top edge, regardless of current scroll position (SCROLLING.md §2).
  const bookRect = bookEl.value.getBoundingClientRect();
  const contentRect = contentEl.value.getBoundingClientRect();
  const contentOffsetInBook = contentRect.bottom - bookRect.top;

  const contentBottom = bookTop + contentOffsetInBook + insetBottom;
  const scrollRange = Math.max(0, contentBottom - vh);

  bookEl.value.style.height = `${scrollRange + vh * 1.5}px`;
  stageEl.value.style.height = `${vh + scrollRange}px`;
}

let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  layout();
  resizeObserver = new ResizeObserver(layout);
  if (contentEl.value) {
    resizeObserver.observe(contentEl.value);
  }
  window.addEventListener("resize", layout);
});

onUnmounted(() => {
  resizeObserver?.disconnect();
  window.removeEventListener("resize", layout);
});

// On section change: paint (handled by the router swapping the slot
// content), call layout(), then reset scroll — in that order (SCROLLING.md
// §5). The ResizeObserver above covers late content changes on top of this.
watch(
  () => route.path,
  async () => {
    await nextTick();
    layout();
    window.scrollTo(0, 0);
  },
);
</script>

<template>
  <div class="countertop"></div>

  <div ref="stageEl" class="stage">
    <CounterHeader :wordmark="wordmark" :user-name="userName" @sign-out="emit('signOut')" />

    <div ref="bookEl" class="book">
      <div class="cover"></div>

      <div class="page-left">
        <div
          v-for="(layer, i) in layers"
          :key="i"
          class="page-layer"
          :style="{
            left: `${-layer.off}px`,
            top: `${-layer.rise}px`,
            bottom: `${-layer.rise}px`,
            zIndex: layer.z,
          }"
        ></div>

        <AppSidebar :tabs="tabs" />

        <div class="page-top" :style="{ zIndex: zTop }">
          <div ref="contentEl" class="page-content">
            <slot />
          </div>
        </div>
      </div>

      <div class="page-right">
        <div
          v-for="(layer, i) in layers"
          :key="i"
          class="page-layer-r"
          :style="{
            right: `${-layer.off}px`,
            top: `${-layer.rise}px`,
            bottom: `${-layer.rise}px`,
            zIndex: layer.z,
          }"
        ></div>
        <div class="page-top-r" :style="{ zIndex: zTop }"></div>
      </div>

      <div class="gutter"></div>
    </div>
  </div>
</template>

<style scoped>
/* Never moves — the camera is static (SCROLLING.md §1). */
.countertop {
  position: fixed;
  inset: 0;
  z-index: 0;
  background-image:
    linear-gradient(rgba(0, 0, 0, 0.14), rgba(0, 0, 0, 0.14)),
    radial-gradient(ellipse at 30% 25%, transparent 38%, rgba(0, 0, 0, 0.42) 100%),
    url("@/assets/finals/countertop.jpg");
  background-size: cover;
  background-position: center center;
}

.stage {
  --tab-w: 165px;
  --tab-h: 40px;
  --tab-gap: 14px;
  --tab-top: 13vh;
  --tab-overlap: 30px;

  /* --cover-lip and --slate-h must be declared before --book-top, which
     derives from them (HEADER.md §6) — measuring only to the book's own
     top edge leaves the gap the slate needs filled with leather. */
  --cover-lip: 26px;
  --slate-w: 330px;
  --slate-h: 104px;
  --slate-gap: 18px;
  --book-top: max(11vh, calc(var(--slate-h) + var(--cover-lip) + var(--slate-gap)));
  --book-left: max(5vw, calc(var(--tab-w) + 24px));
  --right-sliver: 72px;
  --page-w: calc(66.667% - var(--right-sliver) - var(--book-left));
  --content-inset-top: 9vh;
  --content-inset-bottom: 9vh;

  /* The riven edge sits ~11.5% in from the slate element's left; because
     the image is width-scaled by `cover` at this aspect ratio, that stays
     true at any slate size, so it must be a %, not a px value (§5.1). */
  --slate-pad-l: calc(11.5% + 32px);
  --slate-pad-b: 30px;
  --slate-pad-r: 32px;
  --coins-w: 333px;
  --paper-w: 560px;
  --paper-peek: 128px;
  --paper-left: calc(var(--book-left) + 2vw);
  --coins-img: url("@/assets/finals/coins.webp");
  --slate-img: url("@/assets/finals/slate.png");

  --cloth-scale: 320px;
  --ink-weave: 0.7;
  --thread: rgba(238, 226, 200, 0.88);
  --stitch-len: 5px;
  --stitch-gap: 4px;

  --tab-font: "MedievalSharp", Georgia, serif;
  --tab-size: 14.5px;
  --tab-tracking: 0.09em;
  --tab-weight: 400;

  /* Normal flow — this height (set by layout()) IS the document height.
     overflow:hidden clips the book's excess (SCROLLING.md §3); this is the
     single most important line in the scroll system. */
  position: relative;
  z-index: 1;
  overflow: hidden;
}

/* 150%, not 150vw (4.3) — percentages measure against .stage so the crease
   never drifts. Height is set by layout(), tall enough that the foot never
   reaches the fold at any scroll position. */
.book {
  position: absolute;
  top: var(--book-top);
  left: var(--book-left);
  width: 150%;
  z-index: 3;
  display: flex;
}

.cover {
  position: absolute;
  top: calc(-1 * var(--cover-lip));
  bottom: calc(-1 * var(--cover-lip));
  left: -64px;
  right: -40px;
  z-index: 5;
  background-image:
    linear-gradient(
      115deg,
      rgba(255, 255, 255, 0.1) 0%,
      rgba(0, 0, 0, 0.1) 40%,
      rgba(0, 0, 0, 0.3) 100%
    ),
    url("@/assets/finals/leather.jpg");
  background-size:
    100% 100%,
    190px 190px;
  background-blend-mode: soft-light, normal;
  border-radius: 3px 0 0 3px;
  box-shadow:
    -13px 0 28px -10px rgba(0, 0, 0, 0.55),
    0 -11px 26px -10px rgba(0, 0, 0, 0.5),
    0 14px 30px -10px rgba(0, 0, 0, 0.55),
    inset 0 0 0 1px rgba(0, 0, 0, 0.25);
}

/* Positioning frames only — no background of their own. Each creates a
   stacking context (position + z-index), so the layer/tab numbering inside
   is local and never has to be reconciled against .cover/.gutter. */
.page-left {
  position: relative;
  z-index: 10;
  flex: 0 0 var(--page-w);
}

.page-right {
  position: relative;
  z-index: 10;
  flex: 1 1 auto;
}

/* Every layer shares one background declaration with .page-top (4.5) — the
   paper covering a tab and the paper being read must never drift apart. */
.page-layer {
  position: absolute;
  right: 0;
  background: linear-gradient(to right, var(--page) 88%, var(--page-gutter) 100%);
  border-top: 1px solid rgba(150, 124, 86, 0.16);
  border-bottom: 1px solid rgba(150, 124, 86, 0.16);
  box-shadow: -3px 0 6px -2px rgba(0, 0, 0, 0.32);
}

.page-layer-r {
  position: absolute;
  left: 0;
  background: linear-gradient(to left, var(--page) 88%, var(--page-gutter) 100%);
  border-top: 1px solid rgba(150, 124, 86, 0.16);
  border-bottom: 1px solid rgba(150, 124, 86, 0.16);
  box-shadow: 3px 0 6px -2px rgba(0, 0, 0, 0.32);
}

/* The sheet you read. No overflow, no fixed height — flows at its natural
   (book-length) height. Never scrolls on its own (SCROLLING.md §5). */
.page-top {
  position: absolute;
  inset: 0;
  background: linear-gradient(to right, var(--page) 88%, var(--page-gutter) 100%);
  border-top: 1px solid rgba(150, 124, 86, 0.34);
  border-bottom: 1px solid rgba(150, 124, 86, 0.34);
  box-shadow: -3px 0 7px -2px rgba(0, 0, 0, 0.3);
}

.page-top-r {
  position: absolute;
  inset: 0;
  background: linear-gradient(to left, var(--page) 88%, var(--page-gutter) 100%);
  border-top: 1px solid rgba(150, 124, 86, 0.34);
  border-bottom: 1px solid rgba(150, 124, 86, 0.34);
  box-shadow: 3px 0 7px -2px rgba(0, 0, 0, 0.3);
}

/* Content margin is floored against the tab overlap (4.6) so on narrow
   viewports the tab never overruns the text. */
.page-content {
  padding-top: var(--content-inset-top);
  padding-bottom: var(--content-inset-bottom);
  padding-left: max(7%, calc(var(--tab-overlap) + 30px));
  padding-right: max(5%, 26px);
  color: var(--ink);
}

/* The crease where the two page blocks meet (2, structure). */
.gutter {
  position: absolute;
  top: -12px;
  bottom: -12px;
  left: var(--page-w);
  width: 90px;
  transform: translateX(-50%);
  z-index: 20;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0) 0%,
    rgba(0, 0, 0, 0.02) 22%,
    rgba(0, 0, 0, 0.07) 38%,
    rgba(0, 0, 0, 0.14) 47%,
    rgba(0, 0, 0, 0.18) 50%,
    rgba(0, 0, 0, 0.14) 53%,
    rgba(0, 0, 0, 0.07) 62%,
    rgba(0, 0, 0, 0.02) 78%,
    rgba(0, 0, 0, 0) 100%
  );
}

.gutter::after {
  content: "";
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1px;
  transform: translateX(-50%);
  background: linear-gradient(
    to bottom,
    rgba(40, 28, 18, 0.3) 0px,
    rgba(40, 28, 18, 0.24) 26px,
    rgba(40, 28, 18, 0.18) 70px,
    rgba(40, 28, 18, 0.18) calc(100% - 70px),
    rgba(40, 28, 18, 0.24) calc(100% - 26px),
    rgba(40, 28, 18, 0.3) 100%
  );
}

.gutter::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(
      ellipse 46% 62px at 50% 0%,
      rgba(40, 28, 18, 0.18) 0%,
      rgba(40, 28, 18, 0.06) 45%,
      rgba(40, 28, 18, 0) 78%
    ),
    radial-gradient(
      ellipse 46% 62px at 50% 100%,
      rgba(40, 28, 18, 0.18) 0%,
      rgba(40, 28, 18, 0.06) 45%,
      rgba(40, 28, 18, 0) 78%
    );
}

@media (max-width: 900px) {
  .stage {
    --tab-w: 140px;
    --tab-h: 34px;
    --tab-gap: 11px;
    --tab-overlap: 22px;
    --tab-size: 13px;
    --tab-tracking: 0.06em;
    --right-sliver: 54px;
  }
  .gutter {
    width: 64px;
  }
}

@media (max-width: 600px) {
  .stage {
    --tab-w: 120px;
    --tab-h: 30px;
    --tab-gap: 9px;
    --tab-overlap: 18px;
    --tab-size: 11.5px;
    --slate-gap: 14px;
    --coins-w: 226px;
    --paper-w: 360px;
    --paper-peek: 96px;
    --paper-left: calc(var(--book-left) + 1vw);
    --content-inset-top: 7vh;
    --content-inset-bottom: 7vh;
    --cover-lip: 18px;
    --slate-w: 250px;
    --slate-h: 88px;
    --slate-pad-b: 24px;
    --slate-pad-r: 25px;
    --right-sliver: 40px;
  }
  .gutter {
    width: 48px;
  }
}
</style>
