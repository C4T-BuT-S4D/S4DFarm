import axios from "axios";
import { statsUrl } from "@/config";

const StatsService = axios.create({ baseURL: statsUrl });

export default StatsService;
