export interface DatabaseStackConfig {
  dbName: string;
  engineVersion: string;
  multiAz: boolean;
  storageEncrypted: boolean;
  kmsKeyId?: string;
  deletionProtection: boolean;
  backupRetentionDays: number;
  extensions: string[];
}

export interface DatabaseInstanceDefinition {
  dbName: string;
  engine: 'postgres';
  engineVersion: string;
  multiAz: boolean;
  storageEncrypted: boolean;
  kmsKeyId: string;
  deletionProtection: boolean;
  backupRetentionDays: number;
  extensions: string[];
  port: number;
}

export interface DatabaseStackResult {
  stackName: string;
  database: DatabaseInstanceDefinition;
}

export function createDatabaseStack(config: DatabaseStackConfig): DatabaseStackResult {
  if (!config.storageEncrypted || !config.kmsKeyId) {
    throw new Error('Database storage must be encrypted with KMS key.');
  }

  if (!config.extensions.includes('vector')) {
    throw new Error('pgvector extension must be enabled for semantic knowledge retrieval.');
  }

  return {
    stackName: 'DataStack',
    database: {
      dbName: config.dbName,
      engine: 'postgres',
      engineVersion: config.engineVersion,
      multiAz: config.multiAz,
      storageEncrypted: config.storageEncrypted,
      kmsKeyId: config.kmsKeyId,
      deletionProtection: config.deletionProtection,
      backupRetentionDays: config.backupRetentionDays,
      extensions: [...config.extensions],
      port: 5432,
    },
  };
}
