-- X-sevenAI Enterprise Dashboard Schema Extensions
-- Square-like functionality for Food & Hospitality
-- This extends the base supabase_schema.sql with enterprise features

-- ============================================================================
-- MENU MANAGEMENT SYSTEM
-- ============================================================================

-- Menu Categories (hierarchical)
CREATE TABLE IF NOT EXISTS public.menu_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES public.menu_categories(id) ON DELETE SET NULL,
    display_order INTEGER DEFAULT 0,
    icon_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Menu Items
CREATE TABLE IF NOT EXISTS public.menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    category_id UUID REFERENCES public.menu_categories(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    cost DECIMAL(10,2),
    image_url VARCHAR(500),
    sku VARCHAR(100),
    barcode VARCHAR(100),
    is_available BOOLEAN DEFAULT true,
    prep_time INTEGER,
    calories INTEGER,
    allergens TEXT[],
    tags TEXT[],
    variants JSONB DEFAULT '[]'::jsonb,
    modifiers JSONB DEFAULT '[]'::jsonb,
    availability_schedule JSONB,
    locations UUID[],
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Item Modifiers (toppings, customizations)
CREATE TABLE IF NOT EXISTS public.item_modifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'single', 'multiple'
    required BOOLEAN DEFAULT false,
    min_selections INTEGER DEFAULT 0,
    max_selections INTEGER,
    options JSONB NOT NULL, -- [{name, price, default}]
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Item Modifier Assignments
CREATE TABLE IF NOT EXISTS public.item_modifier_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES public.menu_items(id) ON DELETE CASCADE,
    modifier_id UUID NOT NULL REFERENCES public.item_modifiers(id) ON DELETE CASCADE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(item_id, modifier_id)
);

-- ============================================================================
-- INVENTORY MANAGEMENT SYSTEM
-- ============================================================================

-- Inventory Items
CREATE TABLE IF NOT EXISTS public.inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sku VARCHAR(100),
    unit VARCHAR(50) NOT NULL, -- 'kg', 'lbs', 'units', etc.
    current_stock DECIMAL(10,2) NOT NULL DEFAULT 0,
    min_stock DECIMAL(10,2) NOT NULL DEFAULT 0, -- reorder point
    max_stock DECIMAL(10,2),
    unit_cost DECIMAL(10,2),
    supplier_id UUID REFERENCES public.suppliers(id),
    location_id UUID REFERENCES public.locations(id),
    category VARCHAR(100),
    is_tracked BOOLEAN DEFAULT true,
    last_counted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Inventory Transactions (audit trail)
CREATE TABLE IF NOT EXISTS public.inventory_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    inventory_item_id UUID NOT NULL REFERENCES public.inventory_items(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- 'purchase', 'sale', 'adjustment', 'transfer', 'waste'
    quantity DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(10,2),
    reference_type VARCHAR(50), -- 'order', 'purchase_order', 'manual'
    reference_id UUID,
    notes TEXT,
    performed_by UUID REFERENCES public.users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Stock Alerts
CREATE TABLE IF NOT EXISTS public.stock_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    inventory_item_id UUID NOT NULL REFERENCES public.inventory_items(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL, -- 'low_stock', 'out_of_stock', 'expiring'
    threshold DECIMAL(10,2),
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Suppliers
CREATE TABLE IF NOT EXISTS public.suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    website VARCHAR(500),
    payment_terms TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Purchase Orders
CREATE TABLE IF NOT EXISTS public.purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    supplier_id UUID NOT NULL REFERENCES public.suppliers(id) ON DELETE RESTRICT,
    order_number VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- 'draft', 'sent', 'confirmed', 'received', 'cancelled'
    order_date TIMESTAMPTZ NOT NULL,
    expected_delivery_date TIMESTAMPTZ,
    actual_delivery_date TIMESTAMPTZ,
    total_amount DECIMAL(10,2) NOT NULL,
    items JSONB NOT NULL,
    notes TEXT,
    created_by UUID REFERENCES public.users(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- OPERATIONS MANAGEMENT (Tables, Kitchen, Floor Plans)
-- ============================================================================

-- Locations (for multi-location businesses)
CREATE TABLE IF NOT EXISTS public.locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(255),
    timezone VARCHAR(100) DEFAULT 'UTC',
    settings JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Floor Plans
CREATE TABLE IF NOT EXISTS public.floor_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    location_id UUID REFERENCES public.locations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    layout JSONB NOT NULL, -- SVG/canvas data for visual layout
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Tables
CREATE TABLE IF NOT EXISTS public.tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    location_id UUID REFERENCES public.locations(id) ON DELETE CASCADE,
    floor_plan_id UUID REFERENCES public.floor_plans(id) ON DELETE SET NULL,
    table_number VARCHAR(50) NOT NULL,
    capacity INTEGER NOT NULL,
    position JSONB, -- {x, y} coordinates on floor plan
    shape VARCHAR(50), -- 'circle', 'square', 'rectangle'
    status VARCHAR(50) DEFAULT 'available', -- 'available', 'occupied', 'reserved', 'cleaning'
    current_order_id UUID REFERENCES public.orders(id),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Kitchen Display System (KDS) Orders
CREATE TABLE IF NOT EXISTS public.kds_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    station VARCHAR(100), -- 'grill', 'fryer', 'salad', 'bar'
    items JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'preparing', 'ready', 'served'
    priority INTEGER DEFAULT 0,
    prep_start_time TIMESTAMPTZ,
    prep_end_time TIMESTAMPTZ,
    target_time TIMESTAMPTZ,
    assigned_to UUID REFERENCES public.staff_members(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- STAFF MANAGEMENT
-- ============================================================================

-- Staff Members (extends business_staff)
CREATE TABLE IF NOT EXISTS public.staff_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    employee_id VARCHAR(100),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    position VARCHAR(100),
    department VARCHAR(100),
    hourly_rate DECIMAL(10,2),
    hire_date DATE,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'terminated'
    permissions JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Staff Schedules
CREATE TABLE IF NOT EXISTS public.staff_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    staff_id UUID NOT NULL REFERENCES public.staff_members(id) ON DELETE CASCADE,
    location_id UUID REFERENCES public.locations(id),
    shift_date DATE NOT NULL,
    shift_start TIME NOT NULL,
    shift_end TIME NOT NULL,
    break_duration INTEGER, -- minutes
    position VARCHAR(100),
    notes TEXT,
    status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'confirmed', 'cancelled'
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Time Clock (clock in/out)
CREATE TABLE IF NOT EXISTS public.time_clock (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    staff_id UUID NOT NULL REFERENCES public.staff_members(id) ON DELETE CASCADE,
    clock_in TIMESTAMPTZ NOT NULL,
    clock_out TIMESTAMPTZ,
    break_start TIMESTAMPTZ,
    break_end TIMESTAMPTZ,
    total_hours DECIMAL(5,2),
    overtime_hours DECIMAL(5,2),
    location_id UUID REFERENCES public.locations(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- ENHANCED ORDERS & PAYMENTS
-- ============================================================================

-- Order Items (detailed breakdown)
CREATE TABLE IF NOT EXISTS public.order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    menu_item_id UUID REFERENCES public.menu_items(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    modifiers JSONB DEFAULT '[]'::jsonb,
    special_instructions TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Payments
CREATE TABLE IF NOT EXISTS public.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    order_id UUID REFERENCES public.orders(id) ON DELETE SET NULL,
    payment_method VARCHAR(50) NOT NULL, -- 'card', 'cash', 'digital_wallet'
    amount DECIMAL(10,2) NOT NULL,
    tip_amount DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'completed', 'failed', 'refunded'
    transaction_id VARCHAR(255),
    processor VARCHAR(100), -- 'stripe', 'square', etc.
    metadata JSONB DEFAULT '{}'::jsonb,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- ANALYTICS & REPORTING
-- ============================================================================

-- Daily Sales Summary
CREATE TABLE IF NOT EXISTS public.daily_sales_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    location_id UUID REFERENCES public.locations(id),
    date DATE NOT NULL,
    total_sales DECIMAL(10,2) NOT NULL DEFAULT 0,
    total_orders INTEGER NOT NULL DEFAULT 0,
    total_customers INTEGER NOT NULL DEFAULT 0,
    avg_order_value DECIMAL(10,2),
    total_tips DECIMAL(10,2) DEFAULT 0,
    total_tax DECIMAL(10,2) DEFAULT 0,
    payment_methods JSONB DEFAULT '{}'::jsonb,
    top_items JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(business_id, location_id, date)
);

-- Item Performance Analytics
CREATE TABLE IF NOT EXISTS public.item_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL REFERENCES public.menu_items(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    quantity_sold INTEGER NOT NULL DEFAULT 0,
    revenue DECIMAL(10,2) NOT NULL DEFAULT 0,
    cost DECIMAL(10,2) DEFAULT 0,
    profit DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(business_id, menu_item_id, date)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Menu Management Indexes
CREATE INDEX IF NOT EXISTS idx_menu_categories_business ON public.menu_categories(business_id);
CREATE INDEX IF NOT EXISTS idx_menu_categories_parent ON public.menu_categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_business ON public.menu_items(business_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_category ON public.menu_items(category_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_available ON public.menu_items(is_available);
CREATE INDEX IF NOT EXISTS idx_item_modifiers_business ON public.item_modifiers(business_id);

-- Inventory Indexes
CREATE INDEX IF NOT EXISTS idx_inventory_items_business ON public.inventory_items(business_id);
CREATE INDEX IF NOT EXISTS idx_inventory_items_supplier ON public.inventory_items(supplier_id);
CREATE INDEX IF NOT EXISTS idx_inventory_items_location ON public.inventory_items(location_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_business ON public.inventory_transactions(business_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_item ON public.inventory_transactions(inventory_item_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_date ON public.inventory_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_business ON public.stock_alerts(business_id);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_active ON public.stock_alerts(is_active);
CREATE INDEX IF NOT EXISTS idx_suppliers_business ON public.suppliers(business_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_business ON public.purchase_orders(business_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON public.purchase_orders(supplier_id);

-- Operations Indexes
CREATE INDEX IF NOT EXISTS idx_locations_business ON public.locations(business_id);
CREATE INDEX IF NOT EXISTS idx_floor_plans_business ON public.floor_plans(business_id);
CREATE INDEX IF NOT EXISTS idx_floor_plans_location ON public.floor_plans(location_id);
CREATE INDEX IF NOT EXISTS idx_tables_business ON public.tables(business_id);
CREATE INDEX IF NOT EXISTS idx_tables_location ON public.tables(location_id);
CREATE INDEX IF NOT EXISTS idx_tables_status ON public.tables(status);
CREATE INDEX IF NOT EXISTS idx_kds_orders_business ON public.kds_orders(business_id);
CREATE INDEX IF NOT EXISTS idx_kds_orders_order ON public.kds_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_kds_orders_status ON public.kds_orders(status);

-- Staff Indexes
CREATE INDEX IF NOT EXISTS idx_staff_members_business ON public.staff_members(business_id);
CREATE INDEX IF NOT EXISTS idx_staff_members_user ON public.staff_members(user_id);
CREATE INDEX IF NOT EXISTS idx_staff_schedules_business ON public.staff_schedules(business_id);
CREATE INDEX IF NOT EXISTS idx_staff_schedules_staff ON public.staff_schedules(staff_id);
CREATE INDEX IF NOT EXISTS idx_staff_schedules_date ON public.staff_schedules(shift_date);
CREATE INDEX IF NOT EXISTS idx_time_clock_business ON public.time_clock(business_id);
CREATE INDEX IF NOT EXISTS idx_time_clock_staff ON public.time_clock(staff_id);

-- Payment Indexes
CREATE INDEX IF NOT EXISTS idx_order_items_order ON public.order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_menu_item ON public.order_items(menu_item_id);
CREATE INDEX IF NOT EXISTS idx_payments_business ON public.payments(business_id);
CREATE INDEX IF NOT EXISTS idx_payments_order ON public.payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON public.payments(status);

-- Analytics Indexes
CREATE INDEX IF NOT EXISTS idx_daily_sales_business_date ON public.daily_sales_summary(business_id, date);
CREATE INDEX IF NOT EXISTS idx_item_performance_business_date ON public.item_performance(business_id, date);
CREATE INDEX IF NOT EXISTS idx_item_performance_item ON public.item_performance(menu_item_id);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE TRIGGER update_menu_categories_timestamp
BEFORE UPDATE ON public.menu_categories
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_menu_items_timestamp
BEFORE UPDATE ON public.menu_items
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_item_modifiers_timestamp
BEFORE UPDATE ON public.item_modifiers
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_inventory_items_timestamp
BEFORE UPDATE ON public.inventory_items
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_stock_alerts_timestamp
BEFORE UPDATE ON public.stock_alerts
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_suppliers_timestamp
BEFORE UPDATE ON public.suppliers
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_purchase_orders_timestamp
BEFORE UPDATE ON public.purchase_orders
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_locations_timestamp
BEFORE UPDATE ON public.locations
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_floor_plans_timestamp
BEFORE UPDATE ON public.floor_plans
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_tables_timestamp
BEFORE UPDATE ON public.tables
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_kds_orders_timestamp
BEFORE UPDATE ON public.kds_orders
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_staff_members_timestamp
BEFORE UPDATE ON public.staff_members
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_staff_schedules_timestamp
BEFORE UPDATE ON public.staff_schedules
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_time_clock_timestamp
BEFORE UPDATE ON public.time_clock
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_order_items_timestamp
BEFORE UPDATE ON public.order_items
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_daily_sales_summary_timestamp
BEFORE UPDATE ON public.daily_sales_summary
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_item_performance_timestamp
BEFORE UPDATE ON public.item_performance
FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

-- ============================================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================================

-- Menu Categories
ALTER TABLE public.menu_categories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Business team can view menu categories"
    ON public.menu_categories FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid() AND business_id = menu_categories.business_id
    ));

CREATE POLICY "Business owners can manage menu categories"
    ON public.menu_categories FOR ALL
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid() AND business_id = menu_categories.business_id
        AND role IN ('business_owner'::user_role, 'admin'::user_role)
    ));

-- Menu Items
ALTER TABLE public.menu_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view available menu items"
    ON public.menu_items FOR SELECT
    USING (is_available = true);

CREATE POLICY "Business team can manage menu items"
    ON public.menu_items FOR ALL
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid() AND business_id = menu_items.business_id
    ));

-- Similar policies for other tables...
-- (Inventory, Staff, Tables, etc. - following same pattern)

-- ============================================================================
-- FUNCTIONS FOR BUSINESS LOGIC
-- ============================================================================

-- Function to automatically reduce inventory on order completion
CREATE OR REPLACE FUNCTION reduce_inventory_on_order()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        -- Logic to reduce inventory based on order items
        -- This would iterate through order items and reduce corresponding inventory
        RAISE NOTICE 'Order completed: %', NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_reduce_inventory
AFTER UPDATE ON public.orders
FOR EACH ROW
EXECUTE FUNCTION reduce_inventory_on_order();

-- Function to calculate daily sales summary
CREATE OR REPLACE FUNCTION calculate_daily_sales(
    p_business_id UUID,
    p_date DATE
)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_sales', COALESCE(SUM(total_amount), 0),
        'total_orders', COUNT(*),
        'avg_order_value', COALESCE(AVG(total_amount), 0)
    ) INTO result
    FROM public.orders
    WHERE business_id = p_business_id
    AND DATE(created_at) = p_date
    AND status = 'completed';
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to get low stock items
CREATE OR REPLACE FUNCTION get_low_stock_items(p_business_id UUID)
RETURNS TABLE (
    item_id UUID,
    item_name VARCHAR,
    current_stock DECIMAL,
    min_stock DECIMAL,
    percentage DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        id,
        name,
        current_stock,
        min_stock,
        CASE WHEN min_stock > 0 
            THEN (current_stock / min_stock * 100) 
            ELSE 0 
        END as percentage
    FROM public.inventory_items
    WHERE business_id = p_business_id
    AND current_stock <= min_stock
    AND is_tracked = true
    ORDER BY (current_stock / NULLIF(min_stock, 0)) ASC;
END;
$$ LANGUAGE plpgsql;
