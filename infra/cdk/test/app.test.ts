import { describe, it, expect } from 'vitest';
import { createApp, getGlobalTags, AppConfig } from '../bin/app';

describe('TASK-INFRA-CDK-001: Pinned AWS CDK TypeScript Application', () => {
  it('AC-01: should synthesize cdk application with required stacks and metadata', () => {
    const config: AppConfig = {
      environment: 'staging',
      region: 'ap-southeast-1',
      account: '123456789012',
    };

    const app = createApp(config);
    expect(app).toBeDefined();
    expect(app.environment).toBe('staging');
    expect(app.region).toBe('ap-southeast-1');
    expect(app.account).toBe('123456789012');

    const manifest = app.synth();
    expect(manifest).toBeDefined();
    expect(manifest.stacks).toContain('NetworkStack');
    expect(manifest.stacks).toContain('DataStack');
    expect(manifest.stacks).toContain('ComputeStack');

    const tags = getGlobalTags(config);
    expect(tags.Project).toBe('campus247');
    expect(tags.DataMode).toBe('synthetic_only');
    expect(tags.Institution).toBe('HUCE Demo');
  });

  it('AC-02: failure path - should reject invalid environment or missing account', () => {
    expect(() => {
      createApp({
        environment: 'invalid-env' as any,
        region: 'ap-southeast-1',
        account: '123456789012',
      });
    }).toThrow(/Invalid environment/i);

    expect(() => {
      createApp({
        environment: 'prod',
        region: 'ap-southeast-1',
        account: '',
      });
    }).toThrow(/Account ID must be specified/i);
  });
});
