-- Insert sample users (password is 'password123' hashed)
INSERT INTO users (email, password_hash, is_admin) VALUES 
('admin@example.com', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', TRUE),
('user@example.com', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', FALSE),
('john.doe@example.com', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', FALSE)
ON CONFLICT (email) DO NOTHING;

-- Insert sample verification data
INSERT INTO digilocker_verification (user_id, aadhaar_number, name, dob, gender, address, document_type, raw_json) VALUES 
(2, '1234-5678-9012', 'John Doe', '1990-05-15', 'Male', '123 Main St, City, State 12345', 'aadhaar', '{"status": "verified", "document": "aadhaar"}'),
(3, '9876-5432-1098', 'Jane Smith', '1985-08-22', 'Female', '456 Oak Ave, Town, State 67890', 'aadhaar', '{"status": "verified", "document": "aadhaar"}')
ON CONFLICT DO NOTHING;

-- Insert sample events
INSERT INTO events (admin_id, title, description, start_time, end_time) VALUES 
(1, 'Annual General Meeting', 'Annual meeting for all members to discuss platform updates and future plans.', '2024-02-15 10:00:00', '2024-02-15 12:00:00'),
(1, 'Tech Workshop', 'Workshop on latest technology trends and digital literacy.', '2024-02-20 14:00:00', '2024-02-20 17:00:00'),
(1, 'Community Outreach', 'Community service event for verified members.', '2024-02-25 09:00:00', '2024-02-25 16:00:00')
ON CONFLICT DO NOTHING;
