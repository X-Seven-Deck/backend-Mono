
## Table of Contents
1. [Overview](#overview)
2. [Authentication Flow](#authentication-flow)
   - [Signup Flow](#signup-flow)
   - [Login Flow](#login-flow)
3. [Database Tables](#database-tables)
   - [1. Business Categories](#1-business-categories)
   - [2. Subscription Plans](#2-subscription-plans)
   - [3. Businesses](#3-businesses)
   - [4. Business Details](#4-business-details)
   - [5. Business Subscriptions](#5-business-subscriptions)
   - [6. User Business Roles](#6-user-business-roles)
   - [7. Business Settings](#7-business-settings)
   - [8. Business Invitations](#8-business-invitations)
   - [9. API Keys](#9-api-keys)
   - [10. Audit Logs](#10-audit-logs)
4. [Row Level Security (RLS)](#row-level-security-rls)
5. [Important Functions](#important-functions)
6. [Example Queries](#example-queries)

## Overview

This document outlines the database schema for the X7AI platform, focusing on business management, user roles, and subscription handling. The database is designed with security, scalability, and flexibility in mind.

## Authentication Flow

### Signup Flow

1. **User Registration**
   - User provides email and password
   - System creates auth record in `auth.users` (handled by Supabase Auth)
   - Email verification is sent (if enabled)

2. **Business Creation**
   - After email verification, user is prompted to create a business
   - System creates entries in:
     - `businesses` (core business info)
     - `business_details` (additional business info)
     - `user_business_roles` (set as 'owner')
     - `business_settings` (default settings)

3. **Subscription Setup**
   - User selects a subscription plan
   - System creates record in `business_subscriptions`
   - Payment is processed (via Stripe)
   - Business status set to 'active' on successful payment

### Login Flow

1. **User Authentication**
   - User provides email/password (or uses OAuth)
   - Supabase Auth validates credentials
   - JWT token is issued with user claims

2. **Session Initialization**
   - Frontend extracts user ID from JWT
   - Fetches user's businesses and roles
   - Sets up application state based on permissions

## Database Tables

### 1. Business Categories

Stores predefined business categories for classification.

```sql
business_categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    icon_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
)
```

**Relationships**:
- One-to-Many with `businesses` (category_id → id)

### 2. Subscription Plans

Defines available subscription tiers and pricing.

```sql
subscription_plans (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10, 2) NOT NULL,
    price_yearly DECIMAL(10, 2) NOT NULL,
    features JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    max_users INTEGER,
    max_storage_mb INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
)
```

### 3. Businesses

Core business information.

```sql
businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id TEXT GENERATED ALWAYS AS ('biz_' || lpad((id::text), 8, '0')) STORED,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    category_id INTEGER REFERENCES business_categories(id),
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
)
```

**Relationships**:
- Many-to-One with `business_categories` (category_id → id)
- One-to-One with `business_details` (id → business_id)
- One-to-Many with `business_subscriptions` (id → business_id)

### 4. Business Details

Additional business information (1:1 with businesses).

```sql
business_details (
    business_id UUID PRIMARY KEY REFERENCES businesses(id) ON DELETE CASCADE,
    description TEXT,
    website_url TEXT,
    logo_url TEXT,
    banner_url TEXT,
    address JSONB DEFAULT '{}'::jsonb,
    contact_email TEXT,
    contact_phone TEXT,
    timezone TEXT DEFAULT 'UTC',
    metadata JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
)
```

### 5. Business Subscriptions

Tracks subscription status and billing information.

```sql
business_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    plan_id INTEGER REFERENCES subscription_plans(id),
    status TEXT NOT NULL,
    billing_cycle TEXT NOT NULL,
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT false,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
)
```

### 6. User Business Roles

Manages user permissions within businesses.

```sql
user_business_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, business_id)
)
```

### 7. Business Settings

Stores configuration for each business.

```sql
business_settings (
    business_id UUID PRIMARY KEY REFERENCES businesses(id) ON DELETE CASCADE,
    notifications JSONB DEFAULT '{"email": true, "sms": false, "push": true}'::jsonb,
    preferences JSONB DEFAULT '{"locale": "en-US", "timezone": "UTC", "currency": "USD"}'::jsonb,
    business_hours JSONB DEFAULT '{}'::jsonb,
    integrations JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
)
```

### 8. Business Invitations

Tracks pending team member invitations.

```sql
business_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    invited_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(business_id, email)
)
```

### 9. API Keys

Manages API access for business integrations.

```sql
api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
)
```

### 10. Audit Logs

Tracks important system events.

```sql
audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
)
```

## Row Level Security (RLS)

### Businesses Table
```sql
-- Business owners and members can view their business
CREATE POLICY "Enable read access for business members"
    ON businesses FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM user_business_roles
        WHERE user_business_roles.business_id = businesses.id
        AND user_business_roles.user_id = auth.uid()
    ));
```

### Business Subscriptions
```sql
-- Only business owners can view subscription details
CREATE POLICY "Enable read for business owners"
    ON business_subscriptions FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM user_business_roles
        WHERE user_business_roles.business_id = business_subscriptions.business_id
        AND user_business_roles.user_id = auth.uid()
        AND user_business_roles.role IN ('owner', 'admin')
    ));
```

### User Business Roles
```sql
-- Users can view their own roles
CREATE POLICY "Users can view their own roles"
    ON user_business_roles FOR SELECT
    USING (auth.uid() = user_id);

-- Business owners can manage roles
CREATE POLICY "Business owners can manage roles"
    ON user_business_roles FOR ALL
    USING (EXISTS (
        SELECT 1 FROM user_business_roles owner_roles
        WHERE owner_roles.business_id = user_business_roles.business_id
        AND owner_roles.user_id = auth.uid()
        AND owner_roles.role = 'owner'
    ));
```

## Important Functions

### Create Business with Owner
```sql
CREATE OR REPLACE FUNCTION public.create_business_with_owner(
    business_name TEXT,
    category_name TEXT,
    user_email TEXT,
    user_display_name TEXT,
    business_description TEXT DEFAULT NULL
) RETURNS JSONB
-- Implementation details...
```

### Subscribe to Plan
```sql
CREATE OR REPLACE FUNCTION public.subscribe_to_plan(
    business_id_param UUID,
    plan_id_param INTEGER,
    billing_cycle_param TEXT,
    stripe_customer_id_param TEXT DEFAULT NULL,
    stripe_subscription_id_param TEXT DEFAULT NULL
) RETURNS JSONB
-- Implementation details...
```

## Example Queries

### Get User's Businesses with Roles
```sql
SELECT 
    b.id, b.name, b.slug, b.status,
    ubr.role,
    bs.status as subscription_status
FROM businesses b
JOIN user_business_roles ubr ON b.id = ubr.business_id
LEFT JOIN business_subscriptions bs ON b.id = bs.business_id
WHERE ubr.user_id = auth.uid();
```

### Get Business Team Members
```sql
SELECT 
    u.id, u.email, u.raw_user_meta_data->>'full_name' as name,
    ubr.role, ubr.created_at as member_since
FROM auth.users u
JOIN user_business_roles ubr ON u.id = ubr.user_id
WHERE ubr.business_id = 'business-uuid-here';
```

### Check User Permissions
```sql
SELECT EXISTS (
    SELECT 1 FROM user_business_roles
    WHERE business_id = 'business-uuid-here'
    AND user_id = auth.uid()
    AND role = ANY(ARRAY['owner', 'admin'])
) as has_admin_access;
```

### Get Business Subscription Status
```sql
SELECT 
    bs.status, bs.billing_cycle,
    bs.current_period_start, bs.current_period_end,
    sp.name as plan_name, sp.price_monthly, sp.price_yearly
FROM business_subscriptions bs
JOIN subscription_plans sp ON bs.plan_id = sp.id
WHERE bs.business_id = 'business-uuid-here';
```
---
*Last Updated: October 3, 2025*
