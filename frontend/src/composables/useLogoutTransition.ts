import { ref } from "vue";

const active = ref(false);
let pendingNavigate: (() => void) | null = null;

export function useLogoutTransition() {
  function reverseFireballTransition(navigate: () => void) {
    pendingNavigate = navigate;
    active.value = true;
  }

  function consumeNavigate() {
    const navigate = pendingNavigate;
    pendingNavigate = null;
    return navigate;
  }

  function finish() {
    active.value = false;
  }

  return { active, reverseFireballTransition, consumeNavigate, finish };
}
