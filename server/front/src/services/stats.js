import axios from "axios";
import { statsUrl } from "@/config";

import {
  errorHandlerInterceptor,
  passwordCheckInterceptor,
} from "@/services/interceptors";

const StatsService = axios.create({ baseURL: statsUrl });

StatsService.interceptors.request.use(passwordCheckInterceptor);
StatsService.interceptors.response.use(
  errorHandlerInterceptor.onFulfilled,
  errorHandlerInterceptor.onRejected
);

export default StatsService;
