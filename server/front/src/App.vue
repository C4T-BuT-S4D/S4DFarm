<template>
  <component :is="layout">
    <router-view />
  </component>
</template>

<script>
export default {
  computed: {
    layout() {
      return this.$route.meta.layout || "base-layout";
    },
  },
};
</script>

<style lang="scss">
html,
body,
#app {
  height: 100%;
  margin: 0;
  background-color: white;
}

body {
  font-family: "Source Code Pro", monospace !important;
}

.text-cbs {
  color: white !important;
}

.bg-cbs {
  background: #333333 !important;
}
</style>
