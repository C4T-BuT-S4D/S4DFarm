<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-cbs text-cbs">
      <q-toolbar class="bg-cbs text-cbs">
        <q-avatar>
          <img src="@/assets/cbs.png" />
        </q-avatar>
        <q-toolbar-title> S4D Farm </q-toolbar-title>
        <q-tabs class="bg-cbs text-cbs" shrink>
          <q-route-tab :to="{ name: 'flags' }" label="Flags" />
          <q-route-tab :to="{ name: 'teams' }" label="Teams" />
        </q-tabs>
        <q-space />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <slot />
    </q-page-container>
  </q-layout>
</template>

<script>
export default {
  name: "BaseLayout",
};
</script>

<style></style>
