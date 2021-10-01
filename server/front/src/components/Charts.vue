<template>
  <q-card class="q-pa-md">
    <q-card-section>
      <line-chart
        v-if="showStats"
        :chart-data="processedStats"
        :options="options"
      />
    </q-card-section>
  </q-card>
</template>

<script>
import { mapState, mapActions } from "vuex";
import { LineChart } from "vue-chart-3";
import moment from "moment";
import "chartjs-adapter-moment";

export default {
  components: { LineChart },
  data: function () {
    return {
      options: {
        responsive: true,
        animations: {
          radius: {
            duration: 400,
            easing: "linear",
            loop: (context) => context.active,
          },
        },
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          colorschemes: {
            scheme: "brewer.Paired12",
          },
        },
        scales: {
          x: {
            type: "time",
            display: true,
            ticks: {
              autoSkip: false,
              major: {
                enabled: true,
              },
            },
          },
          y: {
            display: true,
            min: 0,
          },
        },
      },
      showStats: false,
    };
  },
  created: async function () {
    await this.fetchStats();
    this.showStats = true;
  },
  methods: {
    ...mapActions(["fetchStats"]),
    randomColor: function () {
      const r = Math.floor(Math.random() * 255);
      const g = Math.floor(Math.random() * 255);
      const b = Math.floor(Math.random() * 255);
      return "rgb(" + r + "," + g + "," + b + ")";
    },
  },
  computed: {
    ...mapState(["stats"]),
    processedStats: function () {
      const result = { datasets: [] };
      for (const stat of this.stats) {
        const ds = {
          label: `${stat.labels.sploit} x ${stat.labels.team}`,
          borderColor: this.randomColor(),
          data: [],
        };
        for (const point of stat.data) {
          ds.data.push({
            x: moment.unix(point[0]),
            y: point[1],
          });
        }
        result.datasets.push(ds);
      }
      return result;
    },
  },
};
</script>

<style></style>
