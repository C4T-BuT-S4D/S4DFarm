<template>
  <q-card class="q-pa-md">
    <q-card-section>
      <div class="text-h6">Filter attacks</div>
    </q-card-section>
    <q-card-section>
      <q-form @submit.prevent="onSubmit">
        <div class="row justify-center">
          <div class="col col-6 q-px-sm">
            <q-select
              outlined
              v-model="sploit"
              :options="sploitOptions"
              label="Sploit"
              ><template v-if="sploit" v-slot:append>
                <q-icon
                  name="cancel"
                  @click.stop="sploit = null"
                  class="cursor-pointer"
                /> </template
            ></q-select>
          </div>
          <div class="col col-6 q-px-sm">
            <q-select
              outlined
              v-model="team"
              :options="teamOptions"
              label="Team"
              ><template v-if="team" v-slot:append>
                <q-icon
                  name="cancel"
                  @click.stop="team = null"
                  class="cursor-pointer"
                /> </template
            ></q-select>
          </div>
        </div>
        <div class="row justify-center q-pt-md">
          <div class="col col-6 q-px-sm">
            <q-input
              outlined
              v-model="since"
              label="Since"
              :hint="serverTZ"
              placeholder="yyyy-mm-dd hh:mm"
              ><template v-if="since" v-slot:append>
                <q-icon
                  name="cancel"
                  @click.stop="since = null"
                  class="cursor-pointer"
                /> </template
            ></q-input>
          </div>
          <div class="col col-6 q-px-sm">
            <q-input
              outlined
              v-model="until"
              label="Until"
              :hint="serverTZ"
              placeholder="yyyy-mm-dd hh:mm"
              ><template v-if="until" v-slot:append>
                <q-icon
                  name="cancel"
                  @click.stop="until = null"
                  class="cursor-pointer"
                /> </template
            ></q-input>
          </div>
        </div>
        <div class="row justify-center q-pt-md">
          <q-btn label="Filter" type="submit" color="cbs" />
        </div>
      </q-form>
    </q-card-section>
  </q-card>
</template>

<script>
import { mapState, mapActions, mapMutations } from "vuex";

export default {
  data: function () {
    return {
      sploit: null,
      team: null,

      since: null,
      until: null,
    };
  },
  methods: {
    onSubmit: async function () {
      const filters = {
        sploit: this.sploit,
        team: this.team,
        since: this.since,
        until: this.until,
      };

      this.setStatsFilters(filters);
      await this.fetchStats();
    },
    ...mapActions(["fetchStats"]),
    ...mapMutations(["setStatsFilters"]),
  },
  computed: mapState({
    sploitOptions: "sploitFilterOptions",
    teamOptions: "teamFilterOptions",
    serverTZ: "serverTZ",
  }),
};
</script>

<style></style>
