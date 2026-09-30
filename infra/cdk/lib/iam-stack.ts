export interface PolicyStatement {
  effect: 'Allow' | 'Deny';
  actions: string[];
  resources: string[];
}

export interface IamRoleDefinition {
  roleName: string;
  assumedBy: string;
  statements: PolicyStatement[];
}

export interface IamStackConfig {
  account: string;
  region: string;
  kmsKeyArn?: string;
  outboxQueueArn?: string;
  knowledgeBucketArn?: string;
  customStatements?: PolicyStatement[];
}

export interface IamStackResult {
  stackName: string;
  roles: {
    executionRole: IamRoleDefinition;
    apiTaskRole: IamRoleDefinition;
    workerTaskRole: IamRoleDefinition;
  };
}

const ECS_TASK_ASSUME_ROLE_PRINCIPAL = 'ecs-tasks.amazonaws.com';

function validateNoWildcards(statements: PolicyStatement[]): void {
  for (const stmt of statements) {
    for (const act of stmt.actions) {
      if (act === '*' || act.startsWith('*:')) {
        throw new Error('Wildcard action or resource is prohibited in least-privilege IAM policies.');
      }
    }
    for (const res of stmt.resources) {
      if (res === '*' || res === 'arn:aws:*:*:*:*') {
        throw new Error('Wildcard action or resource is prohibited in least-privilege IAM policies.');
      }
    }
  }
}

export function createIamStack(config: IamStackConfig): IamStackResult {
  if (config.customStatements) {
    validateNoWildcards(config.customStatements);
  }

  const defaultOutboxArn = `arn:aws:sqs:${config.region}:${config.account}:campus247-outbox`;

  const executionStatements: PolicyStatement[] = [
    {
      effect: 'Allow',
      actions: ['ecr:GetAuthorizationToken', 'ecr:BatchCheckLayerAvailability', 'ecr:GetDownloadUrlForLayer', 'ecr:BatchGetImage'],
      resources: [`arn:aws:ecr:${config.region}:${config.account}:repository/campus247/*`],
    },
    {
      effect: 'Allow',
      actions: ['logs:CreateLogStream', 'logs:PutLogEvents'],
      resources: [`arn:aws:logs:${config.region}:${config.account}:log-group:/ecs/campus247*`],
    },
  ];

  const apiStatements: PolicyStatement[] = [
    {
      effect: 'Allow',
      actions: ['kms:Decrypt', 'kms:GenerateDataKey'],
      resources: [config.kmsKeyArn || `arn:aws:kms:${config.region}:${config.account}:key/default`],
    },
    {
      effect: 'Allow',
      actions: ['sqs:SendMessage', 'sqs:GetQueueAttributes'],
      resources: [config.outboxQueueArn || defaultOutboxArn],
    },
  ];

  const workerStatements: PolicyStatement[] = [
    {
      effect: 'Allow',
      actions: ['sqs:ReceiveMessage', 'sqs:DeleteMessage', 'sqs:GetQueueAttributes'],
      resources: [config.outboxQueueArn || defaultOutboxArn],
    },
    {
      effect: 'Allow',
      actions: ['s3:GetObject', 's3:PutObject'],
      resources: [`${config.knowledgeBucketArn || 'arn:aws:s3:::campus247-knowledge'}/*`],
    },
  ];

  validateNoWildcards([...executionStatements, ...apiStatements, ...workerStatements]);

  return {
    stackName: 'IamStack',
    roles: {
      executionRole: {
        roleName: 'campus247-ecs-execution-role',
        assumedBy: ECS_TASK_ASSUME_ROLE_PRINCIPAL,
        statements: executionStatements,
      },
      apiTaskRole: {
        roleName: 'campus247-api-task-role',
        assumedBy: ECS_TASK_ASSUME_ROLE_PRINCIPAL,
        statements: apiStatements,
      },
      workerTaskRole: {
        roleName: 'campus247-worker-task-role',
        assumedBy: ECS_TASK_ASSUME_ROLE_PRINCIPAL,
        statements: workerStatements,
      },
    },
  };
}
