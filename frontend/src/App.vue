<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { usePageTransition } from "@/composables/usePageTransition";
import { useLogoutTransition } from "@/composables/useLogoutTransition";
import { useSession } from "@/composables/useSession";
import { useCurrentEmployee } from "@/composables/useCurrentEmployee";
import BookScene from "@/components/BookScene.vue";
import fireballSrc from "@/assets/finals/fireball.webm";
import dragonBreathSrc from "@/assets/finals/dragon-breath.mp3";
// Pre-rendered mirror images of the two clips above (via ffmpeg's `reverse`/
// `areverse` filters — see media-sources.md), rather than reversed at
// runtime: <video>/<audio> don't support negative playbackRate reliably
// across browsers, so scrubbing currentTime backwards by hand was the
// alternative, but that path turned out unreliable in practice.
import fireballReverseSrc from "@/assets/finals/fireball-reverse.webm";
import dragonBreathReverseSrc from "@/assets/finals/dragon-breath-reverse.mp3";

// The fireball clip fully engulfs the frame from roughly 1s-2s before
// dissipating away by ~4s. Its black background was keyed into a real
// alpha channel (see frontend/src/assets/fireball.webm) — the flame
// renders fully opaque and black is fully transparent, via normal
// compositing rather than a CSS blend-mode trick.
const NAVIGATE_AT_SECONDS = 1.5;
// Safety net: browsers can suspend a muted autoplaying video (e.g. Chrome's
// "video-only background media" power-saving pause), which would otherwise
// leave the login page stuck forever waiting on a timeupdate that never
// comes. Navigate anyway once this fires, even if the video never played.
const FALLBACK_NAVIGATE_MS = 2000;
// The logout clip's navigate point is mirrored to (duration - 1.5s) rather
// than fixed at 1.5s (see below), which lands around 2.5s for the ~4s
// clip — past the fallback above. Reusing FALLBACK_NAVIGATE_MS here would
// fire before the normal timeupdate-triggered navigate ever does, cutting
// the transition short every time instead of only as a genuine fallback.
const LOGOUT_FALLBACK_NAVIGATE_MS = 3500;

const { active, consumeNavigate, finish } = usePageTransition();
const navigated = ref(false);
const videoRef = ref<HTMLVideoElement | null>(null);
const audioRef = ref<HTMLAudioElement | null>(null);

// Sign-out plays the pre-reversed fireball/roar clips forward — the mirror
// image of the login transition above. Since the reversed clip starts clear
// and becomes fully engulfed around (duration - 2s) to (duration - 1s)
// (the mirror of the forward clip's 1s-2s engulf window), navigate at the
// mirrored point (duration - NAVIGATE_AT_SECONDS) instead of the fixed one.
const {
  active: loggingOut,
  reverseFireballTransition,
  consumeNavigate: consumeLogoutNavigate,
  finish: finishLogout,
} = useLogoutTransition();
const logoutNavigated = ref(false);
const logoutVideoRef = ref<HTMLVideoElement | null>(null);
const logoutAudioRef = ref<HTMLAudioElement | null>(null);

const { logout } = useSession();
const { employee } = useCurrentEmployee();
const router = useRouter();

const userName = computed(() => {
  if (!employee.value) {
    return "";
  }
  return `${employee.value.first_name} ${employee.value.last_name}`;
});

function handleSignOut() {
  reverseFireballTransition(async () => {
    await logout();
    router.push({ name: "login" });
  });
}

function navigateLogoutOnce() {
  if (logoutNavigated.value) return;
  logoutNavigated.value = true;
  consumeLogoutNavigate()?.();
}

watch(loggingOut, (isActive) => {
  if (!isActive) return;
  logoutNavigated.value = false;
  logoutVideoRef.value?.play().catch(() => {
    navigateLogoutOnce();
    finishLogout();
  });
  if (logoutAudioRef.value) {
    logoutAudioRef.value.currentTime = 0;
    logoutAudioRef.value.play().catch(() => {
      // Autoplay blocked — the visual transition still works fine without sound.
    });
  }
  setTimeout(() => {
    if (logoutNavigated.value) return;
    navigateLogoutOnce();
    finishLogout();
  }, LOGOUT_FALLBACK_NAVIGATE_MS);
});

function handleLogoutTimeUpdate(event: Event) {
  const video = event.target as HTMLVideoElement;
  if (Number.isNaN(video.duration)) return;
  if (video.currentTime >= video.duration - NAVIGATE_AT_SECONDS) {
    navigateLogoutOnce();
  }
}

function handleLogoutEnded() {
  finishLogout();
}

function navigateOnce() {
  if (navigated.value) return;
  navigated.value = true;
  consumeNavigate()?.();
}

watch(active, (isActive) => {
  if (!isActive) return;
  navigated.value = false;
  videoRef.value?.play().catch(() => {
    // Video never started (e.g. browser power-saving pause) — nothing will
    // dismiss the overlay, so tear it down along with navigating.
    navigateOnce();
    finish();
  });
  if (audioRef.value) {
    audioRef.value.currentTime = 0;
    audioRef.value.play().catch(() => {
      // Autoplay blocked, e.g. no user-activation window left — the visual
      // transition still works fine without sound.
    });
  }
  setTimeout(() => {
    // Only reached if timeupdate never got here on its own (stalled
    // playback, buffering, etc.) — the normal path already navigated by now.
    if (navigated.value) return;
    navigateOnce();
    finish();
  }, FALLBACK_NAVIGATE_MS);
});

function handleTimeUpdate(event: Event) {
  const video = event.target as HTMLVideoElement;
  if (video.currentTime >= NAVIGATE_AT_SECONDS) {
    navigateOnce();
  }
}

function handleEnded() {
  finish();
}
</script>

<template>
  <RouterView v-slot="{ Component, route }">
    <BookScene
      v-if="route.meta.requiresAuth"
      wordmark="Wyrmwood Coffee"
      :user-name="userName"
      @sign-out="handleSignOut"
    >
      <transition name="page-fade" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </BookScene>
    <component :is="Component" v-else />
  </RouterView>
  <div v-if="active" class="fireball-overlay">
    <video
      ref="videoRef"
      class="fireball-video"
      :src="fireballSrc"
      muted
      playsinline
      autoplay
      @timeupdate="handleTimeUpdate"
      @ended="handleEnded"
    />
  </div>
  <audio ref="audioRef" :src="dragonBreathSrc" preload="auto" />
  <div v-if="loggingOut" class="fireball-overlay">
    <video
      ref="logoutVideoRef"
      class="fireball-video"
      :src="fireballReverseSrc"
      muted
      playsinline
      autoplay
      @timeupdate="handleLogoutTimeUpdate"
      @ended="handleLogoutEnded"
    />
  </div>
  <audio ref="logoutAudioRef" :src="dragonBreathReverseSrc" preload="auto" />
</template>

<style>
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}
</style>

<style scoped>
.fireball-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  pointer-events: none;
  overflow: hidden;
}

.fireball-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
