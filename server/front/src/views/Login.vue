<template>
  <q-page class="q-pa-md"
    ><div class="row justify-center">
      <div class="col col-12 col-md-6"><login-form /></div>
    </div>
  </q-page>
</template>

<script>
import LoginForm from "@/components/LoginForm.vue";
export default {
  components: { LoginForm },
};
</script>

<style></style>
