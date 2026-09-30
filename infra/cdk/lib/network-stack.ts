export interface NetworkStackConfig {
  vpcName: string;
  cidr: string;
  maxAzs: number;
  natGateways?: number;
}

export type SubnetType = 'public' | 'private' | 'isolated';

export interface SubnetDefinition {
  name: string;
  type: SubnetType;
  azIndex: number;
  cidr: string;
  hasDirectInternetAccess: boolean;
}

export interface SecurityGroupDefinition {
  id: string;
  name: string;
  description: string;
  inboundSources: string[];
}

export interface NetworkStackResult {
  stackName: string;
  vpc: {
    name: string;
    cidr: string;
    maxAzs: number;
  };
  subnets: SubnetDefinition[];
  securityGroups: {
    alb: SecurityGroupDefinition;
    app: SecurityGroupDefinition;
    data: SecurityGroupDefinition;
  };
}

export function createNetworkStack(config: NetworkStackConfig): NetworkStackResult {
  if (config.maxAzs < 2) {
    throw new Error('VPC must span across at least two Availability Zones for high availability.');
  }

  const cidrRegex = /^([0-9]{1,3}\.){3}[0-9]{1,3}\/[0-9]{1,2}$/;
  if (!cidrRegex.test(config.cidr)) {
    throw new Error(`Invalid CIDR block: ${config.cidr}`);
  }

  const subnets: SubnetDefinition[] = [];
  for (let az = 0; az < config.maxAzs; az++) {
    subnets.push({
      name: 'Public',
      type: 'public',
      azIndex: az,
      cidr: `10.0.${az * 16}.0/20`,
      hasDirectInternetAccess: true,
    });
    subnets.push({
      name: 'Application',
      type: 'private',
      azIndex: az,
      cidr: `10.0.${32 + az * 16}.0/20`,
      hasDirectInternetAccess: false,
    });
    subnets.push({
      name: 'IsolatedData',
      type: 'isolated',
      azIndex: az,
      cidr: `10.0.${64 + az * 16}.0/20`,
      hasDirectInternetAccess: false,
    });
  }

  const albSg: SecurityGroupDefinition = {
    id: 'sg-alb',
    name: 'campus247-alb-sg',
    description: 'Security group for public application load balancer',
    inboundSources: ['0.0.0.0/0'],
  };

  const appSg: SecurityGroupDefinition = {
    id: 'sg-app',
    name: 'campus247-app-sg',
    description: 'Security group for ECS application containers',
    inboundSources: [albSg.id],
  };

  const dataSg: SecurityGroupDefinition = {
    id: 'sg-data',
    name: 'campus247-data-sg',
    description: 'Security group for RDS PostgreSQL and ElastiCache Redis',
    inboundSources: [appSg.id],
  };

  return {
    stackName: 'NetworkStack',
    vpc: {
      name: config.vpcName,
      cidr: config.cidr,
      maxAzs: config.maxAzs,
    },
    subnets,
    securityGroups: {
      alb: albSg,
      app: appSg,
      data: dataSg,
    },
  };
}
