let url = "";

if (process.env.NODE_ENV === "development") {
  url = "http://127.0.0.1:5137";
} else {
  url = window.location.origin;
}

const serverUrl = url;
const apiUrl = `${serverUrl}/api`;
const statsUrl = `${serverUrl}/stats`;

const flagsPerPage = 30;

export { serverUrl, apiUrl, statsUrl, flagsPerPage };
