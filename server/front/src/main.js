import App from "@/App.vue";
import BaseLayout from "@/layouts/BaseLayout.vue";
import quasarUserOptions from "@/quasar-user-options";
import router from "@/router";
import store from "@/store";
import { Quasar } from "quasar";
import "quasar/dist/quasar.sass";
import { createApp } from "vue";

const app = createApp(App);

app.use(Quasar, quasarUserOptions);
app.use(store);
app.use(router);

app.component("base-layout", BaseLayout);

app.mount("#app");
