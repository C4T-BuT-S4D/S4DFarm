import axios from "axios";
import { apiUrl } from "@/config";
import {
  errorHandlerInterceptor,
  passwordCheckInterceptor,
} from "@/services/interceptors";

const APIService = axios.create({ baseURL: apiUrl });

APIService.interceptors.request.use(passwordCheckInterceptor);
APIService.interceptors.response.use(
  errorHandlerInterceptor.onFulfilled,
  errorHandlerInterceptor.onRejected
);

export default APIService;
