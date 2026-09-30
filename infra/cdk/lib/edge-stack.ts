export interface RoutingRuleConfig {
  pathPattern: string;
  targetService: 'api' | 'web';
  port: number;
}

export interface EdgeStackConfig {
  albName: string;
  domainName: string;
  enableWaf: boolean;
  rateLimitPer5Min: number;
  routingRules: RoutingRuleConfig[];
  account?: string;
  region?: string;
}

export interface AlbDefinition {
  name: string;
  routingRules: RoutingRuleConfig[];
}

export interface CloudFrontDefinition {
  enabled: boolean;
  domainName: string;
  wafWebAclId: string;
}

export interface WafDefinition {
  rateLimitRuleEnabled: boolean;
  rateLimit: number;
}

export interface EdgeStackResult {
  stackName: string;
  alb: AlbDefinition;
  cloudFront: CloudFrontDefinition;
  waf: WafDefinition;
}

export function createEdgeStack(config: EdgeStackConfig): EdgeStackResult {
  if (!config.enableWaf) {
    throw new Error('AWS WAF must be enabled at edge for public traffic inspection.');
  }

  if (config.rateLimitPer5Min <= 0) {
    throw new Error('Rate limiting rule must specify a positive request threshold.');
  }

  const account = config.account || '123456789012';
  const webAclId = `arn:aws:wafv2:us-east-1:${account}:global/webacl/campus247-waf`;

  return {
    stackName: 'EdgeStack',
    alb: {
      name: config.albName,
      routingRules: [...config.routingRules],
    },
    cloudFront: {
      enabled: true,
      domainName: config.domainName,
      wafWebAclId: webAclId,
    },
    waf: {
      rateLimitRuleEnabled: true,
      rateLimit: config.rateLimitPer5Min,
    },
  };
}
