import { describe, it, expect } from 'vitest';
import { createDatabaseStack, DatabaseStackConfig } from '../lib/database-stack';

describe('TASK-INFRA-DATA-001: RDS PostgreSQL pgvector Topology', () => {
  it('AC-01: should configure RDS PostgreSQL Multi-AZ with pgvector, KMS and deletion protection', () => {
    const config: DatabaseStackConfig = {
      dbName: 'campus247',
      engineVersion: '16.3',
      multiAz: true,
      storageEncrypted: true,
      kmsKeyId: 'arn:aws:kms:ap-southeast-1:123456789012:key/db-key',
      deletionProtection: true,
      backupRetentionDays: 14,
      extensions: ['vector', 'uuid-ossp'],
    };

    const stack = createDatabaseStack(config);
    expect(stack).toBeDefined();
    expect(stack.database.dbName).toBe('campus247');
    expect(stack.database.engine).toBe('postgres');
    expect(stack.database.engineVersion).toBe('16.3');
    expect(stack.database.multiAz).toBe(true);
    expect(stack.database.storageEncrypted).toBe(true);
    expect(stack.database.kmsKeyId).toBe('arn:aws:kms:ap-southeast-1:123456789012:key/db-key');
    expect(stack.database.deletionProtection).toBe(true);
    expect(stack.database.backupRetentionDays).toBe(14);
    expect(stack.database.extensions).toContain('vector');
  });

  it('AC-02: failure path - should reject unencrypted storage or missing vector extension', () => {
    expect(() => {
      createDatabaseStack({
        dbName: 'campus247',
        engineVersion: '16.3',
        multiAz: true,
        storageEncrypted: false,
        deletionProtection: true,
        backupRetentionDays: 14,
        extensions: ['vector'],
      });
    }).toThrow(/Database storage must be encrypted with KMS/i);

    expect(() => {
      createDatabaseStack({
        dbName: 'campus247',
        engineVersion: '16.3',
        multiAz: true,
        storageEncrypted: true,
        kmsKeyId: 'key-123',
        deletionProtection: true,
        backupRetentionDays: 14,
        extensions: [],
      });
    }).toThrow(/pgvector extension must be enabled/i);
  });
});
