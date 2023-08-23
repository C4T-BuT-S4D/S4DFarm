let url = "";

console.log("!!!", import.meta.env)

if (import.meta.env.DEV) {
  url = "http://127.0.0.1:5137";
} else {
  url = window.location.origin;
}

const serverUrl = url;
const apiUrl = `${serverUrl}/api`;

console.log("!!!", apiUrl)

const flagsPerPage = 30;

export { apiUrl, flagsPerPage, serverUrl };
