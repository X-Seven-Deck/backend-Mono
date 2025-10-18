# X-sevenAI Database Schema Documentation

## Overview

This document provides comprehensive documentation for the X-sevenAI platform's database schema. The schema supports a multi-tenant SaaS platform with user management, business operations, order processing, reservations, chat functionality, and analytics.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Auth System   │    │   Business Mgmt  │    │   Operations    │
│   (Supabase)    │◄──►│   & Profiles     │◄──►│   & Analytics   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│     Users       │    │   Businesses     │    │     Orders      │
│   (profiles)    │    │   (entities)     │    │   (transactions)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Tables Documentation

---

## 1. Users Table (`public.users`)

**Purpose**: Extends Supabase's built-in `auth.users` table with additional profile information.

**Key Fields**:
- `id` (UUID) - References `auth.users(id)`
- `full_name` (TEXT) - User's complete name
- `avatar_url` (TEXT) - Profile picture URL
- `created_at` (TIMESTAMPTZ) - Account creation timestamp
- `updated_at` (TIMESTAMPTZ) - Last profile update

**Relationships**:
- Extends `auth.users` (1:1 relationship)
- Owns `business_profiles` (1:many)
- Member of `business_staff` (many:many via user_id)
- Creates `orders` (1:many)
- Makes `reservations` (1:many)
- Participates in `chat_sessions` (many:many)

**Security**: RLS enabled - users can only view/edit their own profiles

---

## 2. Businesses Table (`public.businesses`)

**Purpose**: Core business entities in the platform.

**Key Fields**:
- `id` (UUID) - Primary key
- `business_id` (TEXT) - Human-readable business identifier (auto-generated)
- `name` (TEXT) - Business name
- `slug` (TEXT) - URL-friendly identifier (unique)
- `category_id` (INTEGER) - References business categories
- `status` (TEXT) - Business status (pending, active, suspended, deactivated)

**Relationships**:
- Has one `business_details` (1:1)
- Has one `business_profiles` (1:1)
- Has many `business_staff` (1:many)
- Has many `orders` (1:many)
- Has many `reservations` (1:many)
- Has many `chat_sessions` (1:many)

**Security**: RLS enabled - business owners can manage their businesses

---

## 3. Business Profiles Table (`public.business_profiles`)

**Purpose**: Extended business information and ownership management.

**Key Fields**:
- `id` (UUID) - Primary key
- `business_id` (UUID) - References businesses table
- `owner_id` (UUID) - References users table (business owner)
- `name` (TEXT) - Business display name
- `description` (TEXT) - Business description
- `address` (TEXT) - Physical address
- `phone` (TEXT) - Contact phone number
- `email` (TEXT) - Contact email
- `website` (TEXT) - Business website
- `logo_url` (TEXT) - Logo image URL
- `settings` (JSONB) - Business-specific settings
- `is_active` (BOOLEAN) - Whether business is active

**Relationships**:
- Owned by `users` (many:1 via owner_id)
- Extends `businesses` (1:1 via business_id)
- Manages `business_staff` (1:many)

**Security**: RLS enabled - only business owners can view/manage their profiles

---

## 4. Business Staff Table (`public.business_staff`)

**Purpose**: Manages staff members and their roles within businesses.

**Key Fields**:
- `id` (UUID) - Primary key
- `business_id` (UUID) - References businesses table
- `user_id` (UUID) - References users table
- `role` (user_role ENUM) - Staff role (admin, business_owner, staff, customer)
- `permissions` (JSONB) - Specific permissions for the staff member
- `is_active` (BOOLEAN) - Whether staff member is active

**Relationships**:
- Belongs to `businesses` (many:1)
- References `users` (many:1)
- Maps to `user_business_roles` (1:1 relationship)

**Security**: RLS enabled - staff can view their own records, owners manage all staff

---

## 5. Orders Table (`public.orders`)

**Purpose**: Manages customer orders and transactions.

**Key Fields**:
- `id` (UUID) - Primary key
- `business_id` (UUID) - Business that received the order
- `customer_id` (UUID) - Customer who placed the order
- `order_number` (TEXT) - Human-readable order identifier (unique)
- `status` (TEXT) - Order status (pending, confirmed, processing, completed, cancelled)
- `total_amount` (DECIMAL) - Total order value
- `currency` (TEXT) - Currency code (default: USD)
- `items` (JSONB) - Array of order items with details
- `metadata` (JSONB) - Additional order information

**Relationships**:
- Belongs to `businesses` (many:1)
- Placed by `users` (many:1 via customer_id)

**Security**: RLS enabled - customers see their orders, business owners see all orders for their business

---

## 6. Reservations Table (`public.reservations`)

**Purpose**: Manages booking and reservation system.

**Key Fields**:
- `id` (UUID) - Primary key
- `business_id` (UUID) - Business being reserved
- `customer_id` (UUID) - Customer making the reservation
- `reservation_number` (TEXT) - Human-readable reservation identifier (unique)
- `status` (TEXT) - Reservation status (confirmed, pending, cancelled, completed)
- `reservation_date` (TIMESTAMPTZ) - Date and time of reservation
- `party_size` (INTEGER) - Number of people in the party
- `notes` (TEXT) - Special requests or notes
- `metadata` (JSONB) - Additional reservation information

**Relationships**:
- Belongs to `businesses` (many:1)
- Made by `users` (many:1 via customer_id)

**Security**: RLS enabled - customers see their reservations, business owners see all reservations for their business

---

## 7. Chat Sessions Table (`public.chat_sessions`)

**Purpose**: Manages chat conversations between users and businesses.

**Key Fields**:
- `id` (UUID) - Primary key
- `business_id` (UUID) - Business involved in the chat
- `user_id` (UUID) - Customer initiating the chat
- `title` (TEXT) - Chat session title/topic
- `metadata` (JSONB) - Chat session metadata
- `created_at` (TIMESTAMPTZ) - Session creation time
- `updated_at` (TIMESTAMPTZ) - Last activity time

**Relationships**:
- Belongs to `businesses` (many:1)
- Initiated by `users` (many:1)
- Contains many `chat_messages` (1:many)

**Security**: RLS enabled - participants and business owners can view chat sessions

---

## 8. Chat Messages Table (`public.chat_messages`)

**Purpose**: Stores individual messages within chat sessions.

**Key Fields**:
- `id` (UUID) - Primary key
- `session_id` (UUID) - References chat_sessions table
- `sender_id` (UUID) - User who sent the message
- `is_ai` (BOOLEAN) - Whether message is from AI assistant
- `content` (TEXT) - Message content
- `attachments` (JSONB) - File attachments metadata
- `created_at` (TIMESTAMPTZ) - Message timestamp

**Relationships**:
- Belongs to `chat_sessions` (many:1)
- Sent by `users` (many:1 via sender_id)

**Security**: RLS enabled - chat participants can view messages

---

## 9. Analytics Events Table (`public.analytics_events`)

**Purpose**: Tracks user interactions and business metrics.

**Key Fields**:
- `id` (UUID) - Primary key
- `business_id` (UUID) - Business being tracked
- `user_id` (UUID) - User performing the action
- `event_type` (TEXT) - Type of event (page_view, button_click, form_submit, etc.)
- `event_data` (JSONB) - Detailed event information
- `created_at` (TIMESTAMPTZ) - Event timestamp

**Relationships**:
- Belongs to `businesses` (many:1)
- Performed by `users` (many:1)

**Security**: RLS enabled - business owners can view their analytics data

---

## 10. Business Categories Table (`public.business_categories`) (Updated to match DB schema as of 2025-10-03 - Changed id to SERIAL, icon to icon_url, removed updated_at, added RLS policy for public read access)

**Purpose**: Categorizes businesses by type/industry.

**Key Fields** (Updated to match current DB schema):
- `id` (SERIAL) - Primary key (auto-increment)
- `name` (TEXT) - Category name
- `description` (TEXT) - Category description
- `icon_url` (TEXT) - Category icon image URL
- `created_at` (TIMESTAMPTZ) - Creation timestamp

**Relationships**:
- Referenced by `businesses` (1:many via category_id)

**Security**: Public read access - anyone can view categories

---

## 11. Subscription Plans Table (`public.subscription_plans`) (Updated to match DB schema - Added RLS policy for public read access)

**Purpose**: Defines available subscription tiers and pricing.

**Key Fields** (Updated to match current DB schema):
- `id` (UUID) - Primary key
- `name` (TEXT) - Plan name
- `description` (TEXT) - Plan description
- `price` (DECIMAL) - Plan price
- `interval` (TEXT) - Billing interval ('month' or 'year')
- `features` (JSONB) - Array of plan features
- `is_active` (BOOLEAN) - Whether plan is available
- `created_at` (TIMESTAMPTZ) - Creation timestamp
- `updated_at` (TIMESTAMPTZ) - Last update timestamp

**Security**: RLS enabled - public read access for all users

---

## 12. Business Subscriptions Table (`public.business_subscriptions`) (Updated to match DB schema - Added RLS policy for business owner access)

**Purpose**: Tracks business subscription status and billing.

**Key Fields** (Updated to match current DB schema):
- `id` (UUID) - Primary key
- `business_id` (UUID) - Subscribed business
- `plan_id` (UUID) - References subscription plan
- `status` (subscription_status ENUM) - Subscription status
- `current_period_start` (TIMESTAMPTZ) - Current billing period start
- `current_period_end` (TIMESTAMPTZ) - Current billing period end
- `cancel_at_period_end` (BOOLEAN) - Auto-cancel at period end
- `stripe_customer_id` (TEXT) - Stripe customer ID
- `stripe_subscription_id` (TEXT) - Stripe subscription ID
- `created_at` (TIMESTAMPTZ) - Creation timestamp
- `updated_at` (TIMESTAMPTZ) - Last update timestamp

**Relationships**:
- Belongs to `businesses` (many:1)
- References `subscription_plans` (many:1)

**Security**: RLS enabled - business owners can view their subscriptions

---

## 13. User Business Roles Table (`public.user_business_roles`) (Updated to match DB schema - role column is TEXT, added RLS policies for role management)

**Purpose**: Pivot table managing user roles across multiple businesses.

**Key Fields** (Updated to match current DB schema):
- `id` (UUID) - Primary key
- `user_id` (UUID) - References users table
- `business_id` (UUID) - References businesses table
- `role` (TEXT) - User role ('admin', 'business_owner', 'staff', 'customer')
- `created_at` (TIMESTAMPTZ) - Role assignment time
- `updated_at` (TIMESTAMPTZ) - Last role update

**Relationships**:
- References `users` (many:1)
- References `businesses` (many:1)
- Unique constraint on (user_id, business_id)

**Security**: RLS enabled - users see their own roles, business owners manage all roles

---

## 14. Business Details Table (`public.business_details`)

**Purpose**: Extended business information and settings.

**Key Fields**:
- `business_id` (UUID) - Primary key (references businesses)
- `description` (TEXT) - Detailed business description
- `website_url` (TEXT) - Business website
- `logo_url` (TEXT) - Logo image URL
- `banner_url` (TEXT) - Banner image URL
- `address` (JSONB) - Structured address information
- `contact_email` (TEXT) - Primary contact email
- `contact_phone` (TEXT) - Primary contact phone
- `timezone` (TEXT) - Business timezone
- `metadata` (JSONB) - Additional business data

**Relationships**:
- Extends `businesses` (1:1 relationship)

**Security**: Public read access for basic info, restricted write access

---

## 15. Business Settings Table (`public.business_settings`)

**Purpose**: Business-specific configuration and preferences.

**Key Fields**:
- `business_id` (UUID) - Primary key (references businesses)
- `notifications` (JSONB) - Notification preferences
- `preferences` (JSONB) - Business preferences (locale, currency, timezone)
- `business_hours` (JSONB) - Operating hours configuration
- `integrations` (JSONB) - Third-party integrations

**Relationships**:
- Belongs to `businesses` (1:1)

**Security**: RLS enabled - business team members can view, owners can manage

---

## 16. Business Invitations Table (`public.business_invitations`)

**Purpose**: Manages invitations for users to join businesses.

**Key Fields**:
- `id` (UUID) - Primary key
- `business_id` (UUID) - Business being invited to
- `email` (TEXT) - Email address of invitee
- `role` (TEXT) - Role being offered (admin, staff)
- `token` (TEXT) - Unique invitation token (unique)
- `expires_at` (TIMESTAMPTZ) - Invitation expiration time
- `invited_by` (UUID) - User who sent the invitation

**Relationships**:
- Belongs to `businesses` (many:1)
- Sent by `users` (many:1 via invited_by)

**Security**: RLS enabled - users see their own invitations, business owners manage invitations

---

## 17. API Keys Table (`public.api_keys`) (Updated to match DB schema - added scopes and expiration, updated RLS policies)

**Purpose**: Manages API keys for business integrations.

**Key Fields** (Updated to match current DB schema):
- `id` (UUID) - Primary key
- `business_id` (UUID) - Business the key belongs to
- `name` (TEXT) - Human-readable key name
- `key` (TEXT) - API key value (unique)
- `scopes` (TEXT[]) - Array of allowed scopes
- `expires_at` (TIMESTAMPTZ) - Key expiration time
- `last_used_at` (TIMESTAMPTZ) - Last usage timestamp
- `created_at` (TIMESTAMPTZ) - Creation timestamp
- `updated_at` (TIMESTAMPTZ) - Last update timestamp

**Relationships**:
- Belongs to `businesses` (many:1)
- Created by `users` (many:1)

**Security**: RLS enabled - business team members can view, owners can manage

---

## 18. Audit Logs Table (`public.audit_logs`)

**Purpose**: Tracks all important actions and changes in the system.

**Key Fields**:
- `id` (UUID) - Primary key
- `business_id` (UUID) - Business context (nullable for system-wide events)
- `user_id` (UUID) - User who performed the action
- `action` (TEXT) - Action performed (create, update, delete, login, etc.)
- `resource_type` (TEXT) - Type of resource affected
- `resource_id` (TEXT) - ID of affected resource
- `metadata` (JSONB) - Additional context data
- `ip_address` (INET) - IP address of the user
- `user_agent` (TEXT) - Browser/client information

**Relationships**:
- Related to `businesses` (many:1)
- Performed by `users` (many:1)

**Security**: RLS enabled - business team members can view their business audit logs

---

## Data Flow Architecture

### User Registration Flow
```
1. User signs up via Supabase Auth
2. create_user_profile() RPC function called
3. Profile created in public.users table
4. User can now access platform features
```

### Business Creation Flow
```
1. Authenticated user initiates business creation
2. create_business_with_owner() RPC function called
3. Business record created in businesses table
4. Business profile created in business_profiles table
5. Owner added to business_staff table
6. User-business role mapping created
7. Business is ready for operations
```

### Order Processing Flow
```
1. Customer browses business services
2. Customer places order via frontend
3. Order record created in orders table
4. Business owner notified
5. Order status updated through workflow
6. Audit log entry created for tracking
```

### Staff Management Flow
```
1. Business owner invites staff member
2. Invitation created in business_invitations table
3. Staff member accepts invitation
4. Staff record created in business_staff table
5. Role mapping created in user_business_roles table
6. Staff member can now access business resources
```

## Security Model

### Row Level Security (RLS) - All Tables Now Protected
- **Status**: ✅ **Fully Implemented** - All 18 tables have RLS enabled with comprehensive policies
- **Coverage**: Users can only access data they own or have explicit permission to view
- **Implementation**: PostgreSQL RLS policies automatically enforce access control at database level
- **Recent Update**: All missing policies applied on 2025-10-03, resolving previous unprotected tables issue

### Permission Hierarchy
```
Super Admin > Business Owner > Business Admin > Staff > Customer
```

### Data Isolation
- Business data is completely isolated between businesses
- Users can only see data from businesses they belong to
- Cross-business data access is explicitly prevented

## Performance Considerations

### Indexing Strategy
- **Primary keys**: All tables use UUID primary keys
- **Foreign keys**: Indexed for fast joins
- **Common queries**: Indexed (status, created_at, business_id, user_id)
- **Unique constraints**: Indexed automatically

### Query Optimization
- **Business-specific queries**: Use business_id indexes
- **User-specific queries**: Use user_id indexes
- **Time-based queries**: Use created_at indexes
- **Status filtering**: Use status indexes

## Maintenance & Monitoring

### Audit Trail
- All important actions logged in `audit_logs` table
- Includes user context, IP address, and metadata
- Helps with debugging and compliance

### Analytics Collection
- User interactions tracked in `analytics_events` table
- Business metrics calculated from order and reservation data
- Performance monitoring through query statistics

---

*This documentation provides a complete overview of the X-sevenAI database schema, its purpose, relationships, and operational flow. For technical implementation details, refer to the actual SQL schema files.*
