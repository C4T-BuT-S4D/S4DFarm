import { flagsPerPage } from "@/config";
import Flag from "@/models/flag.js";
import Team from "@/models/team.js";
import APIService from "@/services/api";
import { createStore } from "vuex";
import createPersistedState from "vuex-persistedstate";

export default createStore({
  plugins: [createPersistedState({ paths: ["serverPassword"] })],
  state: {
    totalFlags: 0,
    selectedPage: 1,

    flags: [],
    flagFilters: null,
    serverTZ: null,

    sploitFilterOptions: [],
    teamFilterOptions: [],
    statusFilterOptions: [],

    flagFormat: null,

    teams: [],

    serverPassword: null,
  },
  mutations: {
    setTotalFlags(state, totalFlags) {
      state.totalFlags = totalFlags;
    },
    setFlags(state, flags) {
      state.flags = flags;
    },
    setFlagFilters(state, flagFilters) {
      state.flagFilters = flagFilters;
    },
    setSelectedPage(state, page) {
      state.selectedPage = page;
    },
    setServerTZ(state, tz) {
      state.serverTZ = tz;
    },

    setFilterOptions(state, filterOptions) {
      state.sploitFilterOptions = filterOptions.sploit ?? [];
      state.teamFilterOptions = filterOptions.team ?? [];
      state.statusFilterOptions = filterOptions.status ?? [];
    },
    setFlagFormat(state, flagFormat) {
      state.flagFormat = flagFormat;
    },

    setTeams(state, teams) {
      state.teams = teams;
    },

    setServerPassword(state, password) {
      state.serverPassword = password;
    },
  },
  actions: {
    fetchFlags: async function (context) {
      const filters = context.state.flagFilters;
      let params = {
        page: context.state.selectedPage,
        page_size: flagsPerPage,
      };
      if (filters) {
        params = { ...params, ...filters };
      }
      try {
        const { data } = await APIService.get("/filter_flags", { params });

        const flags = data.flags.map((flag) => new Flag(flag));
        context.commit("setFlags", flags);
        context.commit("setTotalFlags", data.total);
      } catch (e) {
        console.error("Error fetching tasks", e);
      }

      await context.dispatch("fetchFilterOptions");
    },

    updatePage: async function (context, page) {
      context.commit("setSelectedPage", page);
      await context.dispatch("fetchFlags");
    },

    fetchFilterOptions: async function (context) {
      try {
        const { data } = await APIService.get("/filter_config");
        context.commit("setFilterOptions", data.filters);
        context.commit("setFlagFormat", data.flag_format);
        context.commit("setServerTZ", data.server_tz);
      } catch (e) {
        console.error("Error fetching filter options", e);
      }
    },

    fetchTeams: async function (context) {
      try {
        const { data } = await APIService.get("/teams");
        const teams = data.map((team) => new Team(team));
        context.commit("setTeams", teams);
      } catch (e) {
        console.error("Error fetching teams", e);
      }
    },
  },
  modules: {},
});
