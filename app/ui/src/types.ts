export type KPI = {
  cog_per_kg: number | null;
  annual_throughput_kg: number | null;
  overall_yield: number | null;
};

export type RunSummary = {
  run_id: string;
  summary: KPI;
};
