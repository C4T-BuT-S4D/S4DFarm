<template>
  <q-page class="q-pa-md"
    ><div class="row justify-between q-col-gutter-md">
      <div class="col col-12 col-md-8"><flags-form /></div>
      <div class="col col-12 col-md-4"><flags-submit /></div>
    </div>
    <div class="row q-pt-md justify-center">
      <div class="col">
        <flags-table />
      </div>
    </div>
  </q-page>
</template>

<script>
import FlagsForm from "@/components/FlagsForm.vue";
import FlagsSubmit from "@/components/FlagsSubmit.vue";
import FlagsTable from "@/components/FlagsTable.vue";
import { mapActions } from "vuex";
import { flagsPerPage } from "@/config";
export default {
  components: { FlagsForm, FlagsSubmit, FlagsTable },
  methods: mapActions(["fetchFlags"]),
  created: async function () {
    await this.fetchFlags({ page: 1, pageSize: flagsPerPage });
  },
};
</script>

<style></style>
