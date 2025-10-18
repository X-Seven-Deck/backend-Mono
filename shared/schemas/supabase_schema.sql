-- X-sevenAI Supabase Schema
-- This file defines the database structure for X-sevenAI

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types
CREATE TYPE user_role AS ENUM ('admin', 'business_owner', 'staff', 'customer');
CREATE TYPE subscription_status AS ENUM ('active', 'past_due', 'unpaid', 'canceled', 'incomplete', 'incomplete_expired', 'trialing');
CREATE TYPE invitation_status AS ENUM ('pending', 'accepted', 'expired');

-- Users Table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Business Categories Table (updated to match DB schema)
CREATE TABLE IF NOT EXISTS public.business_categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    icon_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Subscription Plans Table
CREATE TABLE IF NOT EXISTS public.subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    interval TEXT NOT NULL, -- 'month' or 'year'
    features JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Businesses Table
CREATE TABLE IF NOT EXISTS public.businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    category_id INTEGER NOT NULL REFERENCES public.business_categories(id),
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Business Profiles Table
CREATE TABLE IF NOT EXISTS public.business_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    address TEXT,
    phone TEXT,
    email TEXT,
    website TEXT,
    logo_url TEXT,
    settings JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(business_id)
);

-- Business Staff Table
CREATE TABLE IF NOT EXISTS public.business_staff (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role user_role NOT NULL,
    permissions JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(business_id, user_id)
);

-- Orders Table
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    order_number TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_amount DECIMAL(10, 2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    items JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Reservations Table
CREATE TABLE IF NOT EXISTS public.reservations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    reservation_number TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed',
    reservation_date TIMESTAMPTZ NOT NULL,
    party_size INTEGER NOT NULL,
    notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Business Details Table
CREATE TABLE IF NOT EXISTS public.business_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    postal_code TEXT,
    phone TEXT,
    email TEXT,
    operating_hours JSONB,
    social_links JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(business_id)
);

-- User Business Roles (Pivot Table)
CREATE TABLE IF NOT EXISTS public.user_business_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    role user_role NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, business_id)
);

-- Business Subscriptions Table
CREATE TABLE IF NOT EXISTS public.business_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES public.subscription_plans(id) ON DELETE RESTRICT,
    status subscription_status NOT NULL,
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT false,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- API Keys Table
CREATE TABLE IF NOT EXISTS public.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key TEXT NOT NULL UNIQUE,
    scopes TEXT[],
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Business Settings Table
CREATE TABLE IF NOT EXISTS public.business_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(business_id)
);

-- Business Invitations Table
CREATE TABLE IF NOT EXISTS public.business_invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role user_role NOT NULL,
    status invitation_status DEFAULT 'pending',
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES public.businesses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    metadata JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Chat Sessions Table
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES public.businesses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    title TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Chat Messages Table
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    is_ai BOOLEAN DEFAULT FALSE,
    content TEXT NOT NULL,
    attachments JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Analytics Events Table
CREATE TABLE IF NOT EXISTS public.analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES public.businesses(id) ON DELETE SET NULL,
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS Policies

-- Users: Users can read their own profile
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile" 
    ON public.users FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" 
    ON public.users FOR UPDATE 
    USING (auth.uid() = id);

-- Business Categories: Public read
ALTER TABLE public.business_categories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view business categories" 
    ON public.business_categories FOR SELECT 
    USING (true);

-- Subscription Plans: Public read
ALTER TABLE public.subscription_plans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view subscription plans" 
    ON public.subscription_plans FOR SELECT 
    USING (true);

-- Businesses: Public read, restricted write
ALTER TABLE public.businesses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view businesses" 
    ON public.businesses FOR SELECT 
    USING (true);

CREATE POLICY "Business owners can manage their business"
    ON public.businesses FOR ALL
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid()
        AND business_id = businesses.id
        AND role = 'business_owner'::user_role
    ));

-- Business Details: Public read, restricted write
ALTER TABLE public.business_details ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view business details"
    ON public.business_details FOR SELECT
    USING (true);

CREATE POLICY "Business owners can manage their business details"
    ON public.business_details FOR ALL
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid()
        AND business_id = business_details.business_id
        AND role = 'business_owner'::user_role
    ));

-- User Business Roles: Restricted access
ALTER TABLE public.user_business_roles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own roles"
    ON public.user_business_roles FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Business owners can manage roles for their business"
    ON public.user_business_roles FOR ALL
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles ubr
        WHERE ubr.user_id = auth.uid()
        AND ubr.business_id = user_business_roles.business_id
        AND ubr.role = 'business_owner'::user_role
    ));

-- Business Subscriptions: Restricted access
ALTER TABLE public.business_subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Business owners can view their subscriptions"
    ON public.business_subscriptions FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid()
        AND business_id = business_subscriptions.business_id
        AND role = 'business_owner'::user_role
    ));

-- API Keys: Restricted access
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Business team members can view API keys"
    ON public.api_keys FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid()
        AND business_id = api_keys.business_id
    ));

CREATE POLICY "Business owners can manage API keys"
    ON public.api_keys FOR ALL
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid()
        AND business_id = api_keys.business_id
        AND role = 'business_owner'::user_role
    ));

-- Business Settings: Restricted access
ALTER TABLE public.business_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Business team members can view settings"
    ON public.business_settings FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid()
        AND business_id = business_settings.business_id
    ));

CREATE POLICY "Business owners can manage settings"
    ON public.business_settings FOR ALL
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid()
        AND business_id = business_settings.business_id
        AND role = 'business_owner'::user_role
    ));

-- Business Profiles: Restricted access
ALTER TABLE public.business_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Business owners can view their business profiles"
    ON public.business_profiles FOR SELECT
    USING (owner_id = auth.uid());

CREATE POLICY "Business owners can manage their business profiles"
    ON public.business_profiles FOR ALL
    USING (owner_id = auth.uid());

-- Business Staff: Restricted access
ALTER TABLE public.business_staff ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Business staff can view their own staff records"
    ON public.business_staff FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Business owners can manage staff for their business"
    ON public.business_staff FOR ALL
    USING (EXISTS (
        SELECT 1 FROM public.business_profiles
        WHERE business_id = business_staff.business_id
        AND owner_id = auth.uid()
    ));

-- Orders: Customers and business owners can view
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Customers can view their orders"
    ON public.orders FOR SELECT
    USING (customer_id = auth.uid());

CREATE POLICY "Business owners can view their orders"
    ON public.orders FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.business_profiles
            WHERE business_id = orders.business_id AND owner_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM public.business_staff
            WHERE business_id = orders.business_id AND user_id = auth.uid()
        )
    );

CREATE POLICY "Business owners can manage their orders"
    ON public.orders FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.business_profiles
            WHERE business_id = orders.business_id AND owner_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM public.business_staff
            WHERE business_id = orders.business_id AND user_id = auth.uid()
        )
    );

-- Reservations: Customers and business owners can view
ALTER TABLE public.reservations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Customers can view their reservations"
    ON public.reservations FOR SELECT
    USING (customer_id = auth.uid());

CREATE POLICY "Business owners can view their reservations"
    ON public.reservations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.business_profiles
            WHERE business_id = reservations.business_id AND owner_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM public.business_staff
            WHERE business_id = reservations.business_id AND user_id = auth.uid()
        )
    );

CREATE POLICY "Business owners can manage their reservations"
    ON public.reservations FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.business_profiles
            WHERE business_id = reservations.business_id AND owner_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM public.business_staff
            WHERE business_id = reservations.business_id AND user_id = auth.uid()
        )
    );

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_timestamp
BEFORE UPDATE ON public.users
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_business_profiles_timestamp
BEFORE UPDATE ON public.business_profiles
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_businesses_timestamp
BEFORE UPDATE ON public.businesses
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_business_staff_timestamp
BEFORE UPDATE ON public.business_staff
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_chat_sessions_timestamp
BEFORE UPDATE ON public.chat_sessions
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_orders_timestamp
BEFORE UPDATE ON public.orders
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_reservations_timestamp
BEFORE UPDATE ON public.reservations
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

-- Indexes for better query performance
CREATE INDEX idx_users_created_at ON public.users(created_at);

-- Business indexes
CREATE INDEX idx_businesses_slug ON public.businesses(slug);
CREATE INDEX idx_businesses_category ON public.businesses(category_id);
CREATE INDEX idx_businesses_created_at ON public.businesses(created_at);

-- User Business Roles indexes
CREATE INDEX idx_user_business_roles_user ON public.user_business_roles(user_id);
CREATE INDEX idx_user_business_roles_business ON public.user_business_roles(business_id);
CREATE INDEX idx_user_business_roles_role ON public.user_business_roles(role);

-- Subscription indexes
CREATE INDEX idx_business_subscriptions_business ON public.business_subscriptions(business_id);
CREATE INDEX idx_business_subscriptions_status ON public.business_subscriptions(status);
CREATE INDEX idx_business_subscriptions_period ON public.business_subscriptions(current_period_start, current_period_end);

-- API Keys indexes
CREATE INDEX idx_api_keys_business ON public.api_keys(business_id);
CREATE INDEX idx_api_keys_key ON public.api_keys(key);

-- Business Invitations indexes
CREATE INDEX idx_business_invitations_business ON public.business_invitations(business_id);
CREATE INDEX idx_business_invitations_email ON public.business_invitations(email);
CREATE INDEX idx_business_invitations_token ON public.business_invitations(token);
CREATE INDEX idx_business_invitations_status ON public.business_invitations(status);

-- Audit Logs indexes
CREATE INDEX idx_audit_logs_business ON public.audit_logs(business_id);
CREATE INDEX idx_audit_logs_user ON public.audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON public.audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON public.audit_logs(action);

-- Chat and Analytics indexes
CREATE INDEX idx_chat_sessions_business ON public.chat_sessions(business_id);
CREATE INDEX idx_chat_sessions_user ON public.chat_sessions(user_id);
CREATE INDEX idx_chat_messages_session ON public.chat_messages(session_id);
CREATE INDEX idx_analytics_events_business ON public.analytics_events(business_id);
CREATE INDEX idx_analytics_events_created_at ON public.analytics_events(created_at);
CREATE INDEX idx_analytics_business ON public.analytics_events(business_id);
CREATE INDEX idx_analytics_event_type ON public.analytics_events(event_type);

-- Business Profiles indexes
CREATE INDEX idx_business_profiles_business ON public.business_profiles(business_id);
CREATE INDEX idx_business_profiles_owner ON public.business_profiles(owner_id);

-- Business Staff indexes
CREATE INDEX idx_business_staff_business ON public.business_staff(business_id);
CREATE INDEX idx_business_staff_user ON public.business_staff(user_id);
CREATE INDEX idx_business_staff_role ON public.business_staff(role);

-- Orders indexes
CREATE INDEX idx_orders_business ON public.orders(business_id);
CREATE INDEX idx_orders_customer ON public.orders(customer_id);
CREATE INDEX idx_orders_status ON public.orders(status);
CREATE INDEX idx_orders_created_at ON public.orders(created_at);

-- Reservations indexes
CREATE INDEX idx_reservations_business ON public.reservations(business_id);
CREATE INDEX idx_reservations_customer ON public.reservations(customer_id);
CREATE INDEX idx_reservations_date ON public.reservations(reservation_date);
CREATE INDEX idx_reservations_status ON public.reservations(status);

-- RPC Functions

-- Create user profile RPC function
CREATE OR REPLACE FUNCTION create_user_profile(profile_data JSONB)
RETURNS UUID AS $$
DECLARE
    user_id UUID;
    result UUID;
BEGIN
    -- Extract user ID from profile data
    user_id := (profile_data->>'id')::UUID;

    -- Insert user profile
    INSERT INTO public.users (
        id,
        full_name,
        avatar_url
    ) VALUES (
        user_id,
        profile_data->>'full_name',
        profile_data->>'avatar_url'
    ) ON CONFLICT (id) DO UPDATE SET
        full_name = EXCLUDED.full_name,
        avatar_url = EXCLUDED.avatar_url,
        updated_at = now();

    RETURN user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create business with owner RPC function
CREATE OR REPLACE FUNCTION create_business_with_owner(
    business_data JSONB,
    owner_id UUID
)
RETURNS JSONB AS $$
DECLARE
    business_id UUID;
    business_record RECORD;
    result JSONB;
BEGIN
    -- Create the business
    INSERT INTO public.businesses (
        name,
        slug,
        description
    ) VALUES (
        business_data->>'name',
        lower(regexp_replace(business_data->>'name', '[^a-zA-Z0-9]+', '-', 'g')),
        business_data->>'description'
    ) RETURNING id INTO business_id;

    -- Create business profile
    INSERT INTO public.business_profiles (
        business_id,
        owner_id,
        name,
        description,
        email,
        phone
    ) VALUES (
        business_id,
        owner_id,
        business_data->>'name',
        business_data->>'description',
        business_data->>'email',
        business_data->>'phone'
    );

    -- Add owner to business staff
    INSERT INTO public.business_staff (
        business_id,
        user_id,
        role
    ) VALUES (
        business_id,
        owner_id,
        'business_owner'::user_role
    );

    -- Add owner to user business roles
    INSERT INTO public.user_business_roles (
        user_id,
        business_id,
        role
    ) VALUES (
        owner_id,
        business_id,
        'business_owner'::user_role
    );

    -- Return the created business data
    SELECT jsonb_build_object(
        'id', b.id,
        'name', b.name,
        'slug', b.slug,
        'description', b.description,
        'owner_id', bp.owner_id,
        'created_at', b.created_at
    ) INTO result
    FROM public.businesses b
    JOIN public.business_profiles bp ON b.id = bp.business_id
    WHERE b.id = business_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
