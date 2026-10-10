# Liberty Park Scenario Engine - SaaS MVP Architecture Proposal

## Executive Summary

This document proposes a clean MVP architecture for transforming the Liberty Park Scenario Engine from a single-tenant educational tool into a multi-tenant commercial SaaS platform. The proposal preserves the existing scenario engine's strengths while adding essential SaaS capabilities.

---

## Current State Analysis

### Existing Strengths
- **Robust Scenario Engine**: JSON-driven branching narratives with variable tracking
- **Rich Content**: 6 complete scenarios with images covering civics, history, and law
- **Flexible Logic**: Conditional branching, multiple outcomes, reflection collection
- **Working Prototype**: Already deployed on Render with Google Sheets integration

### Current Limitations for SaaS
| Limitation | Impact |
|------------|--------|
| No multi-tenancy | Cannot serve multiple schools/organizations |
| No authentication | No user accounts or access control |
| Hardcoded roster files | Each deployment needs manual CSV updates |
| Single Google Sheet | All data in one spreadsheet |
| No admin interface | Teachers cannot manage their own content |
| No billing/subscription | No revenue model |
| No analytics | Limited insights for educators |

---

## Proposed MVP Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Student UI  │  │  Teacher UI  │  │   Admin UI   │              │
│  │  (Streamlit) │  │  (Streamlit) │  │  (Streamlit) │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           API LAYER                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Auth API    │  │ Scenario API │  │  Data API    │              │
│  │  (FastAPI)   │  │  (FastAPI)   │  │  (FastAPI)   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          SERVICE LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Scenario     │  │  Tenant      │  │  Analytics   │              │
│  │ Engine       │  │  Service     │  │  Service     │              │
│  │ (existing)   │  │  (new)       │  │  (new)       │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  PostgreSQL  │  │    Redis     │  │ Object Store │              │
│  │  (primary)   │  │   (cache)    │  │  (S3/R2)     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack Recommendations

| Layer | Current | MVP Recommendation | Rationale |
|-------|---------|-------------------|-----------|
| Frontend | Streamlit | Streamlit + React components | Preserve existing investment, add interactivity |
| Backend | None (monolithic) | FastAPI | Modern, async, excellent for APIs |
| Database | Google Sheets | PostgreSQL | Relational data, multi-tenancy support |
| Cache | None | Redis | Session management, performance |
| Auth | None | Auth0 or Clerk | Rapid implementation, enterprise-ready |
| File Storage | Local filesystem | Cloudflare R2 or AWS S3 | Scalable image storage |
| Payments | None | Stripe | Industry standard, easy integration |
| Hosting | Render | Render or Railway | Simple scaling, managed services |

---

## Data Model Design

### Core Entities

```sql
-- Tenant (Organization/School)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan_type VARCHAR(50) DEFAULT 'free',
    stripe_customer_id VARCHAR(255),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users (Teachers, Students, Admins)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL, -- 'admin', 'teacher', 'student'
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    auth_provider VARCHAR(50), -- 'local', 'auth0', 'google'
    auth_provider_id VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Classes/Courses
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    teacher_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    class_code VARCHAR(20) UNIQUE, -- For student enrollment
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Class Enrollment
CREATE TABLE enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID REFERENCES classes(id),
    student_id UUID REFERENCES users(id),
    enrolled_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(class_id, student_id)
);

-- Scenarios (Content Library)
CREATE TABLE scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id), -- NULL for platform scenarios
    created_by UUID REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB NOT NULL, -- The existing config.json structure
    is_public BOOLEAN DEFAULT false,
    is_premium BOOLEAN DEFAULT false,
    version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Scenario Images
CREATE TABLE scenario_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES scenarios(id),
    scene_id VARCHAR(50) NOT NULL,
    file_key VARCHAR(500) NOT NULL, -- S3/R2 key
    alt_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Student Sessions (Game State)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id),
    scenario_id UUID REFERENCES scenarios(id),
    class_id UUID REFERENCES classes(id),
    current_scene VARCHAR(50) NOT NULL,
    scene_history JSONB DEFAULT '[]',
    choices_made JSONB DEFAULT '[]',
    variables JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    outcome VARCHAR(50)
);

-- Reflections
CREATE TABLE reflections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    student_id UUID REFERENCES users(id),
    scenario_id UUID REFERENCES scenarios(id),
    responses JSONB NOT NULL, -- {question_1: "answer", ...}
    submitted_at TIMESTAMP DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    stripe_subscription_id VARCHAR(255),
    plan_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## User Roles & Permissions

### Role Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  PLATFORM ADMIN                                              │
│  - Manage all tenants                                        │
│  - Manage platform-wide scenarios                            │
│  - View platform analytics                                   │
│  - Configure system settings                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  ORGANIZATION ADMIN (School Administrator)                   │
│  - Manage organization users                                 │
│  - Manage subscription                                       │
│  - View organization analytics                               │
│  - Create/manage organization scenarios                      │
│  - Manage classes                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TEACHER                                                     │
│  - Create/manage classes                                     │
│  - Assign scenarios to classes                               │
│  - View student progress                                     │
│  - Grade/export student work                                 │
│  - Create custom scenarios (premium)                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STUDENT                                                     │
│  - Join classes via code                                     │
│  - Play assigned scenarios                                   │
│  - Submit reflections                                        │
│  - View own progress                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Pricing Model

### Tiered Subscription Plans

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0 | 1 teacher, 1 class, 30 students, 3 scenarios |
| **Starter** | $29/month | 5 teachers, 10 classes, 150 students, all scenarios |
| **School** | $99/month | Unlimited teachers, unlimited classes, 500 students, custom scenarios |
| **District** | Custom | Multiple schools, SSO, LMS integration, dedicated support |

### Feature Matrix

| Feature | Free | Starter | School | District |
|---------|------|---------|--------|----------|
| Teachers | 1 | 5 | Unlimited | Unlimited |
| Classes | 1 | 10 | Unlimited | Unlimited |
| Students | 30 | 150 | 500 | Unlimited |
| Core Scenarios | 3 | All | All | All |
| Custom Scenarios | ❌ | ❌ | ✅ | ✅ |
| Analytics | Basic | Basic | Advanced | Advanced |
| Grade Export | CSV | CSV | CSV + LMS | CSV + LMS |
| SSO | ❌ | ❌ | ❌ | ✅ |
| Support | Email | Email | Priority | Dedicated |

---

## Key Features for MVP

### Phase 1: Core SaaS (Weeks 1-6)

1. **Multi-Tenancy**
   - Organization signup and onboarding
   - Tenant isolation at database level
   - Custom subdomains (optional)

2. **Authentication**
   - Email/password signup
   - Google OAuth for teachers
   - Simple class codes for students

3. **Class Management**
   - Create/edit/delete classes
   - Generate unique class codes
   - Student enrollment via code

4. **Scenario Assignment**
   - Assign scenarios to classes
   - Set due dates
   - Track completion status

5. **Basic Analytics**
   - Completion rates by class
   - Outcome distribution
   - Student progress dashboard

### Phase 2: Monetization (Weeks 7-10)

1. **Stripe Integration**
   - Subscription checkout
   - Plan upgrades/downgrades
   - Invoice generation

2. **Plan Enforcement**
   - Feature gating by plan
   - Student limit enforcement
   - Premium scenario access

3. **Trial System**
   - 14-day free trial
   - Credit card required
   - Automatic downgrade

### Phase 3: Enhanced Features (Weeks 11-14)

1. **Teacher Dashboard**
   - Class overview
   - Student progress cards
   - Quick actions

2. **Advanced Analytics**
   - Choice distribution analysis
   - Reflection insights
   - Export reports

3. **LMS Integration**
   - LTI 1.3 support
   - Grade passback
   - Canvas/Google Classroom

---

## Migration Strategy

### Data Migration

1. **Scenario Content**
   - Move JSON configs to database
   - Upload images to object storage
   - Preserve existing structure

2. **Student Data**
   - Export from Google Sheets
   - Import to PostgreSQL
   - Maintain audit trail

### Backward Compatibility

- Keep existing Streamlit app as "classic mode"
- Provide migration tool for existing users
- Support both data sources during transition

---

## Security Considerations

### Authentication & Authorization
- JWT tokens with short expiration
- Role-based access control (RBAC)
- Tenant isolation in all queries

### Data Protection
- Encryption at rest (PostgreSQL)
- Encryption in transit (HTTPS)
- PII handling compliance (FERPA/COPPA)

### API Security
- Rate limiting
- Input validation
- SQL injection prevention via ORM

---

## Scalability Considerations

### Horizontal Scaling
- Stateless API design
- Redis for session storage
- CDN for static assets

### Database Scaling
- Read replicas for analytics
- Connection pooling (PgBouncer)
- Partitioning by tenant (future)

### Performance Optimization
- Scenario caching
- Image optimization
- Lazy loading

---

## Success Metrics

### Technical Metrics
- Page load time < 2 seconds
- API response time < 200ms
- 99.9% uptime SLA

### Business Metrics
- Monthly Recurring Revenue (MRR)
- Customer Acquisition Cost (CAC)
- Churn rate < 5%
- Net Promoter Score (NPS)

### Engagement Metrics
- Daily Active Users (DAU)
- Scenarios completed per student
- Average session duration

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep | High | High | Strict MVP definition |
| Performance issues | Medium | High | Load testing, caching |
| Data migration errors | Medium | High | Staged rollout, backups |
| Low conversion rate | Medium | High | User research, pricing A/B |
| Security breach | Low | Critical | Security audit, penetration testing |

---

## Conclusion

This architecture transforms the Liberty Park Scenario Engine into a viable commercial SaaS while preserving its educational value. The phased approach allows for iterative development and early market validation.

**Recommended Next Steps:**
1. Validate pricing model with potential customers
2. Begin Phase 1 development
3. Set up CI/CD pipeline
4. Create user testing program
