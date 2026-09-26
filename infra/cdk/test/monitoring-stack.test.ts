import { describe, it, expect } from 'vitest';
import { createMonitoringStack, MonitoringStackConfig } from '../lib/monitoring-stack';

describe('TASK-INFRA-MON-001: CloudWatch Operational Dashboards and Alarms', () => {
  it('AC-01: should create dashboard with key service/RAG widgets and CloudWatch alarms', () => {
    const config: MonitoringStackConfig = {
      dashboardName: 'Campus247-Operations',
      widgets: [
        { type: 'metric', title: 'API RPS and Error Rate', metrics: ['RequestCount', 'HTTPCode_Target_5XX_Count'] },
        { type: 'metric', title: 'API p95 Latency', metrics: ['TargetResponseTime'] },
        { type: 'metric', title: 'ECS Resource Utilization', metrics: ['CPUUtilization', 'MemoryUtilization'] },
        { type: 'metric', title: 'SQS Backlog and DLQ Depth', metrics: ['ApproximateNumberOfMessagesVisible'] },
      ],
      alarms: [
        { name: 'ApiHigh5xxErrorRate', metric: 'HTTPCode_Target_5XX_Count', threshold: 5, evaluationPeriods: 1 },
        { name: 'DlqMessagesPresent', metric: 'ApproximateNumberOfMessagesVisible', threshold: 0, evaluationPeriods: 1 },
      ],
    };

    const stack = createMonitoringStack(config);
    expect(stack).toBeDefined();
    expect(stack.dashboard.name).toBe('Campus247-Operations');
    expect(stack.dashboard.widgets.length).toBe(4);

    const errorWidget = stack.dashboard.widgets.find(w => w.title.includes('Error Rate'));
    expect(errorWidget).toBeDefined();

    const dlqAlarm = stack.alarms.find(a => a.name === 'DlqMessagesPresent');
    expect(dlqAlarm).toBeDefined();
    expect(dlqAlarm?.threshold).toBe(0);
  });

  it('AC-02: failure path - should reject dashboard without latency widgets or missing DLQ alarms', () => {
    expect(() => {
      createMonitoringStack({
        dashboardName: 'Campus247-Operations',
        widgets: [
          { type: 'metric', title: 'Only Request Count', metrics: ['RequestCount'] },
        ],
        alarms: [],
      });
    }).toThrow(/Dashboard must include latency and error rate widgets/i);

    expect(() => {
      createMonitoringStack({
        dashboardName: 'Campus247-Operations',
        widgets: [
          { type: 'metric', title: 'API Latency and Error Rate', metrics: ['TargetResponseTime', 'HTTPCode_Target_5XX_Count'] },
        ],
        alarms: [
          { name: 'SomeOtherAlarm', metric: 'CPUUtilization', threshold: 80, evaluationPeriods: 1 },
        ],
      });
    }).toThrow(/Must configure DLQ alert alarm for failed asynchronous processing/i);
  });
});
