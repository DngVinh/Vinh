import { describe, it, expect } from 'vitest';
import { createComputeStack, ComputeStackConfig } from '../lib/compute-stack';

describe('TASK-INFRA-COMPUTE-001: ECS Fargate Task Definitions', () => {
  it('AC-01: should configure ECS Fargate services in private subnets with no public IPs', () => {
    const config: ComputeStackConfig = {
      clusterName: 'campus247-cluster',
      assignPublicIp: false,
      services: [
        {
          name: 'api',
          cpu: 512,
          memoryLimitMiB: 1024,
          desiredCount: 2,
          port: 8000,
          healthCheckPath: '/health/live',
        },
        {
          name: 'worker',
          cpu: 512,
          memoryLimitMiB: 1024,
          desiredCount: 2,
        },
      ],
    };

    const stack = createComputeStack(config);
    expect(stack).toBeDefined();
    expect(stack.clusterName).toBe('campus247-cluster');
    expect(stack.assignPublicIp).toBe(false);
    expect(stack.services.length).toBe(2);

    const apiService = stack.services.find(s => s.name === 'api');
    expect(apiService).toBeDefined();
    expect(apiService?.cpu).toBe(512);
    expect(apiService?.memoryLimitMiB).toBe(1024);
    expect(apiService?.desiredCount).toBe(2);
    expect(apiService?.port).toBe(8000);
    expect(apiService?.healthCheckPath).toBe('/health/live');

    const workerService = stack.services.find(s => s.name === 'worker');
    expect(workerService).toBeDefined();
    expect(workerService?.desiredCount).toBe(2);
    expect(workerService?.port).toBeUndefined(); // Worker has no ingress port
  });

  it('AC-02: failure path - should reject public IP assignment or insufficient desired count', () => {
    expect(() => {
      createComputeStack({
        clusterName: 'campus247-cluster',
        assignPublicIp: true, // Violation!
        services: [
          {
            name: 'api',
            cpu: 512,
            memoryLimitMiB: 1024,
            desiredCount: 2,
            port: 8000,
          },
        ],
      });
    }).toThrow(/ECS Fargate tasks must not be assigned public IP addresses/i);

    expect(() => {
      createComputeStack({
        clusterName: 'campus247-cluster',
        assignPublicIp: false,
        services: [
          {
            name: 'api',
            cpu: 512,
            memoryLimitMiB: 1024,
            desiredCount: 1, // Violation of HA
            port: 8000,
          },
        ],
      });
    }).toThrow(/desiredCount must be at least 2 for high availability/i);
  });
});
