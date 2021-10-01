import store from "@/store";
import router from "@/router";

const passwordCheckInterceptor = function (config) {
  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  const urlPassword = urlParams.get("password");
  const password = urlPassword ?? store.state.serverPassword;
  if (password != store.state.serverPassword) {
    store.commit("setServerPassword", password);
  }
  config.headers.Authorization = password;
  return config;
};

const errorHandlerInterceptor = {
  onFulfilled: (response) => response,
  onRejected: (error) => {
    const status = error.response ? error.response.status : null;

    if (status == 403) {
      router.push({ name: "login" });
    }

    return Promise.reject(error);
  },
};

export { passwordCheckInterceptor, errorHandlerInterceptor };
