export interface CacheStackConfig {
  clusterId: string;
  engineVersion: string;
  nodeType: string;
  numCacheClusters: number;
  automaticFailoverEnabled: boolean;
  multiAzEnabled: boolean;
  atRestEncryptionEnabled: boolean;
  transitEncryptionEnabled: boolean;
  authTokenRequired: boolean;
}

export interface CacheClusterDefinition {
  clusterId: string;
  engine: 'redis';
  engineVersion: string;
  nodeType: string;
  numCacheClusters: number;
  automaticFailoverEnabled: boolean;
  multiAzEnabled: boolean;
  atRestEncryptionEnabled: boolean;
  transitEncryptionEnabled: boolean;
  authTokenRequired: boolean;
  port: number;
}

export interface CacheStackResult {
  stackName: string;
  cache: CacheClusterDefinition;
}

export function createCacheStack(config: CacheStackConfig): CacheStackResult {
  if (config.numCacheClusters < 2) {
    throw new Error('Multi-AZ replication group requires at least 2 cache clusters (1 primary + 1 replica).');
  }

  if (!config.transitEncryptionEnabled) {
    throw new Error('Transit encryption must be enabled for ElastiCache Redis in-transit data protection.');
  }

  if (!config.atRestEncryptionEnabled) {
    throw new Error('At-rest encryption must be enabled for ElastiCache Redis data compliance.');
  }

  return {
    stackName: 'CacheStack',
    cache: {
      clusterId: config.clusterId,
      engine: 'redis',
      engineVersion: config.engineVersion,
      nodeType: config.nodeType,
      numCacheClusters: config.numCacheClusters,
      automaticFailoverEnabled: config.automaticFailoverEnabled,
      multiAzEnabled: config.multiAzEnabled,
      atRestEncryptionEnabled: config.atRestEncryptionEnabled,
      transitEncryptionEnabled: config.transitEncryptionEnabled,
      authTokenRequired: config.authTokenRequired,
      port: 6379,
    },
  };
}
