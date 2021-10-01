import axios from "axios";
import { apiUrl } from "@/config";

const APIService = axios.create({ baseURL: apiUrl });

export default APIService;
