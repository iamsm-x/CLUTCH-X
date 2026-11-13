import { useState } from "react";
import * as echarts from "echarts/core";
import ReactEChartsCore from "echarts-for-react/lib/core";
import type { EChartsOption } from "echarts";
import { ScatterChart } from "echarts/charts";
import {
  GraphicComponent,
  GridComponent,
  MarkLineComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { useQuery } from "@tanstack/react-query";

import { getQuadrantScatter } from "../api";
import { useAnalyticsFilters } from "../filters";
import { QueryState } from "./QueryState";

echarts.use([
  ScatterChart,
  GraphicComponent,
  GridComponent,
  MarkLineComponent,
  TooltipComponent,
  CanvasRenderer,
]);

export function QuadrantChart() {
  const [discipline, setDiscipline] = useState<"batting" | "bowling">(
    "batting",
  );
  const { filters } = useAnalyticsFilters();
  const scatter = useQuery({
    queryKey: ["quadrant-scatter", discipline, filters],
    queryFn: () => getQuadrantScatter(discipline, filters),
  });

  const option: EChartsOption = {
    animation: false,
    grid: { left: 58, right: 28, top: 54, bottom: 52 },
    tooltip: {
      trigger: "item",
      formatter: "{b}<br/>Baseline / pressure / delta: {c}",
    },
    xAxis: {
      type: "value",
      min: 0,
      max: 100,
      name: "NORMAL BASELINE RATING",
      nameLocation: "middle",
      nameGap: 34,
      axisLabel: { color: "#94A3B8" },
      nameTextStyle: { color: "#94A3B8", fontSize: 10 },
      splitLine: { lineStyle: { color: "#1E2532" } },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      name: "HIGH-PRESSURE RATING",
      nameLocation: "middle",
      nameGap: 42,
      axisLabel: { color: "#94A3B8" },
      nameTextStyle: { color: "#94A3B8", fontSize: 10 },
      splitLine: { lineStyle: { color: "#1E2532" } },
    },
    graphic: [
      {
        type: "text",
        right: "3%",
        top: "4%",
        style: { text: "ALL-WEATHER ELITES", fill: "#FF5500", fontSize: 10 },
      },
      {
        type: "text",
        left: "8%",
        top: "4%",
        style: { text: "CLUTCH ELEVATORS", fill: "#00A3FF", fontSize: 10 },
      },
      {
        type: "text",
        right: "3%",
        bottom: "4%",
        style: { text: "FRONT-RUNNERS", fill: "#94A3B8", fontSize: 10 },
      },
      {
        type: "text",
        left: "8%",
        bottom: "4%",
        style: { text: "BELOW PAR", fill: "#475569", fontSize: 10 },
      },
    ],
    series: [
      {
        type: "scatter",
        data: (scatter.data?.points ?? []).map((point) => ({
          name: point.rank
            ? `#${point.rank} ${point.player_name}`
            : point.player_name,
          value: [
            point.baseline_rating,
            point.pressure_rating,
            point.net_clutch_delta,
          ],
          symbolSize: point.rank ? 14 : 9,
          itemStyle: { color: point.rank ? "#FF5500" : "#475569" },
          label: {
            show: point.rank !== null,
            formatter: point.rank ? `#${point.rank}` : "",
            color: "#FFFFFF",
            fontSize: 10,
          },
        })),
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { color: "#64748B", type: "dashed", width: 1 },
          label: { show: false },
          data: [
            { xAxis: scatter.data?.baseline_median ?? 50 },
            { yAxis: scatter.data?.pressure_median ?? 50 },
          ],
        },
        labelLayout: { moveOverlap: "shiftY", hideOverlap: true },
      },
    ],
  };

  return (
    <QueryState isLoading={scatter.isLoading} error={scatter.error}>
      <section className="quadrant-panel" aria-label="Baseline and pressure quadrant">
        <div className="quadrant-heading">
          <div>
            <div className="eyebrow">BASELINE VS. PRESSURE EXECUTION</div>
            <h2>Player performance quadrants</h2>
          </div>
          <div className="discipline-switch" aria-label="Scatter discipline">
            <button
              type="button"
              aria-pressed={discipline === "batting"}
              onClick={() => setDiscipline("batting")}
            >
              BATTING
            </button>
            <button
              type="button"
              aria-pressed={discipline === "bowling"}
              onClick={() => setDiscipline("bowling")}
            >
              BOWLING
            </button>
          </div>
        </div>
        <ReactEChartsCore
          echarts={echarts}
          option={option}
          notMerge
          style={{ height: 480, width: "100%" }}
        />
        <div className="quadrant-player-key" aria-label="Ranked player labels">
          {(scatter.data?.points ?? [])
            .filter((point) => point.rank !== null)
            .map((point) => (
              <span key={point.player_id}>
                <strong>#{point.rank}</strong>
                {point.player_name}
              </span>
            ))}
        </div>
      </section>
    </QueryState>
  );
}
