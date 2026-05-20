import { Circle, Cpu } from "lucide-react";
import type { WorkerStatus } from "../types";

type WorkerStatusBadgeProps = {
  worker: WorkerStatus;
};

export function WorkerStatusBadge({ worker }: WorkerStatusBadgeProps) {
  const isOnline = worker.status === "online";

  return (
    <div className={`worker-badge ${isOnline ? "online" : "offline"}`}>
      <Cpu size={17} aria-hidden="true" />
      <span>
        <Circle size={8} fill="currentColor" aria-hidden="true" />
        {isOnline ? "AI 콘솔 온라인" : "AI 콘솔 오프라인"}
      </span>
    </div>
  );
}
