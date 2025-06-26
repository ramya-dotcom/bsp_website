-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_admin BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create digilocker_verification table
CREATE TABLE IF NOT EXISTS digilocker_verification (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  aadhaar_number VARCHAR(20),
  voter_id VARCHAR(20),
  name VARCHAR(255),
  dob DATE,
  gender VARCHAR(10),
  address TEXT,
  photo TEXT, -- Using TEXT instead of BLOB for base64 encoded images
  document_type VARCHAR(20),
  raw_json JSON,
  verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
  id SERIAL PRIMARY KEY,
  admin_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_digilocker_user_id ON digilocker_verification(user_id);
CREATE INDEX IF NOT EXISTS idx_digilocker_aadhaar ON digilocker_verification(aadhaar_number);
CREATE INDEX IF NOT EXISTS idx_digilocker_voter_id ON digilocker_verification(voter_id);
CREATE INDEX IF NOT EXISTS idx_events_admin_id ON events(admin_id);
