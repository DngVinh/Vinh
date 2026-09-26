export type EnvironmentName = 'dev' | 'staging' | 'prod';

export interface AppConfig {
  environment: EnvironmentName;
  region: string;
  account: string;
  institution?: string;
  dataMode?: 'synthetic_only' | 'live';
}

export interface GlobalTags {
  Project: string;
  Environment: string;
  Institution: string;
  DataMode: string;
  ManagedBy: string;
}

export interface AppManifest {
  version: string;
  environment: EnvironmentName;
  region: string;
  account: string;
  stacks: string[];
  tags: GlobalTags;
}

export function getGlobalTags(config: AppConfig): GlobalTags {
  return {
    Project: 'campus247',
    Environment: config.environment,
    Institution: config.institution || 'HUCE Demo',
    DataMode: config.dataMode || 'synthetic_only',
    ManagedBy: 'aws-cdk',
  };
}

export class CdkApp {
  readonly environment: EnvironmentName;
  readonly region: string;
  readonly account: string;
  readonly tags: GlobalTags;
  private readonly stackNames: string[] = [
    'FoundationStack',
    'NetworkStack',
    'DataStack',
    'CacheStack',
    'AsyncStack',
    'ComputeStack',
    'EdgeStack',
    'IamStack',
    'MonitoringStack',
  ];

  constructor(config: AppConfig) {
    const validEnvironments: EnvironmentName[] = ['dev', 'staging', 'prod'];
    if (!validEnvironments.includes(config.environment)) {
      throw new Error(`Invalid environment: ${config.environment}. Expected one of: ${validEnvironments.join(', ')}`);
    }
    if (!config.account || config.account.trim().length === 0) {
      throw new Error('Account ID must be specified and non-empty.');
    }

    this.environment = config.environment;
    this.region = config.region || 'ap-southeast-1';
    this.account = config.account;
    this.tags = getGlobalTags(config);
  }

  synth(): AppManifest {
    return {
      version: '1.0.0',
      environment: this.environment,
      region: this.region,
      account: this.account,
      stacks: [...this.stackNames],
      tags: this.tags,
    };
  }
}

export function createApp(config: AppConfig): CdkApp {
  return new CdkApp(config);
}
