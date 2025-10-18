-- ============================================================================
-- X-sevenAI Enhanced Chat System Schema
-- Enterprise-grade multi-chat system with AI integration
-- ============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================================================
-- CHAT SESSIONS (Enhanced)
-- ============================================================================

-- Drop existing if needed and recreate with enhanced structure
DROP TABLE IF EXISTS public.chat_messages CASCADE;
DROP TABLE IF EXISTS public.chat_sessions CASCADE;

CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Session Type: dedicated (business-specific), dashboard (business AI assistant), global (cross-business)
    session_type VARCHAR(50) NOT NULL CHECK (session_type IN ('dedicated', 'dashboard', 'global')),
    
    -- References
    business_id UUID REFERENCES public.businesses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    
    -- Session Details
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'closed', 'archived', 'transferred')),
    channel VARCHAR(50) DEFAULT 'web' CHECK (channel IN ('web', 'mobile', 'voice', 'whatsapp', 'sms')),
    
    -- AI Context
    context JSONB DEFAULT '{}'::jsonb, -- Conversation context, user preferences, history
    ai_model VARCHAR(100) DEFAULT 'gpt-4o-mini',
    intent VARCHAR(100), -- search, order, reservation, support, analytics
    sentiment VARCHAR(50), -- positive, neutral, negative
    
    -- Agent Assignment (for human handover)
    assigned_agent_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    handover_reason TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    tags TEXT[],
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    last_message_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    
    -- Analytics
    message_count INTEGER DEFAULT 0,
    avg_response_time DECIMAL(10,2), -- in seconds
    satisfaction_score DECIMAL(3,2) -- 0-5 rating
);

CREATE INDEX idx_chat_sessions_business ON public.chat_sessions(business_id);
CREATE INDEX idx_chat_sessions_user ON public.chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_type ON public.chat_sessions(session_type);
CREATE INDEX idx_chat_sessions_status ON public.chat_sessions(status);
CREATE INDEX idx_chat_sessions_intent ON public.chat_sessions(intent);
CREATE INDEX idx_chat_sessions_last_message ON public.chat_sessions(last_message_at DESC);

-- ============================================================================
-- CHAT MESSAGES (Enhanced)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    
    -- Message Details
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'agent', 'bot')),
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text' CHECK (message_type IN ('text', 'voice', 'image', 'file', 'action', 'suggestion')),
    
    -- Sender Information
    sender_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    sender_name VARCHAR(255),
    
    -- AI Processing
    ai_generated BOOLEAN DEFAULT false,
    ai_model VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    processing_time DECIMAL(10,3), -- in seconds
    
    -- Voice/Media
    audio_url TEXT,
    audio_duration DECIMAL(10,2), -- in seconds
    media_urls TEXT[],
    
    -- Actions & Intents
    intent VARCHAR(100), -- Detected intent
    entities JSONB DEFAULT '{}'::jsonb, -- Extracted entities (dates, locations, items)
    actions JSONB DEFAULT '[]'::jsonb, -- Actions taken (create_order, book_reservation)
    
    -- Feedback
    feedback_rating INTEGER CHECK (feedback_rating BETWEEN 1 AND 5),
    feedback_comment TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    edited_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT false
);

CREATE INDEX idx_chat_messages_session ON public.chat_messages(session_id);
CREATE INDEX idx_chat_messages_created ON public.chat_messages(created_at DESC);
CREATE INDEX idx_chat_messages_role ON public.chat_messages(role);
CREATE INDEX idx_chat_messages_sender ON public.chat_messages(sender_id);
CREATE INDEX idx_chat_messages_intent ON public.chat_messages(intent);

-- ============================================================================
-- CHAT PARTICIPANTS (For group chats and multi-user sessions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.chat_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Participant Details
    role VARCHAR(50) DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'observer')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'left', 'removed')),
    
    -- Permissions
    can_send_messages BOOLEAN DEFAULT true,
    can_view_history BOOLEAN DEFAULT true,
    
    -- Activity
    joined_at TIMESTAMPTZ DEFAULT now(),
    left_at TIMESTAMPTZ,
    last_read_at TIMESTAMPTZ,
    unread_count INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    UNIQUE(session_id, user_id)
);

CREATE INDEX idx_chat_participants_session ON public.chat_participants(session_id);
CREATE INDEX idx_chat_participants_user ON public.chat_participants(user_id);

-- ============================================================================
-- CHAT TEMPLATES (For quick responses and AI prompts)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.chat_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES public.businesses(id) ON DELETE CASCADE,
    
    -- Template Details
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100), -- greeting, faq, order_confirmation, reservation_confirmation
    template_type VARCHAR(50) CHECK (template_type IN ('quick_reply', 'ai_prompt', 'system_message')),
    
    -- Content
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]'::jsonb, -- [{name, type, required}]
    
    -- Usage
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_chat_templates_business ON public.chat_templates(business_id);
CREATE INDEX idx_chat_templates_category ON public.chat_templates(category);

-- ============================================================================
-- CHAT ANALYTICS (For tracking performance and insights)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.chat_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES public.businesses(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Session Metrics
    total_sessions INTEGER DEFAULT 0,
    active_sessions INTEGER DEFAULT 0,
    closed_sessions INTEGER DEFAULT 0,
    avg_session_duration DECIMAL(10,2), -- in minutes
    
    -- Message Metrics
    total_messages INTEGER DEFAULT 0,
    user_messages INTEGER DEFAULT 0,
    ai_messages INTEGER DEFAULT 0,
    avg_messages_per_session DECIMAL(10,2),
    
    -- Response Metrics
    avg_first_response_time DECIMAL(10,2), -- in seconds
    avg_response_time DECIMAL(10,2), -- in seconds
    
    -- Satisfaction Metrics
    avg_satisfaction_score DECIMAL(3,2),
    total_feedback_count INTEGER DEFAULT 0,
    
    -- Intent Distribution
    intent_distribution JSONB DEFAULT '{}'::jsonb,
    
    -- Channel Distribution
    channel_distribution JSONB DEFAULT '{}'::jsonb,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(business_id, date)
);

CREATE INDEX idx_chat_analytics_business_date ON public.chat_analytics(business_id, date DESC);

-- ============================================================================
-- CHAT KNOWLEDGE BASE (For RAG and AI responses)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.chat_knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES public.businesses(id) ON DELETE CASCADE,
    
    -- Content
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) CHECK (content_type IN ('faq', 'policy', 'menu_item', 'service', 'general')),
    
    -- Vector Embedding for RAG
    embedding vector(1536), -- OpenAI text-embedding-3-small
    
    -- Metadata
    tags TEXT[],
    category VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    
    -- Usage
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_chat_kb_business ON public.chat_knowledge_base(business_id);
CREATE INDEX idx_chat_kb_type ON public.chat_knowledge_base(content_type);
CREATE INDEX idx_chat_kb_embedding ON public.chat_knowledge_base USING ivfflat (embedding vector_cosine_ops);

-- ============================================================================
-- CHAT WEBHOOKS (For external integrations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.chat_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES public.businesses(id) ON DELETE CASCADE,
    
    -- Webhook Details
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    secret VARCHAR(255),
    
    -- Events
    events TEXT[] NOT NULL, -- ['message.sent', 'session.created', 'session.closed']
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMPTZ,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_chat_webhooks_business ON public.chat_webhooks(business_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_chat_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_chat_sessions_timestamp
BEFORE UPDATE ON public.chat_sessions
FOR EACH ROW EXECUTE FUNCTION update_chat_timestamp();

CREATE TRIGGER update_chat_templates_timestamp
BEFORE UPDATE ON public.chat_templates
FOR EACH ROW EXECUTE FUNCTION update_chat_timestamp();

CREATE TRIGGER update_chat_analytics_timestamp
BEFORE UPDATE ON public.chat_analytics
FOR EACH ROW EXECUTE FUNCTION update_chat_timestamp();

CREATE TRIGGER update_chat_kb_timestamp
BEFORE UPDATE ON public.chat_knowledge_base
FOR EACH ROW EXECUTE FUNCTION update_chat_timestamp();

-- Update message count in session
CREATE OR REPLACE FUNCTION update_session_message_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE public.chat_sessions
        SET message_count = message_count + 1,
            last_message_at = NEW.created_at
        WHERE id = NEW.session_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_message_count_trigger
AFTER INSERT ON public.chat_messages
FOR EACH ROW EXECUTE FUNCTION update_session_message_count();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_participants ENABLE ROW LEVEL SECURITY;

-- Users can view their own sessions
CREATE POLICY "Users can view own chat sessions"
    ON public.chat_sessions FOR SELECT
    USING (user_id = auth.uid() OR assigned_agent_id = auth.uid());

-- Business owners can view their business sessions
CREATE POLICY "Business owners can view business chat sessions"
    ON public.chat_sessions FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.user_business_roles
        WHERE user_id = auth.uid() AND business_id = chat_sessions.business_id
    ));

-- Users can view messages in their sessions
CREATE POLICY "Users can view messages in their sessions"
    ON public.chat_messages FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.chat_sessions
        WHERE id = chat_messages.session_id
        AND (user_id = auth.uid() OR assigned_agent_id = auth.uid())
    ));

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to get chat session summary
CREATE OR REPLACE FUNCTION get_chat_session_summary(p_session_id UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'session_id', s.session_id,
        'session_type', s.session_type,
        'status', s.status,
        'message_count', s.message_count,
        'created_at', s.created_at,
        'last_message_at', s.last_message_at,
        'intent', s.intent,
        'sentiment', s.sentiment,
        'recent_messages', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'role', role,
                    'content', content,
                    'created_at', created_at
                )
                ORDER BY created_at DESC
            )
            FROM (
                SELECT role, content, created_at
                FROM public.chat_messages
                WHERE session_id = p_session_id
                AND is_deleted = false
                ORDER BY created_at DESC
                LIMIT 10
            ) recent
        )
    ) INTO result
    FROM public.chat_sessions s
    WHERE s.id = p_session_id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to search knowledge base
CREATE OR REPLACE FUNCTION search_knowledge_base(
    p_business_id UUID,
    p_query_embedding vector(1536),
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    title VARCHAR,
    content TEXT,
    similarity DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kb.id,
        kb.title,
        kb.content,
        (1 - (kb.embedding <=> p_query_embedding))::DECIMAL as similarity
    FROM public.chat_knowledge_base kb
    WHERE kb.business_id = p_business_id
    AND kb.is_active = true
    ORDER BY kb.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE public.chat_sessions IS 'Chat sessions for dedicated, dashboard, and global chat types';
COMMENT ON TABLE public.chat_messages IS 'Individual messages within chat sessions with AI metadata';
COMMENT ON TABLE public.chat_participants IS 'Participants in group chat sessions';
COMMENT ON TABLE public.chat_templates IS 'Reusable templates for quick replies and AI prompts';
COMMENT ON TABLE public.chat_analytics IS 'Daily analytics for chat performance tracking';
COMMENT ON TABLE public.chat_knowledge_base IS 'Knowledge base for RAG-powered AI responses';
COMMENT ON TABLE public.chat_webhooks IS 'Webhook configurations for external integrations';
