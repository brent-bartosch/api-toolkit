# Day AI Service - API Toolkit Integration

**Service Type**: TypeScript/Node.js (MCP-based)
**Token Cost**: ~500 tokens (MCP integration)
**Status**: ✅ Active

## Overview

Day AI is an AI-native CRM with MCP (Model Context Protocol) integration for natural language data access. Unlike other services in this toolkit (which are Python-based), Day AI uses a TypeScript SDK with MCP capabilities.

**Use Case**: Syncing Faire wholesale brands to CRM with comprehensive enrichment (Instagram, Facebook, website scraping).

## Architecture

```
┌──────────────────┐
│    Supabase      │ → Source of truth (brands, enrichment data)
│  (Python API)    │
└────────┬─────────┘
         ↓
┌──────────────────┐
│     Day AI       │ → Operational CRM (TypeScript SDK + MCP)
│  (TS/Node.js)    │
└────────┬─────────┘
         ↓
┌──────────────────┐
│   Smartlead      │ → Email delivery (webhooks back to Day AI)
└──────────────────┘
```

## Installation & Setup

### SDK Location
The Day AI TypeScript SDK is located in your Faire lead gen project:
```
/path/to/Project1/Faire_lead_gen/day-ai-integration/temp-sdk/
```

### Environment Variables
Add to your `.env` file:
```bash
# Day AI Configuration
DAY_AI_API_URL=https://api.day.ai
DAY_AI_CLIENT_ID=your_client_id
DAY_AI_CLIENT_SECRET=your_client_secret
DAY_AI_REFRESH_TOKEN=your_refresh_token
```

### Project Integration
```typescript
import { DayAIClient } from './temp-sdk/dist/src/index.js';
import * as dotenv from 'dotenv';

dotenv.config();

const client = new DayAIClient();
await client.mcpInitialize();  // Initialize MCP connection
```

## Quick Start

### 1. Create Organization
```typescript
const client = new DayAIClient();
await client.mcpInitialize();

const result = await client.mcpCallTool('create_or_update_person_organization', {
  objectType: 'native_organization',
  standardProperties: {
    domain: 'https://www.faire.com/brand/b_xxx',
    name: 'Brand Name',
    description: 'Brand description',
    city: 'Los Angeles',
    state: 'CA',
    country: 'USA',
    primaryPhoneNumber: '+1-555-0100',
    socialInstagram: 'https://instagram.com/brand'
  },
  customProperties: [
    { propertyId: 'ade15379-5f39-45cc-a20c-a7647e729da9', value: 'faire_upload' },  // Data Source
    { propertyId: 'ed789687-aba8-4096-9e12-a30ae788454c', value: 'b_xxx' },  // Faire Brand Token
    { propertyId: 'active_products_count', value: 7165 },  // Active Products
    { propertyId: 'number_of_reviews', value: 5764 }  // Reviews
  ]
});

if (result.success && !result.data?.isError) {
  console.log('✅ Organization created');
} else {
  console.log('❌ Failed:', result.error || result.data?.content?.[0]?.text);
}
```

### 2. Search Organizations
```typescript
const result = await client.mcpCallTool('search_objects', {
  description: 'Find all organizations with Faire as data source',
  queries: [{
    objectType: 'native_organization',
    filters: [
      {
        propertyId: 'ade15379-5f39-45cc-a20c-a7647e729da9',
        operator: 'eq',
        value: 'faire_upload'
      }
    ]
  }]
});

const content = result.data?.content?.[0]?.text;
const parsed = JSON.parse(content);
const organizations = parsed.native_organization?.results || [];
console.log(`Found ${organizations.length} Faire brands`);
```

### 3. Create Custom Property
```typescript
const result = await client.mcpCallTool('create_custom_property', {
  objectTypeId: 'native_organization',
  propertyId: 'your_property_id',
  name: 'Property Display Name',
  propertyTypeId: 'int',  // or 'textarea', 'url', 'datetime', 'boolean', 'float'
  description: 'What this property tracks',
  aiManaged: true,  // REQUIRED for API updates
  useWeb: false
});
```

## Common Operations

### Sync Faire Brands
Location: `/path/to/Project1/Faire_lead_gen/day-ai-integration/sync_companies.ts`

```bash
cd /path/to/Project1/Faire_lead_gen/day-ai-integration

# Test with 3 brands
npx ts-node sync_companies.ts --limit 3

# Dry run (preview)
npx ts-node sync_companies.ts --limit 10 --dry-run

# Full sync
npx ts-node sync_companies.ts --full
```

**Features**:
- Fetches from 3 Supabase tables (brands, brand_intelligence_unified, instagram_profiles)
- Merges enrichment data with priority logic
- Creates/updates organizations with 14 custom properties
- Handles Instagram followers, product counts, review counts

### Bulk Update Organizations
Location: `/path/to/Project1/Faire_lead_gen/day-ai-integration/bulk_update_gmail_orgs.ts`

```bash
# Tag Gmail-sourced organizations
npx ts-node bulk_update_gmail_orgs.ts
```

## Custom Properties Reference

### All 14 Properties

| Property ID | Name | Type | Purpose |
|---|---|---|---|
| `ade15379-5f39-45cc-a20c-a7647e729da9` | Data Source | textarea | Origin: "faire_upload" or "Gmail" |
| `a589781a-c5f0-4837-ac27-ebae7d1b4568` | Import Date | datetime | When org was added |
| `93d333ea-4129-4232-9d83-a4da6c84eeba` | Quality Tier | textarea | Elite, High Potential, Quality, Active |
| `f4daf74a-5962-42a1-9d14-3ebc1cac5bd7` | Sync Batch ID | textarea | Daily sync identifier |
| `ed789687-aba8-4096-9e12-a30ae788454c` | Faire Brand Token | textarea | b_xxxxxxxxxx format |
| `instagram_url` | Instagram URL | url | Brand Instagram profile |
| `facebook_url` | Facebook URL | url | Brand Facebook page |
| `linkedin_url` | LinkedIn URL | url | Brand LinkedIn page |
| `brand_category` | Brand Category | textarea | From Instagram |
| `website_url` | Website URL | url | Actual brand website |
| `instagram_followers` | Instagram Followers | int | Follower count |
| `faire_brand_url` | Faire Brand Page | url | Marketplace listing |
| `active_products_count` | Active Products | int | Faire product count |
| `number_of_reviews` | Number of Reviews | int | Faire review count |

**Full reference**: [CUSTOM_PROPERTIES_REFERENCE.md](/path/to/Project1/Faire_lead_gen/day-ai-integration/CUSTOM_PROPERTIES_REFERENCE.md)

## MCP Tools Available

### 1. create_or_update_person_organization
Create or update organizations/people

**Parameters**:
- `objectType`: "native_organization" or "native_person"
- `standardProperties`: {domain, name, description, city, state, country, ...}
- `customProperties`: [{ propertyId, value }, ...]

### 2. search_objects
Search for organizations/people

**Parameters**:
- `description`: Natural language description
- `queries`: [{ objectType, filters }]

### 3. create_custom_property
Define new custom property

**Parameters**:
- `objectTypeId`: "native_organization" or "native_person"
- `propertyId`: Unique identifier (snake_case)
- `name`: Display name
- `propertyTypeId`: 'textarea', 'int', 'url', 'datetime', 'boolean', 'float', 'picklist'
- `aiManaged`: **true** (required for API updates)
- `useWeb`: false

### 4. list_tools
List all available MCP tools

```typescript
const tools = await client.mcpListTools();
console.log(tools.data?.tools?.map(t => t.name));
```

## Field Mapping Strategy

### Domain Field (ObjectId)
**Use Faire marketplace URL as unique identifier**:
```typescript
domain: `https://www.faire.com/brand/${brand_token}`
```

**Store actual website separately**:
```typescript
{ propertyId: 'website_url', value: actualBrandWebsite }
```

**Rationale**: Every Faire brand has a unique, stable marketplace page, even if they don't have their own website yet.

### Name Priority
```typescript
name = brand.name || instagram_full_name || 'Unknown Brand'
```

**Rationale**: Use actual brand name (not Instagram display name which has emojis/trademarks).

### Description Priority
```typescript
description = instagram_biography || enrichment_description || default_text
```

**Rationale**: Instagram bios provide rich, consumer-facing descriptions.

## Best Practices

### 1. Always Check Result Success
```typescript
if (result.success && !result.data?.isError) {
  // Success
} else {
  // Handle error
  const error = result.error || result.data?.content?.[0]?.text;
  console.error(error);
}
```

### 2. Filter Null Values
```typescript
const customProperties = [
  { propertyId: 'instagram_url', value: brand.instagram_url || null },
  { propertyId: 'facebook_url', value: brand.facebook_url || null }
];

// Remove nulls before sending
const filtered = customProperties.filter(p => p.value !== null);
```

### 3. Use aiManaged Flag
All custom properties **MUST** have `aiManaged: true` to be updated via API.

### 4. Rate Limiting
```typescript
for (const brand of brands) {
  await syncBrand(brand);
  await delay(100);  // 100ms delay between requests
}
```

## Integration with Supabase

### Combined Workflow
```typescript
import { createClient } from '@supabase/supabase-js';
import { DayAIClient } from './temp-sdk/dist/src/index.js';

// 1. Fetch from Supabase
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);
const { data: brands } = await supabase
  .from('brands')
  .select('*')
  .order('number_of_reviews', { ascending: false })
  .limit(100);

// 2. Sync to Day AI
const dayClient = new DayAIClient();
await dayClient.mcpInitialize();

for (const brand of brands) {
  await dayClient.mcpCallTool('create_or_update_person_organization', {
    objectType: 'native_organization',
    standardProperties: {
      domain: `https://www.faire.com/brand/${brand.token}`,
      name: brand.name
    },
    customProperties: [
      { propertyId: 'active_products_count', value: brand.active_products_count },
      { propertyId: 'number_of_reviews', value: brand.number_of_reviews }
    ]
  });
}
```

## Token Efficiency

**MCP Integration Advantage**:
- Day AI MCP: ~500 tokens
- Traditional REST API docs: ~5,000+ tokens
- **Savings**: 10x more efficient

**Comparison with Python Services**:
- Supabase Python API: ~600 tokens
- Day AI TypeScript MCP: ~500 tokens
- Both are highly efficient for Claude Code

## Troubleshooting

### Authentication Errors
```
Error: Invalid refresh token
```
**Fix**: Refresh your tokens in `.env` file using Day AI dashboard.

### Custom Property Not Updating
**Check**:
1. Property has `aiManaged: true`
2. Property ID is correct (check spelling)
3. Value type matches property type
4. No null values being sent

### Organizations Not Found
**Use domain as search key**:
```typescript
// Search by domain (Faire brand URL)
filters: [{
  propertyId: 'domain',
  operator: 'eq',
  value: 'https://www.faire.com/brand/b_xxx'
}]
```

## Related Documentation

- **Day AI Integration README**: [/day-ai-integration/README.md](/path/to/Project1/Faire_lead_gen/day-ai-integration/README.md)
- **Custom Properties Reference**: [CUSTOM_PROPERTIES_REFERENCE.md](/path/to/Project1/Faire_lead_gen/day-ai-integration/CUSTOM_PROPERTIES_REFERENCE.md)
- **Day AI SDK**: https://github.com/day-ai/day-ai-sdk
- **Day AI MCP**: https://day.ai/mcp

## Example Scripts

All example scripts are in:
```
/path/to/Project1/Faire_lead_gen/day-ai-integration/
```

1. `sync_companies.ts` - Main sync script with full enrichment
2. `add_social_media_properties.ts` - Create social media custom properties
3. `add_product_review_properties.ts` - Create marketplace metric properties
4. `bulk_update_gmail_orgs.ts` - Tag Gmail organizations
5. `test_single_brand.js` - Test sync with one brand

## Support

- **Day AI Solutions Team**: solutions@day.ai
- **API Documentation**: https://docs.day.ai/api
- **MCP Documentation**: https://day.ai/mcp

---

**Note**: Day AI is the only TypeScript/Node.js service in this toolkit. All other services use Python. This is by design - Day AI's MCP integration provides superior Claude Code compatibility compared to traditional REST APIs.
