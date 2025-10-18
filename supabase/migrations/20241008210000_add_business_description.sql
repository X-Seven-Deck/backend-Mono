BEGIN;

-- 1) Ensure description column exists on public.businesses
ALTER TABLE public.businesses
  ADD COLUMN IF NOT EXISTS description TEXT;

-- 2) Ensure a default 'General' business category exists and capture its id
DO $$
DECLARE
  general_id INTEGER;
BEGIN
  SELECT id INTO general_id FROM public.business_categories WHERE name = 'General' LIMIT 1;
  IF general_id IS NULL THEN
    INSERT INTO public.business_categories (name, description)
    VALUES ('General', 'Default business category')
    RETURNING id INTO general_id;
  END IF;
END $$;

-- 3) Replace RPC with enterprise-grade implementation
CREATE OR REPLACE FUNCTION public.create_business_with_owner(
  business_data JSONB,
  owner_id UUID
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $$
DECLARE
  v_business_row_id UUID;
  v_category_id INTEGER;
  v_result JSONB;
  v_name TEXT;
  v_description TEXT;
  v_email TEXT;
  v_phone TEXT;
  v_base_slug TEXT;
  v_slug TEXT;
  v_try INT := 0;
  v_suffix TEXT;
  v_public_business_id TEXT; -- short external id
BEGIN
  -- Extract inputs with safe defaults
  v_name := COALESCE(business_data->>'name', 'New Business');
  v_description := NULLIF(business_data->>'description', '');
  v_email := NULLIF(business_data->>'email', '');
  v_phone := NULLIF(business_data->>'phone', '');

  -- Resolve category id (ensure 'General' exists)
  SELECT id INTO v_category_id FROM public.business_categories WHERE name = 'General' LIMIT 1;
  IF v_category_id IS NULL THEN
    INSERT INTO public.business_categories (name, description)
    VALUES ('General', 'Default business category')
    RETURNING id INTO v_category_id;
  END IF;

  -- Build base slug from name
  v_base_slug := lower(regexp_replace(v_name, '[^a-zA-Z0-9]+', '-', 'g'));
  v_base_slug := regexp_replace(v_base_slug, '^-+|-+$', '', 'g');
  IF v_base_slug = '' THEN
    v_base_slug := 'business';
  END IF;

  -- Ensure unique slug by appending -1, -2, ... when needed
  LOOP
    v_suffix := CASE WHEN v_try = 0 THEN '' ELSE '-' || v_try::text END;
    v_slug := v_base_slug || v_suffix;
    EXIT WHEN NOT EXISTS (SELECT 1 FROM public.businesses WHERE slug = v_slug);
    v_try := v_try + 1;
  END LOOP;

  -- Generate a unique short public business_id (not the UUID PK)
  LOOP
    v_public_business_id := substring(replace(gen_random_uuid()::text, '-', ''), 1, 12);
    EXIT WHEN NOT EXISTS (SELECT 1 FROM public.businesses WHERE business_id = v_public_business_id);
  END LOOP;

  -- Insert business row (status/created_at/updated_at have defaults)
  INSERT INTO public.businesses (
    business_id,
    name,
    slug,
    description,
    category_id
  ) VALUES (
    v_public_business_id,
    v_name,
    v_slug,
    v_description,
    v_category_id
  ) RETURNING id INTO v_business_row_id;

  -- Create business profile
  INSERT INTO public.business_profiles (
    business_id,
    owner_id,
    name,
    description,
    email,
    phone
  ) VALUES (
    v_business_row_id,
    owner_id,
    v_name,
    v_description,
    v_email,
    v_phone
  );

  -- Add owner to business staff
  INSERT INTO public.business_staff (
    business_id,
    user_id,
    role
  ) VALUES (
    v_business_row_id,
    owner_id,
    'business_owner'::user_role
  );

  -- Ensure user_business_roles entry
  INSERT INTO public.user_business_roles (
    user_id,
    business_id,
    role
  ) VALUES (
    owner_id,
    v_business_row_id,
    'business_owner'::user_role
  ) ON CONFLICT (user_id, business_id) DO NOTHING;

  -- Return consolidated business data
  SELECT jsonb_build_object(
    'id', b.id,
    'business_id', b.business_id,
    'name', b.name,
    'slug', b.slug,
    'description', COALESCE(b.description, bp.description),
    'owner_id', bp.owner_id,
    'category_id', b.category_id,
    'status', b.status,
    'created_at', b.created_at,
    'updated_at', b.updated_at
  ) INTO v_result
  FROM public.businesses b
  JOIN public.business_profiles bp ON b.id = bp.business_id
  WHERE b.id = v_business_row_id;

  RETURN v_result;
END;
$$;

COMMIT;
