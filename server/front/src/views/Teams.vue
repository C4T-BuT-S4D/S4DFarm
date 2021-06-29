<template>
  <q-page class="q-pa-md"
    ><div class="row justify-between q-col-gutter-md">
      <div class="col col-12"><teams-table /></div>
    </div>
  </q-page>
</template>

<script>
import TeamsTable from "@/components/TeamsTable.vue";
import { mapActions } from "vuex";
export default {
  components: { TeamsTable },
  created: async function () {
    await this.fetchTeams();
  },
  methods: mapActions(["fetchTeams"]),
};
</script>

<style></style>
