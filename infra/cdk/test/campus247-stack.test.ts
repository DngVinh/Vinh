import { describe, it, expect } from 'vitest';
import {
  synthesizeCampus247Stack,
  Campus247StackConfig,
} from '../lib/campus247-stack';

describe('TASK-INFRA-CDK-002: Deterministic Synthesis & Policy Gates', () => {
  const baseConfig: Campus247StackConfig = {
    environment: 'staging',
    region: 'ap-southeast-1',
    account: '123456789012',
    encryptionEnabled: true,
    retentionDays: 30,
    privateNetworkingOnly: true,
  };

  it('AC-01: synthesizes deterministically without cloud credentials', () => {
    const synth1 = synthesizeCampus247Stack(baseConfig);
    const synth2 = synthesizeCampus247Stack(baseConfig);

    expect(synth1).toBeDefined();
    expect(synth1.stackName).toBe('Campus247CompositeStack');
    expect(synth1.resources.length).toBeGreaterThan(0);
    // Byte-for-byte deterministic identity
    expect(JSON.stringify(synth1)).toEqual(JSON.stringify(synth2));
  });

  it('AC-02: policy gate - fails when encryption is disabled', () => {
    const insecureConfig: Campus247StackConfig = {
      ...baseConfig,
      encryptionEnabled: false,
    };

    expect(() => synthesizeCampus247Stack(insecureConfig)).toThrow(
      /SEC-CRYPTO-005.*At-rest encryption is mandatory/i
    );
  });

  it('AC-02: policy gate - fails when wildcard permissions are requested', () => {
    const wildcardConfig: Campus247StackConfig = {
      ...baseConfig,
      policies: {
        allowWildcardPermissions: true,
      },
    };

    expect(() => synthesizeCampus247Stack(wildcardConfig)).toThrow(
      /SEC-ARCH-001.*Wildcard permissions '\*' are strictly forbidden/i
    );
  });

  it('AC-02: policy gate - fails when private networking is bypassed', () => {
    const publicConfig: Campus247StackConfig = {
      ...baseConfig,
      privateNetworkingOnly: false,
    };

    expect(() => synthesizeCampus247Stack(publicConfig)).toThrow(
      /SEC-ARCH-003.*Public data paths are forbidden/i
    );
  });

  it('AC-03: guarantees synthesized stack is marked un-deployed', () => {
    const synth = synthesizeCampus247Stack(baseConfig);
    expect(synth.isDeployed).toBe(false);
    expect(synth.deploymentApprovalAttached).toBe(false);
  });
});
