import {
  createContext,
  useContext,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react";

import type { AnalyticsFilterState } from "./api";

interface AnalyticsFiltersContextValue {
  filters: AnalyticsFilterState;
  setFilters: Dispatch<SetStateAction<AnalyticsFilterState>>;
}

const AnalyticsFiltersContext =
  createContext<AnalyticsFiltersContextValue | null>(null);

const DEFAULT_FILTERS: AnalyticsFilterState = {
  competition: "ALL",
  innings: null,
  match_stage: "ALL",
  min_high_pressure_balls: 150,
  over: null,
};

export function AnalyticsFiltersProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [filters, setFilters] =
    useState<AnalyticsFilterState>(DEFAULT_FILTERS);
  return (
    <AnalyticsFiltersContext.Provider value={{ filters, setFilters }}>
      {children}
    </AnalyticsFiltersContext.Provider>
  );
}

export function useAnalyticsFilters() {
  const context = useContext(AnalyticsFiltersContext);
  if (!context) {
    throw new Error(
      "useAnalyticsFilters must be used within AnalyticsFiltersProvider",
    );
  }
  return context;
}
