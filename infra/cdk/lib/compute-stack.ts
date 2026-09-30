export interface ServiceConfig {
  name: string;
  cpu: number;
  memoryLimitMiB: number;
  desiredCount: number;
  port?: number;
  healthCheckPath?: string;
}

export interface ComputeStackConfig {
  clusterName: string;
  assignPublicIp: boolean;
  services: ServiceConfig[];
}

export interface ComputeStackResult {
  stackName: string;
  clusterName: string;
  assignPublicIp: boolean;
  services: ServiceConfig[];
}

export function createComputeStack(config: ComputeStackConfig): ComputeStackResult {
  if (config.assignPublicIp) {
    throw new Error('ECS Fargate tasks must not be assigned public IP addresses. Must use private subnets.');
  }

  for (const svc of config.services) {
    if (svc.desiredCount < 2) {
      throw new Error(`Service ${svc.name}: desiredCount must be at least 2 for high availability.`);
    }
  }

  return {
    stackName: 'ComputeStack',
    clusterName: config.clusterName,
    assignPublicIp: false,
    services: [...config.services],
  };
}
