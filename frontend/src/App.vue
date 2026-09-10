<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { usePageTransition } from "@/composables/usePageTransition";
import { useSession } from "@/composables/useSession";
import { useCurrentEmployee } from "@/composables/useCurrentEmployee";
import BookScene from "@/components/BookScene.vue";
import fireballSrc from "@/assets/finals/fireball.webm";
import dragonBreathSrc from "@/assets/finals/dragon-breath.mp3";

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

const { active, consumeNavigate, finish } = usePageTransition();
const navigated = ref(false);
const videoRef = ref<HTMLVideoElement | null>(null);
const audioRef = ref<HTMLAudioElement | null>(null);

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
  logout();
  router.push({ name: "login" });
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
