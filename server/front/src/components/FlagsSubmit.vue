<template>
  <q-card class="q-pa-md">
    <q-card-section>
      <div class="text-h6">Submit manually</div>
    </q-card-section>
    <q-card-section>
      <q-form @submit.prevent="onSubmit">
        <q-input
          outlined
          v-model="text"
          label="Text with flags"
          type="textarea"
          :hint="'flag format: ' + flagFormat"
          ><template v-if="text" v-slot:append>
            <q-icon
              name="cancel"
              @click.stop="text = null"
              class="cursor-pointer"
            /> </template
        ></q-input>
        <div class="q-pt-md">
          <q-btn label="Submit" type="submit" color="cbs" />
        </div>
      </q-form>
    </q-card-section>
  </q-card>
</template>

<script>
import { mapState, mapActions, mapMutations } from "vuex";
import APIService from "@/services/api";

export default {
  data: function () {
    return {
      text: "",
    };
  },
  methods: {
    onSubmit: async function () {
      const matches = [...this.text.matchAll(this.flagFormat)];
      const flags = matches.map((flag) => {
        return { flag: flag[0], team: "*", sploit: "Manual" };
      });
      try {
        await APIService.post("/post_flags", flags);
        const newFilters = { sploit: "Manual" };
        this.setFlagFilters(newFilters);
        await this.updatePage(1);
      } catch (e) {
        console.error("Error sending manual flags", e);
      }
    },
    ...mapActions(["updatePage"]),
    ...mapMutations(["setFlagFilters"]),
  },
  computed: mapState(["flagFormat"]),
};
</script>

<style></style>
