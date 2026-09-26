import { describe, it, expect } from 'vitest';
import { createIamStack, IamStackConfig, PolicyStatement } from '../lib/iam-stack';

describe('TASK-INFRA-IAM-001: Least-Privilege IAM Roles and Policies', () => {
  it('AC-01: should create scoped least-privilege roles without wildcards', () => {
    const config: IamStackConfig = {
      account: '123456789012',
      region: 'ap-southeast-1',
      kmsKeyArn: 'arn:aws:kms:ap-southeast-1:123456789012:key/app-key',
      outboxQueueArn: 'arn:aws:sqs:ap-southeast-1:123456789012:campus247-outbox',
      knowledgeBucketArn: 'arn:aws:s3:::campus247-knowledge',
    };

    const stack = createIamStack(config);
    expect(stack).toBeDefined();
    expect(stack.roles.executionRole).toBeDefined();
    expect(stack.roles.apiTaskRole).toBeDefined();
    expect(stack.roles.workerTaskRole).toBeDefined();

    // Check statements have no wildcards
    const allStatements = [
      ...stack.roles.executionRole.statements,
      ...stack.roles.apiTaskRole.statements,
      ...stack.roles.workerTaskRole.statements,
    ];

    expect(allStatements.length).toBeGreaterThan(0);
    for (const stmt of allStatements) {
      expect(stmt.actions).not.toContain('*');
      expect(stmt.resources).not.toContain('*');
      expect(stmt.effect).toBe('Allow');
    }
  });

  it('AC-02: failure path - should reject policy statements with wildcard actions or resources', () => {
    const invalidStatements: PolicyStatement[] = [
      {
        effect: 'Allow',
        actions: ['*'], // Wildcard action violation
        resources: ['arn:aws:s3:::test'],
      },
    ];

    expect(() => {
      createIamStack({
        account: '123456789012',
        region: 'ap-southeast-1',
        customStatements: invalidStatements,
      });
    }).toThrow(/Wildcard action or resource is prohibited in least-privilege IAM policies/i);
  });
});
