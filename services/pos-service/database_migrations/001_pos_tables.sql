-- POS Service Additional Tables
-- Customers table for customer management and loyalty

CREATE TABLE IF NOT EXISTS public.customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    email VARCHAR(255),
    phone VARCHAR(50),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255),
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0,
    loyalty_points INTEGER DEFAULT 0,
    last_visit TIMESTAMPTZ,
    notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Receipts table for receipt generation
CREATE TABLE IF NOT EXISTS public.receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    receipt_number VARCHAR(100) UNIQUE NOT NULL,
    receipt_data JSONB NOT NULL,
    generated_by UUID REFERENCES public.staff_members(id),
    generated_at TIMESTAMPTZ DEFAULT now()
);

-- Tax rules table for location-based tax calculation
CREATE TABLE IF NOT EXISTS public.tax_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    location_id UUID REFERENCES public.locations(id),
    name VARCHAR(100) NOT NULL,
    rate DECIMAL(5,4) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('vat', 'gst', 'sales_tax', 'service_tax')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_customers_business ON public.customers(business_id);
CREATE INDEX IF NOT EXISTS idx_customers_email ON public.customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON public.customers(phone);
CREATE INDEX IF NOT EXISTS idx_receipts_order ON public.receipts(order_id);
CREATE INDEX IF NOT EXISTS idx_receipts_number ON public.receipts(receipt_number);
CREATE INDEX IF NOT EXISTS idx_tax_rules_business ON public.tax_rules(business_id);
CREATE INDEX IF NOT EXISTS idx_tax_rules_location ON public.tax_rules(location_id);
CREATE INDEX IF NOT EXISTS idx_tax_rules_active ON public.tax_rules(is_active);

-- Update triggers
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_customers_timestamp
BEFORE UPDATE ON public.customers
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_tax_rules_timestamp
BEFORE UPDATE ON public.tax_rules
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

-- Row Level Security
ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tax_rules ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Business team can view customers"
    ON public.customers FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid() AND business_id = customers.business_id
    ));

CREATE POLICY "Business team can insert customers"
    ON public.customers FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid() AND business_id = customers.business_id
    ));

CREATE POLICY "Business team can update customers"
    ON public.customers FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid() AND business_id = customers.business_id
    ));

CREATE POLICY "Business team can view receipts"
    ON public.receipts FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.orders o
        JOIN public.user_business_roles ubr ON o.business_id = ubr.business_id
        WHERE o.id = receipts.order_id AND ubr.user_id = auth.uid()
    ));

CREATE POLICY "Business team can view tax rules"
    ON public.tax_rules FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid() AND business_id = tax_rules.business_id
    ));
