import { describe, it, expect } from 'vitest';
import { createEdgeStack, EdgeStackConfig } from '../lib/edge-stack';

describe('TASK-INFRA-EDGE-001: ALB, CloudFront and WAF Edge Topology', () => {
  it('AC-01: should configure ALB routing rules, CloudFront CDN and WAF WebACL with rate limiting', () => {
    const config: EdgeStackConfig = {
      albName: 'campus247-alb',
      domainName: 'campus247.huce.edu.vn',
      enableWaf: true,
      rateLimitPer5Min: 2000,
      routingRules: [
        { pathPattern: '/api/*', targetService: 'api', port: 8000 },
        { pathPattern: '/health/*', targetService: 'api', port: 8000 },
        { pathPattern: '/*', targetService: 'web', port: 3000 },
      ],
    };

    const stack = createEdgeStack(config);
    expect(stack).toBeDefined();
    expect(stack.alb.name).toBe('campus247-alb');
    expect(stack.alb.routingRules.length).toBe(3);

    // Invariant: /api/* routes to api service
    const apiRule = stack.alb.routingRules.find(r => r.pathPattern === '/api/*');
    expect(apiRule).toBeDefined();
    expect(apiRule?.targetService).toBe('api');

    // CloudFront and WAF
    expect(stack.cloudFront.enabled).toBe(true);
    expect(stack.cloudFront.wafWebAclId).toBeDefined();
    expect(stack.waf.rateLimitRuleEnabled).toBe(true);
    expect(stack.waf.rateLimit).toBe(2000);
  });

  it('AC-02: failure path - should reject disabled WAF or missing rate limiting', () => {
    expect(() => {
      createEdgeStack({
        albName: 'campus247-alb',
        domainName: 'campus247.huce.edu.vn',
        enableWaf: false, // Violation of SEC-CTRL-005
        rateLimitPer5Min: 2000,
        routingRules: [],
      });
    }).toThrow(/AWS WAF must be enabled at edge for public traffic/i);

    expect(() => {
      createEdgeStack({
        albName: 'campus247-alb',
        domainName: 'campus247.huce.edu.vn',
        enableWaf: true,
        rateLimitPer5Min: 0, // Violation
        routingRules: [],
      });
    }).toThrow(/Rate limiting rule must specify a positive request threshold/i);
  });
});
