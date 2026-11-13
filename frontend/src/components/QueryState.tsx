import type { ReactNode } from "react";

interface QueryStateProps {
  isLoading: boolean;
  error: Error | null;
  children: ReactNode;
}

export function QueryState({ isLoading, error, children }: QueryStateProps) {
  if (isLoading) {
    return (
      <div className="query-state" role="status">
        Loading analytics…
      </div>
    );
  }
  if (error) {
    return (
      <div className="query-state query-state-error" role="alert">
        <strong>Analytics unavailable</strong>
        <span>{error.message}</span>
      </div>
    );
  }
  return children;
}
