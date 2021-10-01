<template>
  <q-page class="q-pa-md"
    ><div class="row justify-center q-col-gutter-md">
      <div class="col col-12 col-md-6"><charts-form /></div>
    </div>
    <div class="row q-pt-md justify-center">
      <div class="col">
        <charts />
      </div>
    </div>
  </q-page>
</template>

<script>
import ChartsForm from "@/components/ChartsForm.vue";
import Charts from "@/components/Charts.vue";
import { mapActions } from "vuex";
export default {
  components: { ChartsForm, Charts },
  methods: mapActions(["fetchFilterOptions"]),
  created: async function () {
    await this.fetchFilterOptions();
  },
};
</script>

<style></style>
