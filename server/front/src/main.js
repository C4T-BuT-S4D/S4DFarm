import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import { Quasar } from "quasar";
import quasarUserOptions from "./quasar-user-options";
import BaseLayout from "@/layouts/BaseLayout";
import axios from "axios";
import { apiUrl } from "@/config";
import { Chart, registerables } from "chart.js";

axios.defaults.baseURL = apiUrl;

axios.interceptors.request.use(function (config) {
  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  const urlPassword = urlParams.get("password");
  const password = urlPassword ?? store.state.serverPassword;
  if (password != store.state.serverPassword) {
    store.commit("setServerPassword", password);
  }
  config.headers.Authorization = password;
  return config;
});

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response ? error.response.status : null;

    if (status == 403) {
      router.push({ name: "login" });
    }

    return Promise.reject(error);
  }
);

Chart.register(...registerables);

const app = createApp(App);

app.use(Quasar, quasarUserOptions);
app.use(store);
app.use(router);

app.component("base-layout", BaseLayout);

app.config.globalProperties.$http = axios;

app.mount("#app");
