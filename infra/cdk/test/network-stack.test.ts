import { describe, it, expect } from 'vitest';
import { createNetworkStack, NetworkStackConfig } from '../lib/network-stack';

describe('TASK-INFRA-NET-001: VPC and Private Subnet Topology', () => {
  it('AC-01: should create 2-AZ VPC with public, private and isolated subnets and isolated security groups', () => {
    const config: NetworkStackConfig = {
      vpcName: 'campus247-vpc',
      cidr: '10.0.0.0/16',
      maxAzs: 2,
      natGateways: 2,
    };

    const stack = createNetworkStack(config);
    expect(stack).toBeDefined();
    expect(stack.vpc.name).toBe('campus247-vpc');
    expect(stack.vpc.cidr).toBe('10.0.0.0/16');
    expect(stack.vpc.maxAzs).toBe(2);

    // Subnets
    const subnetNames = stack.subnets.map(s => s.name);
    expect(subnetNames).toContain('Public');
    expect(subnetNames).toContain('Application');
    expect(subnetNames).toContain('IsolatedData');

    const isolatedSubnets = stack.subnets.filter(s => s.type === 'isolated');
    expect(isolatedSubnets.length).toBe(2); // 1 per AZ
    expect(isolatedSubnets.every(s => s.hasDirectInternetAccess === false)).toBe(true);

    // Security groups
    expect(stack.securityGroups.alb).toBeDefined();
    expect(stack.securityGroups.app).toBeDefined();
    expect(stack.securityGroups.data).toBeDefined();

    // Invariant: data SG must only accept traffic from app SG
    expect(stack.securityGroups.data.inboundSources).toContain(stack.securityGroups.app.id);
    expect(stack.securityGroups.data.inboundSources).not.toContain('0.0.0.0/0');
  });

  it('AC-02: failure path - should reject topology with fewer than 2 AZs or invalid CIDR', () => {
    expect(() => {
      createNetworkStack({
        vpcName: 'campus247-vpc',
        cidr: '10.0.0.0/16',
        maxAzs: 1,
        natGateways: 1,
      });
    }).toThrow(/VPC must span across at least two Availability Zones/i);

    expect(() => {
      createNetworkStack({
        vpcName: 'campus247-vpc',
        cidr: 'invalid-cidr',
        maxAzs: 2,
        natGateways: 2,
      });
    }).toThrow(/Invalid CIDR block/i);
  });
});
