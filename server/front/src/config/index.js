let url = "";

if (process.env.NODE_ENV === "development") {
  url = "http://127.0.0.1:5000";
} else {
  url = window.location.origin;
}

const serverUrl = url;
const apiUrl = `${serverUrl}/api`;

const flagsPerPage = 30;

export { serverUrl, apiUrl, flagsPerPage };
