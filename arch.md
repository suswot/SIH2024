//uploaded at supabase 



-- Enable PostGIS extension for geospatial capabilities
CREATE EXTENSION IF NOT EXISTS postgis;

-- Tourist User Table
CREATE TABLE Tourists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fullName VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    phoneNumber VARCHAR(20),
    country VARCHAR(100),
    profilePictureUrl TEXT,
    kycStatus VARCHAR(50) DEFAULT 'Pending', -- Pending, Verified, Rejected
    createdAt TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updatedAt TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Emergency Contacts Table
CREATE TABLE EmergencyContacts (
    id SERIAL PRIMARY KEY,
    touristId UUID REFERENCES Tourists(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    relationship VARCHAR(100),
    phoneNumber VARCHAR(20) NOT NULL,
    createdAt TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Police/Admin User Table
CREATE TABLE Admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role VARCHAR(50) NOT NULL, -- e.g., 'Police', 'TourismOfficial'
    precinctId VARCHAR(100),
    createdAt TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tourist Location History Table
CREATE TABLE LocationHistory (
    id BIGSERIAL PRIMARY KEY,
    touristId UUID REFERENCES Tourists(id) ON DELETE CASCADE,
    -- Storing location using the PostGIS 'geography' type for accuracy
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Geofenced Zones Table
CREATE TABLE Zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    -- Storing the area as a polygon
    area GEOGRAPHY(POLYGON, 4326) NOT NULL,
    riskLevel VARCHAR(50) NOT NULL, -- 'Safe', 'Warning', 'Restricted'
    description TEXT,
    createdAt TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Alerts Table
CREATE TABLE Alerts (
    id BIGSERIAL PRIMARY KEY,
    touristId UUID REFERENCES Tourists(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'Panic', 'Geo-fence', 'Anomaly'
    status VARCHAR(50) DEFAULT 'Active', -- Active, Acknowledged, Resolved
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    details TEXT,
    eFirNumber VARCHAR(100),
    createdAt TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolvedAt TIMESTAMPTZ
);

-- Gamification: Safety Profile Table
CREATE TABLE SafetyProfiles (
    touristId UUID PRIMARY KEY REFERENCES Tourists(id) ON DELETE CASCADE,
    safetyScore INT DEFAULT 75, -- Starting score
    checkInStreak INT DEFAULT 0,
    lastCheckInDate DATE,
    updatedAt TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Gamification: Badges Table
CREATE TABLE Badges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    iconUrl TEXT
);

-- Junction table for tourists and their earned badges
CREATE TABLE EarnedBadges (
    touristId UUID REFERENCES Tourists(id) ON DELETE CASCADE,
    badgeId INT REFERENCES Badges(id) ON DELETE CASCADE,
    earnedAt TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (touristId, badgeId)
);