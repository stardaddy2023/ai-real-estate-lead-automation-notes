-- MACRO INTELLIGENCE: Market Grades
CREATE TABLE market_metrics (
    zip_code VARCHAR(10) PRIMARY KEY,
    grade_cashflow VARCHAR(2), -- "A+", "B-"
    grade_flip VARCHAR(2),
    price_to_rent_ratio DECIMAL(5,2),
    months_inventory DECIMAL(4,1),
    net_migration_trend VARCHAR -- "Positive", "Negative"
);

-- CORE PROPERTY TABLE
CREATE TABLE properties (
    id UUID PRIMARY KEY,
    zip_code VARCHAR(10) REFERENCES market_metrics(zip_code),
    address_street VARCHAR NOT NULL,
    
    -- Analysis Data
    arv_estimate DECIMAL(12,2),
    rehab_cost_estimate DECIMAL(12,2),
    
    -- Distress Flags
    distress_score INTEGER,
    is_tax_delinquent BOOLEAN,
    is_absentee_owner BOOLEAN
);

-- TRANSACTION: Offers & Contracts
CREATE TABLE offers (
    id UUID PRIMARY KEY,
    property_id UUID REFERENCES properties(id),
    offer_amount DECIMAL(12,2),
    lex_approval_status BOOLEAN DEFAULT FALSE, -- Legal Check
    contract_pdf_url VARCHAR
);

-- DISPOSITIONS: The Buyers List
CREATE TABLE cash_buyers (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    
    -- Buy Box Criteria
    target_zip_codes VARCHAR[], 
    buy_box_embedding VECTOR(768) -- For AI Matching
);