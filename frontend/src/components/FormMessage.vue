<script setup lang="ts">
defineProps<{
  text: string;
  type: "error" | "success";
}>();
</script>

<template>
  <div v-if="text" class="message" :class="`message-${type}`">{{ text }}</div>
</template>
