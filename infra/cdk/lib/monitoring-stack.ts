export interface DashboardWidgetConfig {
  type: 'metric' | 'text' | 'log';
  title: string;
  metrics?: string[];
}

export interface AlarmConfig {
  name: string;
  metric: string;
  threshold: number;
  evaluationPeriods: number;
}

export interface MonitoringStackConfig {
  dashboardName: string;
  widgets: DashboardWidgetConfig[];
  alarms: AlarmConfig[];
}

export interface MonitoringStackResult {
  stackName: string;
  dashboard: {
    name: string;
    widgets: DashboardWidgetConfig[];
  };
  alarms: AlarmConfig[];
}

export function createMonitoringStack(config: MonitoringStackConfig): MonitoringStackResult {
  const hasLatencyOrError = config.widgets.some(
    w => w.title.toLowerCase().includes('latency') || w.title.toLowerCase().includes('error')
  );

  if (!hasLatencyOrError) {
    throw new Error('Dashboard must include latency and error rate widgets for service observability.');
  }

  const hasDlqAlarm = config.alarms.some(a => a.name.toLowerCase().includes('dlq'));
  if (!hasDlqAlarm) {
    throw new Error('Must configure DLQ alert alarm for failed asynchronous processing.');
  }

  return {
    stackName: 'MonitoringStack',
    dashboard: {
      name: config.dashboardName,
      widgets: [...config.widgets],
    },
    alarms: [...config.alarms],
  };
}
