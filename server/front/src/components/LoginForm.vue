<template>
  <q-card class="q-pa-md">
    <q-card-section>
      <div class="text-h6">Enter server password</div>
    </q-card-section>
    <q-card-section>
      <q-form @submit.prevent="onSubmit">
        <div class="row">
          <div class="col col-12">
            <q-input
              outlined
              v-model="password"
              type="password"
              label="Password"
            ></q-input>
          </div>
        </div>
        <div class="q-pt-md">
          <q-btn label="Submit" type="submit" color="cbs" />
        </div>
      </q-form>
    </q-card-section>
  </q-card>
</template>

<script>
import { mapMutations } from "vuex";

export default {
  data: function () {
    return {
      password: null,
    };
  },
  methods: {
    onSubmit: async function () {
      this.setServerPassword(this.password);
      await this.$router.push({ name: "flags" });
    },
    ...mapMutations(["setServerPassword"]),
  },
};
</script>

<style></style>
