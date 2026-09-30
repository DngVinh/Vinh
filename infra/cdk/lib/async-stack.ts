export interface QueueItemConfig {
  name: string;
  fifo: boolean;
  maxReceiveCount: number;
  dlqRetentionDays: number;
  kmsMasterKeyId: string;
}

export interface AsyncStackConfig {
  queues: QueueItemConfig[];
}

export interface DeadLetterQueueDefinition {
  name: string;
  maxReceiveCount: number;
  retentionPeriodDays: number;
}

export interface QueueDefinition {
  name: string;
  fifo: boolean;
  kmsMasterKeyId: string;
  deadLetterQueue: DeadLetterQueueDefinition;
}

export interface AsyncStackResult {
  stackName: string;
  queues: QueueDefinition[];
}

export function createAsyncStack(config: AsyncStackConfig): AsyncStackResult {
  const queues: QueueDefinition[] = config.queues.map(q => {
    if (q.maxReceiveCount < 1) {
      throw new Error(`Queue ${q.name}: maxReceiveCount must be at least 1.`);
    }
    if (!q.kmsMasterKeyId || q.kmsMasterKeyId.trim().length === 0) {
      throw new Error(`Queue ${q.name}: KMS key ID must be specified for encryption.`);
    }

    return {
      name: q.name,
      fifo: q.fifo,
      kmsMasterKeyId: q.kmsMasterKeyId,
      deadLetterQueue: {
        name: `${q.name}-dlq`,
        maxReceiveCount: q.maxReceiveCount,
        retentionPeriodDays: q.dlqRetentionDays || 14,
      },
    };
  });

  return {
    stackName: 'AsyncStack',
    queues,
  };
}
