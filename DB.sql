-- ==========================================
-- DATABASE SCHEMA (PostgreSQL)
-- Thêm đầy đủ bảng evaluation_result_details
-- ==========================================

-- 1. Bảng Users (Đã bổ sung thông tin giao hàng)
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone_number VARCHAR(20),        -- Bổ sung để liên hệ giao hàng
    address TEXT,                    -- Bổ sung địa chỉ mặc định
    role VARCHAR(20) NOT NULL DEFAULT 'user', -- 'admin', 'user'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng Brands (Giữ nguyên)
CREATE TABLE brands (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    logo_url TEXT,                   -- Bổ sung logo hãng
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Bảng Laptops (Giữ nguyên + Bổ sung tồn kho)
CREATE TABLE laptops (
    id BIGSERIAL PRIMARY KEY,
    brand_id BIGINT REFERENCES brands(id) ON DELETE SET NULL,

    name VARCHAR(255) NOT NULL,
    model_code VARCHAR(100),

    -- Cấu hình chi tiết
    cpu VARCHAR(150) NOT NULL,
    ram_gb INTEGER NOT NULL,
    gpu VARCHAR(150),
    ssd_gb INTEGER NOT NULL,
    screen_size NUMERIC(4,1),
    screen_resolution VARCHAR(50),
    weight_kg NUMERIC(4,2),
    battery_hours NUMERIC(4,1),
    durability_score NUMERIC(4,2),
    upgradeability_score NUMERIC(4,2),

    price NUMERIC(15,2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0, -- Bổ sung: Quản lý tồn kho
    release_year INTEGER,
    ports_count INTEGER DEFAULT 0,
    condition_status VARCHAR(20) NOT NULL DEFAULT 'new',

    description TEXT,
    image_url TEXT,

    -- Các cột chuẩn hóa cho AHP (Khớp với train_model.py)
    norm_cpu NUMERIC(10,6),
    norm_ram NUMERIC(10,6),
    norm_gpu NUMERIC(10,6),
    norm_screen NUMERIC(10,6),
    norm_weight NUMERIC(10,6),
    norm_battery NUMERIC(10,6),
    norm_durability NUMERIC(10,6),
    norm_upgradeability NUMERIC(10,6),

    ahp_score NUMERIC(10,6), -- Điểm số từ Model AI (nếu tính trước)

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Bảng Laptop Import Logs (Giữ nguyên)
CREATE TABLE laptop_import_logs (
    id BIGSERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    imported_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    total_rows INTEGER DEFAULT 0,
    success_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- PHẦN AHP & GỢI Ý (Giữ nguyên logic của bạn)
-- ==========================================

-- 5. Bảng Tiêu chí AHP
CREATE TABLE ahp_criteria (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Insert dữ liệu mẫu cho tiêu chí
INSERT INTO ahp_criteria (code, name, description) VALUES
('cpu', 'CPU', 'Hiệu năng bộ xử lý'),
('ram', 'RAM', 'Dung lượng bộ nhớ RAM'),
('gpu', 'GPU', 'Hiệu năng đồ họa'),
('screen', 'Màn hình', 'Chất lượng/kích thước màn hình'),
('weight', 'Trọng lượng', 'Mức độ gọn nhẹ'),
('battery', 'Pin', 'Thời lượng pin'),
('durability', 'Độ bền', 'Độ bền thiết bị'),
('upgradeability', 'Khả năng nâng cấp', 'Khả năng nâng cấp SSD/RAM');

-- 6. Phiên đánh giá/tư vấn
CREATE TABLE evaluation_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,

    student_major VARCHAR(100),
    usage_needs VARCHAR(255),
    budget_min NUMERIC(15,2),
    budget_max NUMERIC(15,2),

    -- Các cờ ưu tiên nhanh
    prefer_battery BOOLEAN DEFAULT FALSE,
    prefer_lightweight BOOLEAN DEFAULT FALSE,
    prefer_performance BOOLEAN DEFAULT FALSE,
    prefer_durability BOOLEAN DEFAULT FALSE,
    prefer_upgradeability BOOLEAN DEFAULT FALSE,

    ai_enabled BOOLEAN DEFAULT FALSE,
    cr_value NUMERIC(10,6),
    ci_value NUMERIC(10,6),
    is_consistent BOOLEAN DEFAULT FALSE,

    recommended_laptop_id BIGINT REFERENCES laptops(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Trọng số đánh giá (Weights)
CREATE TABLE evaluation_weights (
    id BIGSERIAL PRIMARY KEY,
    evaluation_session_id BIGINT NOT NULL REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    criterion_id BIGINT NOT NULL REFERENCES ahp_criteria(id) ON DELETE CASCADE,

    ai_suggested_weight NUMERIC(10,6),
    user_final_weight NUMERIC(10,6) NOT NULL,

    UNIQUE (evaluation_session_id, criterion_id)
);

-- 8. Ma trận so sánh cặp (Pairwise Matrix)
CREATE TABLE evaluation_pairwise_matrix (
    id BIGSERIAL PRIMARY KEY,
    evaluation_session_id BIGINT NOT NULL REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    criterion_1_id BIGINT NOT NULL REFERENCES ahp_criteria(id) ON DELETE CASCADE,
    criterion_2_id BIGINT NOT NULL REFERENCES ahp_criteria(id) ON DELETE CASCADE,
    comparison_value NUMERIC(10,6) NOT NULL,

    UNIQUE (evaluation_session_id, criterion_1_id, criterion_2_id)
);

-- 9. Bộ lọc tìm kiếm
CREATE TABLE evaluation_filters (
    id BIGSERIAL PRIMARY KEY,
    evaluation_session_id BIGINT NOT NULL REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    brand_id BIGINT REFERENCES brands(id) ON DELETE SET NULL,
    min_price NUMERIC(15,2),
    max_price NUMERIC(15,2),
    min_ssd_gb INTEGER,
    max_ssd_gb INTEGER,
    min_release_year INTEGER,
    max_release_year INTEGER,
    min_screen_size NUMERIC(4,1),
    max_screen_size NUMERIC(4,1),
    min_ports_count INTEGER,
    condition_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Kết quả gợi ý
CREATE TABLE evaluation_results (
    id BIGSERIAL PRIMARY KEY,
    evaluation_session_id BIGINT NOT NULL REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    laptop_id BIGINT NOT NULL REFERENCES laptops(id) ON DELETE CASCADE,
    total_score NUMERIC(10,6) NOT NULL,
    rank_position INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (evaluation_session_id, laptop_id)
);

-- 10.1. Bảng CHI TIẾT kết quả đánh giá (BỔ SUNG)
CREATE TABLE evaluation_result_details (
    id BIGSERIAL PRIMARY KEY,
    evaluation_result_id BIGINT NOT NULL REFERENCES evaluation_results(id) ON DELETE CASCADE,
    criterion_id BIGINT NOT NULL REFERENCES ahp_criteria(id) ON DELETE CASCADE,

    criterion_weight NUMERIC(10,6) NOT NULL,         -- Trọng số tiêu chí tại thời điểm đánh giá
    laptop_value_raw NUMERIC(10,6),                  -- Giá trị gốc của laptop theo tiêu chí
    laptop_value_normalized NUMERIC(10,6) NOT NULL,  -- Giá trị đã chuẩn hóa
    criterion_score NUMERIC(10,6) NOT NULL,          -- Điểm đóng góp = weight * normalized

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (evaluation_result_id, criterion_id)
);

-- Index để tăng tốc truy vấn cho bảng chi tiết
CREATE INDEX idx_evaluation_result_details_result_id
ON evaluation_result_details(evaluation_result_id);

CREATE INDEX idx_evaluation_result_details_criterion_id
ON evaluation_result_details(criterion_id);

-- ==========================================
-- PHẦN SHOPPING & CHATBOT (Bổ sung mới)
-- ==========================================

-- 11. Bảng Đơn hàng (Orders)
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(15, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, shipped, delivered, cancelled
    shipping_address TEXT NOT NULL,
    shipping_phone VARCHAR(20) NOT NULL,
    payment_method VARCHAR(50) DEFAULT 'cod', -- cod, banking
    payment_status VARCHAR(20) DEFAULT 'unpaid' -- unpaid, paid
);

-- 12. Bảng Chi tiết đơn hàng (Order Items)
CREATE TABLE order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    laptop_id BIGINT REFERENCES laptops(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    price_at_purchase NUMERIC(15, 2) NOT NULL -- Lưu giá tại thời điểm mua
);

-- 13. Bảng Đánh giá sản phẩm (Reviews)
CREATE TABLE reviews (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    laptop_id BIGINT NOT NULL REFERENCES laptops(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. Bảng Lịch sử Chatbot (Chat History)
CREATE TABLE chat_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL, -- Null nếu là khách vãng lai
    session_id VARCHAR(100), -- Để gom nhóm hội thoại
    message_content TEXT NOT NULL,
    sender VARCHAR(10) NOT NULL, -- 'user' hoặc 'bot'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);