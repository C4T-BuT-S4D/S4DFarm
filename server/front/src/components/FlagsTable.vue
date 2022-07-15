<template>
  <q-table
    :rows="flags"
    :columns="columns"
    :rows-per-page-options="[flagsPerPage]"
    v-model:pagination="pagination"
    @request="onRequest"
    row-key="flag"
    no-data-label="No flags for you"
    table-header-class="bg-cbs text-cbs"
    dense
  >
    <template v-slot:top="scope">
      <div class="text-h6">{{ scope.pagination.rowsNumber }} flags total</div>
      <q-space />
      <pagination-custom
        :pagesNumber="scope.pagesNumber"
        :isFirstPage="scope.isFirstPage"
        :isLastPage="scope.isLastPage"
        :page="scope.pagination.page"
        :pageSize="scope.pagination.rowsPerPage"
        :total="scope.pagination.rowsNumber"
        @firstPage="scope.firstPage"
        @prevPage="scope.prevPage"
        @nextPage="scope.nextPage"
        @lastPage="scope.lastPage"
      />
      <q-btn
        flat
        round
        dense
        :icon="scope.inFullscreen ? 'fullscreen_exit' : 'fullscreen'"
        @click="scope.toggleFullscreen"
        class="q-ml-md"
      />
    </template>
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
    <template v-slot:body-cell="props">
      <q-td :props="props">
        <div>
          {{ props.value }}
          <q-btn
            size="sm"
            flat
            round
            icon="content_copy"
            v-if="copyableColumns.includes(props.col.name)"
            @click="copyToClipboard(props.value)"
          />
        </div>
      </q-td>
    </template>
    <template v-slot:pagination="scope">
      <pagination-custom
        :pagesNumber="scope.pagesNumber"
        :isFirstPage="scope.isFirstPage"
        :isLastPage="scope.isLastPage"
        :page="scope.pagination.page"
        :pageSize="scope.pagination.rowsPerPage"
        :total="scope.pagination.rowsNumber"
        @firstPage="scope.firstPage"
        @prevPage="scope.prevPage"
        @nextPage="scope.nextPage"
        @lastPage="scope.lastPage" /></template
  ></q-table>
</template>

<script>
import { mapState, mapActions } from "vuex";
import { copyToClipboard } from "quasar";
import moment from "moment";
import { flagsPerPage } from "@/config";
import PaginationCustom from "@/components/PaginationCustom.vue";

export default {
  components: { PaginationCustom },
  data: function () {
    return {
      columns: [
        { name: "sploit", label: "Sploit", field: "sploit", align: "center" },
        { name: "team", label: "Team", field: "team", align: "center" },
        { name: "flag", label: "Flag", field: "flag", align: "center" },
        {
          name: "time",
          label: "Time",
          field: "time",
          align: "center",
          format: (val) => moment.unix(val).format("MMMM Do YYYY, HH:mm:ss"),
        },
        { name: "status", label: "Status", field: "status", align: "center" },
        {
          name: "checksystemResponse",
          label: "Checksystem response",
          field: "checksystemResponse",
          align: "left",
        },
      ],
      copyableColumns: ["sploit", "flag", "checksystemResponse"],
      flagsPerPage,
    };
  },
  computed: {
    pagination: {
      get: function () {
        return {
          page: this.selectedPage,
          rowsPerPage: flagsPerPage,
          rowsNumber: this.totalFlags,
        };
      },
      set: function (newPagination) {
        if (newPagination.page) {
          this.updatePage(newPagination.page);
        }
      },
    },
    ...mapState(["flags", "totalFlags", "selectedPage"]),
  },
  methods: {
    onRequest: async function (props) {
      this.pagination = props.pagination;
    },
    copyToClipboard,

    ...mapActions(["updatePage"]),
  },
};
</script>

<style></style>
