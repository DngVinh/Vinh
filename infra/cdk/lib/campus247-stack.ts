export interface Campus247StackConfig {
  environment: 'staging' | 'production';
  region: string;
  account: string;
  encryptionEnabled: boolean;
  retentionDays: number;
  privateNetworkingOnly: boolean;
  policies?: {
    allowWildcardPermissions?: boolean;
  };
}

export interface ResourceDefinition {
  logicalId: string;
  type: string;
  encrypted: boolean;
  isolated: boolean;
}

export interface Campus247StackSynthesisResult {
  stackName: string;
  environment: string;
  region: string;
  account: string;
  encryption: {
    kmsKeyManaged: boolean;
    algorithm: string;
  };
  networking: {
    vpcCidr: string;
    isolatedDataSubnets: boolean;
  };
  resources: ResourceDefinition[];
  isDeployed: boolean;
  deploymentApprovalAttached: boolean;
}

export function synthesizeCampus247Stack(
  config: Campus247StackConfig
): Campus247StackSynthesisResult {
  // Gate 1: Mandatory at-rest encryption (SEC-CRYPTO-005)
  if (!config.encryptionEnabled) {
    throw new Error(
      'SEC-CRYPTO-005: Policy violation - At-rest encryption is mandatory for all persistent data stores.'
    );
  }

  // Gate 2: Least-privilege IAM, strictly no wildcard permissions (SEC-ARCH-001)
  if (config.policies?.allowWildcardPermissions) {
    throw new Error(
      "SEC-ARCH-001: Policy violation - Wildcard permissions '*' are strictly forbidden. Least privilege must be explicitly declared."
    );
  }

  // Gate 3: Private networking boundary (SEC-ARCH-003)
  if (!config.privateNetworkingOnly) {
    throw new Error(
      'SEC-ARCH-003: Policy violation - Public data paths are forbidden. Storage and database resources must reside in isolated/private subnets.'
    );
  }

  // Deterministic resource assembly without dynamic cloud lookups
  const resources: ResourceDefinition[] = [
    {
      logicalId: 'Campus247Vpc',
      type: 'AWS::EC2::VPC',
      encrypted: false,
      isolated: true,
    },
    {
      logicalId: 'PostgresDatabaseCluster',
      type: 'AWS::RDS::DBCluster',
      encrypted: true,
      isolated: true,
    },
    {
      logicalId: 'AppSecretsKey',
      type: 'AWS::KMS::Key',
      encrypted: true,
      isolated: true,
    },
    {
      logicalId: 'AuditLogBucket',
      type: 'AWS::S3::Bucket',
      encrypted: true,
      isolated: true,
    },
  ];

  return {
    stackName: 'Campus247CompositeStack',
    environment: config.environment,
    region: config.region,
    account: config.account,
    encryption: {
      kmsKeyManaged: true,
      algorithm: 'AES-256-GCM',
    },
    networking: {
      vpcCidr: '10.0.0.0/16',
      isolatedDataSubnets: true,
    },
    resources,
    // AC-03: Infrastructure changes remain un-deployed until explicitly promoted
    isDeployed: false,
    deploymentApprovalAttached: false,
  };
}
