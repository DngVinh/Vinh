import { describe, it, expect } from 'vitest';
import { createCacheStack, CacheStackConfig } from '../lib/cache-stack';

describe('TASK-INFRA-CACHE-001: ElastiCache Redis Cluster Topology', () => {
  it('AC-01: should configure Multi-AZ ElastiCache Redis replication group with encryption', () => {
    const config: CacheStackConfig = {
      clusterId: 'campus247-cache',
      engineVersion: '7.1',
      nodeType: 'cache.t4g.medium',
      numCacheClusters: 2,
      automaticFailoverEnabled: true,
      multiAzEnabled: true,
      atRestEncryptionEnabled: true,
      transitEncryptionEnabled: true,
      authTokenRequired: true,
    };

    const stack = createCacheStack(config);
    expect(stack).toBeDefined();
    expect(stack.cache.clusterId).toBe('campus247-cache');
    expect(stack.cache.engine).toBe('redis');
    expect(stack.cache.numCacheClusters).toBe(2);
    expect(stack.cache.automaticFailoverEnabled).toBe(true);
    expect(stack.cache.multiAzEnabled).toBe(true);
    expect(stack.cache.atRestEncryptionEnabled).toBe(true);
    expect(stack.cache.transitEncryptionEnabled).toBe(true);
    expect(stack.cache.port).toBe(6379);
  });

  it('AC-02: failure path - should reject single-node cluster or unencrypted in-transit cache', () => {
    expect(() => {
      createCacheStack({
        clusterId: 'campus247-cache',
        engineVersion: '7.1',
        nodeType: 'cache.t4g.medium',
        numCacheClusters: 1,
        automaticFailoverEnabled: true,
        multiAzEnabled: true,
        atRestEncryptionEnabled: true,
        transitEncryptionEnabled: true,
        authTokenRequired: true,
      });
    }).toThrow(/Multi-AZ replication group requires at least 2 cache clusters/i);

    expect(() => {
      createCacheStack({
        clusterId: 'campus247-cache',
        engineVersion: '7.1',
        nodeType: 'cache.t4g.medium',
        numCacheClusters: 2,
        automaticFailoverEnabled: true,
        multiAzEnabled: true,
        atRestEncryptionEnabled: true,
        transitEncryptionEnabled: false,
        authTokenRequired: true,
      });
    }).toThrow(/Transit encryption must be enabled/i);
  });
});
