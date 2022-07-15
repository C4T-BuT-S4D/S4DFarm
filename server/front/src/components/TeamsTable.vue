<template>
  <q-table
    virtual-scroll
    dense
    :rows="teams"
    :columns="columns"
    :rows-per-page-options="[0]"
    style="height: 80vh"
    row-key="name"
    no-data-label="No teams to attack"
    table-header-class="bg-cbs text-cbs"
  >
    <template v-slot:no-data="{ message }">
      <div class="full-width row flex-center text-accent q-gutter-sm">
        <q-icon size="2em" name="sentiment_dissatisfied" />
        <span> Well this is sad... {{ message }} </span>
      </div>
    </template>
    <template v-slot:header-cell="props">
      <q-th :props="props" :style="{ textAlign: 'center' }">
        {{ props.col.label }}
      </q-th>
    </template>
    <template v-slot:body-cell-address="props">
      <q-td :props="props">
        <div>
          {{ props.value }}
          <q-btn
            size="sm"
            flat
            round
            icon="content_copy"
            @click="copyToClipboard(props.value)"
          />
        </div>
      </q-td>
    </template>
  </q-table>
</template>

<script>
import { mapState } from "vuex";
import { copyToClipboard } from "quasar";

export default {
  data: function () {
    return {
      columns: [
        { name: "name", label: "Name", field: "name", align: "center" },
        {
          name: "address",
          label: "Address",
          field: "address",
          align: "center",
        },
      ],
    };
  },
  computed: mapState(["teams"]),
  methods: { copyToClipboard },
};
</script>

<style></style>
