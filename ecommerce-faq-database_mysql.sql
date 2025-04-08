-- Create database
CREATE DATABASE ecommerce_faq;
USE ecommerce_faq;

-- Table: FAQ Categories
CREATE TABLE faq_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

-- Table: FAQ Items
CREATE TABLE faq_items (
    faq_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    question VARCHAR(500) NOT NULL,
    answer TEXT NOT NULL,
    helpful_count INT DEFAULT 0,
    not_helpful_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_faq_category FOREIGN KEY (category_id) REFERENCES faq_categories(category_id) ON DELETE CASCADE,
    FULLTEXT (question, answer)
) ENGINE=InnoDB;

-- Table: FAQ Tags (For tagging FAQs)
CREATE TABLE faq_tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Table: FAQ Item Tags (Many-to-Many)
CREATE TABLE faq_item_tags (
    faq_id INT,
    tag_id INT,
    PRIMARY KEY (faq_id, tag_id),
    CONSTRAINT fk_faq FOREIGN KEY (faq_id) REFERENCES faq_items(faq_id) ON DELETE CASCADE,
    CONSTRAINT fk_tag FOREIGN KEY (tag_id) REFERENCES faq_tags(tag_id) ON DELETE CASCADE
);

-- Table: FAQ Search Log
CREATE TABLE faq_search_log (
    search_id INT AUTO_INCREMENT PRIMARY KEY,
    search_query VARCHAR(255) NOT NULL,
    results_count INT NOT NULL,
    session_id VARCHAR(100),
    user_ip VARCHAR(50),
    search_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table: Click Log (When a user clicks a FAQ from search results)
CREATE TABLE faq_click_log (
    click_id INT AUTO_INCREMENT PRIMARY KEY,
    search_id INT NOT NULL,
    faq_id INT NOT NULL,
    clicked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_search FOREIGN KEY (search_id) REFERENCES faq_search_log(search_id) ON DELETE CASCADE,
    CONSTRAINT fk_faq_click FOREIGN KEY (faq_id) REFERENCES faq_items(faq_id) ON DELETE CASCADE
);

-- Insert sample data
INSERT INTO faq_categories (name) VALUES 
('Orders & Shipping'),
('Payments & Refunds'),
('Account & Security'),
('Product Information'),
('Returns & Cancellations'),
('Technical Support'),
('Discounts & Promotions');

INSERT INTO faq_items (category_id, question, answer)
VALUES
-- Orders & Shipping
(1, 'How long does shipping take?', 'Shipping takes 3-5 business days for standard delivery.'),
(1, 'How can I track my order?', 'You can track your order using the tracking link provided in your email.'),
(1, 'Do you offer international shipping?', 'Yes, we ship worldwide. Delivery time varies by location.'),
(1, 'Can I change my shipping address after placing an order?', 'Once the order is shipped, we cannot change the address. Contact support for assistance.'),

-- Payments & Refunds
(2, 'Which payment methods are accepted?', 'We accept credit/debit cards, PayPal, and Apple Pay.'),
(2, 'How can I request a refund?', 'Refunds can be requested through your account under "Order History".'),
(2, 'Why was my payment declined?', 'Common reasons include insufficient funds, incorrect card details, or security restrictions from your bank.'),

-- Account & Security
(3, 'How do I reset my password?', 'Click "Forgot Password" on the login page to reset it.'),
(3, 'How can I change my email address?', 'Go to Account Settings > Email and update your email.'),
(3, 'Is my personal data safe?', 'We use encryption and secure storage to protect your data.'),

-- Product Information
(4, 'Are the products under warranty?', 'Yes, all our products come with a 1-year warranty.'),
(4, 'How do I check product availability?', 'Product availability is shown on the product page.'),

-- Returns & Cancellations
(5, 'What is the return policy?', 'You can return unused products within 30 days for a full refund.'),
(5, 'How long does it take to process a return?', 'Returns are processed within 5-7 business days.'),
(5, 'Can I cancel my order?', 'Orders can be canceled within 24 hours after purchase.'),

-- Technical Support
(6, 'How do I contact technical support?', 'You can reach our support team via chat, phone, or email.'),
(6, 'Why is my order status not updating?', 'It can take up to 24 hours for tracking details to appear.'),
(6, 'Do you provide installation guides?', 'Yes, installation guides are available on the product page.'),

-- Discounts & Promotions
(7, 'How can I apply a discount code?', 'Enter the discount code at checkout to apply it.'),
(7, 'Why is my discount code not working?', 'Ensure the code is valid and meets the minimum purchase requirement.');

INSERT INTO faq_tags (name) VALUES 
('shipping'), ('tracking'), ('payment'), ('refund'), 
('security'), ('warranty'), ('returns'), ('discount'), 
('support'), ('account');

INSERT INTO faq_item_tags (faq_id, tag_id) VALUES 
(1, 1), (2, 2), (3, 1), (4, 1),
(5, 3), (6, 4), (7, 3),
(8, 5), (9, 5), (10, 5),
(11, 6), (12, 6),
(13, 7), (14, 7), (15, 7),
(16, 9), (17, 9), (18, 9),
(19, 8), (20, 8);

-- Create stored procedure for search using full-text search
DELIMITER //
CREATE PROCEDURE search_faqs(IN p_search_term VARCHAR(255))
BEGIN
    SELECT 
        f.faq_id, f.question, LEFT(f.answer, 200) AS preview_answer,
        c.name AS category, f.helpful_count, f.not_helpful_count
    FROM faq_items f
    JOIN faq_categories c ON f.category_id = c.category_id
    WHERE 
        MATCH(f.question, f.answer) AGAINST(p_search_term IN NATURAL LANGUAGE MODE)
    ORDER BY f.helpful_count DESC
    LIMIT 10;
END //
DELIMITER ;

-- Create index for full-text search
ALTER TABLE faq_items ADD FULLTEXT INDEX ft_question_answer (question, answer);