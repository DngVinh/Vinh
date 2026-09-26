import { describe, it, expect } from 'vitest';
import { createAsyncStack, AsyncStackConfig } from '../lib/async-stack';

describe('TASK-INFRA-ASYNC-001: SQS Queues and Dead-Letter-Queues', () => {
  it('AC-01: should configure SQS queues with paired DLQs, KMS encryption and retry budgets', () => {
    const config: AsyncStackConfig = {
      queues: [
        {
          name: 'campus247-outbox-events',
          fifo: false,
          maxReceiveCount: 5,
          dlqRetentionDays: 14,
          kmsMasterKeyId: 'alias/aws/sqs',
        },
        {
          name: 'campus247-ingestion-tasks',
          fifo: false,
          maxReceiveCount: 3,
          dlqRetentionDays: 14,
          kmsMasterKeyId: 'alias/aws/sqs',
        },
      ],
    };

    const stack = createAsyncStack(config);
    expect(stack).toBeDefined();
    expect(stack.queues.length).toBe(2);

    const outboxQueue = stack.queues.find(q => q.name === 'campus247-outbox-events');
    expect(outboxQueue).toBeDefined();
    expect(outboxQueue?.deadLetterQueue).toBeDefined();
    expect(outboxQueue?.deadLetterQueue?.name).toBe('campus247-outbox-events-dlq');
    expect(outboxQueue?.deadLetterQueue?.maxReceiveCount).toBe(5);
    expect(outboxQueue?.deadLetterQueue?.retentionPeriodDays).toBe(14);
    expect(outboxQueue?.kmsMasterKeyId).toBe('alias/aws/sqs');
  });

  it('AC-02: failure path - should reject queues with zero maxReceiveCount or missing KMS key', () => {
    expect(() => {
      createAsyncStack({
        queues: [
          {
            name: 'invalid-queue',
            fifo: false,
            maxReceiveCount: 0,
            dlqRetentionDays: 14,
            kmsMasterKeyId: 'alias/aws/sqs',
          },
        ],
      });
    }).toThrow(/maxReceiveCount must be at least 1/i);

    expect(() => {
      createAsyncStack({
        queues: [
          {
            name: 'unencrypted-queue',
            fifo: false,
            maxReceiveCount: 3,
            dlqRetentionDays: 14,
            kmsMasterKeyId: '',
          },
        ],
      });
    }).toThrow(/KMS key ID must be specified/i);
  });
});
