-- Create database
CREATE DATABASE ecommerce_ticketing;
USE ecommerce_ticketing;

-- Customers table
CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Support agents table
CREATE TABLE agents (
    agent_id VARCHAR(20) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Orders table (simplified)
CREATE TABLE orders (
    order_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(30) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Ticket categories table
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    parent_id INT,
    is_subcategory BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id)
);

-- Ticket status table
CREATE TABLE ticket_statuses (
    status_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    description TEXT,
    is_closed BOOLEAN DEFAULT FALSE
);

-- Communication channels table
CREATE TABLE channels (
    channel_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    description TEXT
);

-- Priority levels table
CREATE TABLE priorities (
    priority_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) NOT NULL,
    description TEXT,
    sla_hours INT  -- Service Level Agreement in hours
);

-- Main tickets table
CREATE TABLE tickets (
    ticket_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    category_id INT NOT NULL,
    subcategory_id INT,
    status_id INT NOT NULL,
    priority_id INT NOT NULL,
    agent_id VARCHAR(20),
    channel_id INT NOT NULL,
    order_id VARCHAR(20),
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    internal_notes TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    closed_at TIMESTAMP NULL,
    satisfaction_level INT CHECK (satisfaction_level BETWEEN 1 AND 5),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (subcategory_id) REFERENCES categories(category_id),
    FOREIGN KEY (status_id) REFERENCES ticket_statuses(status_id),
    FOREIGN KEY (priority_id) REFERENCES priorities(priority_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (channel_id) REFERENCES channels(channel_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FULLTEXT (subject, description)
) ENGINE=InnoDB;

-- Ticket interactions table
CREATE TABLE interactions (
    interaction_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id VARCHAR(20) NOT NULL,
    interaction_type VARCHAR(30) NOT NULL,
    message TEXT NOT NULL,
    author_type VARCHAR(10) NOT NULL CHECK (author_type IN ('Customer', 'Agent', 'System')),
    author_id VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_internal BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id),
    FULLTEXT (message)
) ENGINE=InnoDB;

-- Ticket attachments table
CREATE TABLE attachments (
    attachment_id INT AUTO_INCREMENT PRIMARY KEY,
    interaction_id INT,
    ticket_id VARCHAR(20) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(100),
    file_size INT,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    uploader_type VARCHAR(10) NOT NULL CHECK (uploader_type IN ('Customer', 'Agent')),
    uploader_id VARCHAR(20),
    FOREIGN KEY (interaction_id) REFERENCES interactions(interaction_id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
);

-- Ticket tags table
CREATE TABLE tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Ticket-tag relationship (many-to-many)
CREATE TABLE ticket_tags (
    ticket_id VARCHAR(20) NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (ticket_id, tag_id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id),
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id)
);

-- Add indexes for better performance
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_status ON tickets(status_id);
CREATE INDEX idx_tickets_agent ON tickets(agent_id);
CREATE INDEX idx_tickets_created ON tickets(created_at);
CREATE INDEX idx_interactions_ticket ON interactions(ticket_id);
CREATE INDEX idx_interactions_created ON interactions(created_at);
CREATE INDEX idx_attachments_ticket ON attachments(ticket_id);

-- Insert default statuses
INSERT INTO ticket_statuses (name, description, is_closed) VALUES 
('Open', 'Ticket is newly created and awaiting agent assignment', FALSE),
('In Progress', 'Ticket is assigned and being worked on', FALSE),
('Pending Customer', 'Waiting for customer reply', FALSE),
('Pending Third-Party', 'Waiting for response from external department or vendor', FALSE),
('Resolved', 'Issue has been resolved', TRUE),
('Closed', 'Ticket has been closed', TRUE),
('Cancelled', 'Ticket was cancelled', TRUE);

-- Insert default priorities
INSERT INTO priorities (name, description, sla_hours) VALUES 
('Low', 'Non-urgent issues that can wait', 72),
('Medium', 'Standard issues requiring normal response time', 24),
('High', 'Urgent issues requiring fast response', 8),
('Critical', 'Emergency issues requiring immediate attention', 2);

-- Insert default channels
INSERT INTO channels (name, description) VALUES 
('Email', 'Customer support via email'),
('Phone', 'Customer support via phone call'),
('Chat', 'Live chat support'),
('Web Form', 'Support request submitted via website form'),
('Social Media', 'Support request via social media platform'),
('Mobile App', 'Support request via mobile application');

-- Insert default categories
INSERT INTO categories (name, description, is_subcategory) VALUES 
('Order', 'Issues related to orders', FALSE),
('Product', 'Issues related to products', FALSE),
('Payment', 'Issues related to payments and refunds', FALSE),
('Shipping', 'Issues related to delivery and shipping', FALSE),
('Account', 'Issues related to customer accounts', FALSE),
('Technical', 'Technical issues with website or app', FALSE),
('Other', 'Other issues not covered by other categories', FALSE);

-- Insert default subcategories
INSERT INTO categories (name, description, parent_id, is_subcategory) VALUES
('Order Status', 'Questions about order status', 1, TRUE),
('Order Modification', 'Changes to existing orders', 1, TRUE),
('Order Cancellation', 'Requests to cancel orders', 1, TRUE),
('Delivery Delay', 'Issues with delayed orders', 1, TRUE),
('Defective Product', 'Issues with product defects', 2, TRUE),
('Product Information', 'Questions about product details', 2, TRUE),
('Missing Parts', 'Products with missing components', 2, TRUE),
('Product Return', 'Requests to return products', 2, TRUE),
('Payment Failure', 'Issues with failed payments', 3, TRUE),
('Refund Request', 'Requests for refunds', 3, TRUE),
('Double Charge', 'Issues with duplicate charges', 3, TRUE),
('Invoice Issue', 'Problems with invoices', 3, TRUE),
('Wrong Address', 'Issues with incorrect shipping address', 4, TRUE),
('Tracking Issues', 'Problems tracking shipments', 4, TRUE),
('Damaged in Transit', 'Products damaged during shipping', 4, TRUE),
('Failed Delivery', 'Unsuccessful delivery attempts', 4, TRUE),
('Login Problems', 'Issues accessing accounts', 5, TRUE),
('Password Reset', 'Password recovery requests', 5, TRUE),
('Account Update', 'Changes to account information', 5, TRUE),
('Account Deletion', 'Requests to delete accounts', 5, TRUE);

-- Insert sample customers
INSERT INTO customers (customer_id, full_name, email, phone) VALUES
('CLT-1289', 'Marco Bianchi', 'marco.bianchi@email.it', '+39 331 1234567'),
('CLT-4567', 'Giulia Rossi', 'g.rossi@email.it', '+39 345 7654321'),
('CLT-7823', 'Antonio Verdi', 'a.verdi@email.it', '+39 347 8901234'),
('CLT-2156', 'Sofia Esposito', 's.esposito@email.it', '+39 339 2345678'),
('CLT-9023', 'Luca Ferretti', 'l.ferretti@email.it', '+39 333 5678901');

-- Insert sample agents
INSERT INTO agents (agent_id, username, full_name, email, department) VALUES
('AG-001', 'support_01', 'Alex Support', 'alex.support@company.com', 'General Support'),
('AG-002', 'support_02', 'Maria Helper', 'maria.helper@company.com', 'Account Support'),
('AG-003', 'support_03', 'John Tech', 'john.tech@company.com', 'Technical Support'),
('AG-004', 'support_04', 'Sara Returns', 'sara.returns@company.com', 'Returns Department'),
('AG-005', 'support_05', 'Tom Finance', 'tom.finance@company.com', 'Payments Support');

-- Insert sample orders
INSERT INTO orders (order_id, customer_id, total_amount, status) VALUES
('ORD-95431', 'CLT-1289', 129.99, 'Processing'),
('ORD-85692', 'CLT-4567', 899.00, 'Delivered'),
('ORD-79054', 'CLT-7823', 549.99, 'Returned'),
('ORD-98765', 'CLT-9023', 75.50, 'Shipped');

-- Insert sample tickets
INSERT INTO tickets (
    ticket_id, customer_id, category_id, subcategory_id, 
    status_id, priority_id, agent_id, channel_id, 
    order_id, subject, description, internal_notes, 
    created_at, updated_at, satisfaction_level
) VALUES
(
    'TK-0001', 'CLT-1289', 1, 1, 
    1, 2, 'AG-001', 1, 
    'ORD-95431', 'Shipping delay inquiry', 
    'I placed an order on 12/28/2024 (order #ORD-95431) but haven\'t received any shipping information yet. On the website my order still shows as processing. I would like to know when it will be shipped.',
    'Check with warehouse about product availability.',
    '2025-01-03 09:12:34', '2025-01-03 14:28:15', NULL
),
(
    'TK-0002', 'CLT-4567', 2, 5, 
    5, 3, 'AG-003', 3, 
    'ORD-85692', 'Defective laptop', 
    'I received a laptop that has power-on issues. Sometimes it starts normally, other times it gets stuck with a black screen. I\'ve already tried factory reset but the problem persists.',
    'Hardware issue confirmed, replacement approved.',
    '2025-01-02 11:45:22', '2025-01-04 16:10:05', 4
),
(
    'TK-0003', 'CLT-7823', 3, 10, 
    2, 2, 'AG-005', 2, 
    'ORD-79054', 'Refund not received', 
    'I returned a TV purchased last month (order #ORD-79054) but haven\'t received my refund yet. The return shows as delivered and accepted for more than 10 days now.',
    'Refund approved but waiting for payment system processing. Escalate to accounting department.',
    '2025-01-04 08:30:10', '2025-01-05 11:22:40', NULL
),
(
    'TK-0004', 'CLT-2156', 5, 18, 
    5, 1, 'AG-002', 1, 
    NULL, 'Cannot reset password', 
    'I can\'t access my account. I tried to reset my password but I\'m not receiving the recovery email link.',
    'Issue resolved. Reset email was being blocked by spam filters.',
    '2025-01-01 15:23:44', '2025-01-03 16:40:15', 5
),
(
    'TK-0005', 'CLT-9023', 4, 13, 
    1, 3, NULL, 3, 
    'ORD-98765', 'Wrong address for delivery', 
    'I just realized I entered the wrong address for my order #ORD-98765. I confused the house number, I wrote 12 instead of 21. The courier is supposed to deliver tomorrow. Is it possible to change the address?',
    '',
    '2025-01-05 10:05:17', '2025-01-05 10:05:17', NULL
);

-- Insert sample interactions for the tickets
INSERT INTO interactions (ticket_id, interaction_type, message, author_type, author_id, created_at, is_internal) VALUES
-- Ticket 1 interactions
('TK-0001', 'Ticket Creation', 'Ticket created by user', 'Customer', 'CLT-1289', '2025-01-03 09:12:34', FALSE),
('TK-0001', 'Note', 'Checked the order, there are delivery delays from the supplier. Inform the customer about expected timeframes.', 'Agent', 'AG-001', '2025-01-03 14:28:15', TRUE),

-- Ticket 2 interactions
('TK-0002', 'Ticket Creation', 'Ticket created by user', 'Customer', 'CLT-4567', '2025-01-02 11:45:22', FALSE),
('TK-0002', 'Response', 'Good morning Ms. Rossi, I\'m sorry for the inconvenience. Could you please send us a short video showing the issue? This would help us better diagnose the situation.', 'Agent', 'AG-003', '2025-01-02 13:20:45', FALSE),
('TK-0002', 'Response', 'I sent the video via email to the address you provided.', 'Customer', 'CLT-4567', '2025-01-03 09:15:33', FALSE),
('TK-0002', 'Response', 'Thank you for the video. We have verified that this is a hardware issue. We can proceed with replacing the product. You will need to return the defective one using the return label we will send you via email.', 'Agent', 'AG-003', '2025-01-03 14:50:12', FALSE),
('TK-0002', 'Response', 'Replacement approved and return procedure initiated. The new product will be shipped within 2 business days.', 'Agent', 'AG-003', '2025-01-04 16:10:05', FALSE),

-- Ticket 3 interactions
('TK-0003', 'Ticket Creation', 'Ticket created during call with customer', 'Agent', 'AG-002', '2025-01-04 08:30:10', FALSE),
('TK-0003', 'Response', 'Dear Mr. Verdi, we have verified that your return has been received and approved. We are escalating the processing of the refund which should be visible on your account within the next 3-5 business days.', 'Agent', 'AG-005', '2025-01-04 09:45:23', FALSE),
('TK-0003', 'Note', 'Confirmed with accounting that the refund was processed today. Customer should receive it within 48 hours.', 'Agent', 'AG-005', '2025-01-05 11:22:40', TRUE),

-- Ticket 4 interactions
('TK-0004', 'Ticket Creation', 'Ticket created by user', 'Customer', 'CLT-2156', '2025-01-01 15:23:44', FALSE),
('TK-0004', 'Response', 'Good morning Ms. Esposito, I have manually sent a new password reset link. Please also check your spam folder.', 'Agent', 'AG-002', '2025-01-02 09:10:22', FALSE),
('TK-0004', 'Response', 'Thank you very much, I found the email in spam and was able to change my password. I can now access my account normally.', 'Customer', 'CLT-2156', '2025-01-03 14:25:05', FALSE),
('TK-0004', 'Response', 'Great! I\'m glad the issue has been resolved. Don\'t hesitate to contact us for any other needs.', 'Agent', 'AG-002', '2025-01-03 16:40:15', FALSE),

-- Ticket 5 interactions
('TK-0005', 'Ticket Creation', 'Ticket created by user', 'Customer', 'CLT-9023', '2025-01-05 10:05:17', FALSE);

-- Create full text indexes
ALTER TABLE tickets ADD FULLTEXT INDEX ft_ticket_content (subject, description);
ALTER TABLE interactions ADD FULLTEXT INDEX ft_interaction_message (message);

-- Create views for easier reporting

-- Open tickets view
CREATE VIEW view_open_tickets AS
SELECT t.ticket_id, t.subject, c.full_name AS customer, 
       cat.name AS category, subcat.name AS subcategory,
       p.name AS priority, ch.name AS channel,
       a.username AS assigned_agent, t.created_at,
       TIMESTAMPDIFF(HOUR, t.created_at, NOW()) AS hours_open
FROM tickets t
JOIN customers c ON t.customer_id = c.customer_id
JOIN categories cat ON t.category_id = cat.category_id
LEFT JOIN categories subcat ON t.subcategory_id = subcat.category_id
JOIN priorities p ON t.priority_id = p.priority_id
JOIN channels ch ON t.channel_id = ch.channel_id
LEFT JOIN agents a ON t.agent_id = a.agent_id
JOIN ticket_statuses ts ON t.status_id = ts.status_id
WHERE ts.is_closed = FALSE;

-- SLA breached tickets view
CREATE VIEW view_sla_breached_tickets AS
SELECT t.ticket_id, t.subject, c.full_name AS customer, 
       p.name AS priority, p.sla_hours,
       TIMESTAMPDIFF(HOUR, t.created_at, NOW()) AS hours_open,
       a.username AS assigned_agent
FROM tickets t
JOIN customers c ON t.customer_id = c.customer_id
JOIN priorities p ON t.priority_id = p.priority_id
LEFT JOIN agents a ON t.agent_id = a.agent_id
JOIN ticket_statuses ts ON t.status_id = ts.status_id
WHERE ts.is_closed = FALSE 
AND TIMESTAMPDIFF(HOUR, t.created_at, NOW()) > p.sla_hours;

-- Agent performance view
CREATE VIEW view_agent_performance AS
SELECT 
    a.username,
    COUNT(DISTINCT t.ticket_id) AS total_tickets,
    SUM(CASE WHEN ts.is_closed = TRUE THEN 1 ELSE 0 END) AS closed_tickets,
    AVG(CASE WHEN t.satisfaction_level IS NOT NULL THEN t.satisfaction_level ELSE NULL END) AS avg_satisfaction,
    AVG(CASE WHEN ts.is_closed = TRUE THEN TIMESTAMPDIFF(HOUR, t.created_at, t.closed_at) ELSE NULL END) AS avg_resolution_hours
FROM agents a
LEFT JOIN tickets t ON a.agent_id = t.agent_id
LEFT JOIN ticket_statuses ts ON t.status_id = ts.status_id
GROUP BY a.username;

-- Customer satisfaction view
CREATE VIEW view_customer_satisfaction AS
SELECT 
    cat.name AS category,
    COUNT(t.ticket_id) AS total_tickets,
    COUNT(t.satisfaction_level) AS rated_tickets,
    AVG(t.satisfaction_level) AS avg_satisfaction,
    SUM(CASE WHEN t.satisfaction_level = 5 THEN 1 ELSE 0 END) AS five_star,
    SUM(CASE WHEN t.satisfaction_level = 4 THEN 1 ELSE 0 END) AS four_star,
    SUM(CASE WHEN t.satisfaction_level = 3 THEN 1 ELSE 0 END) AS three_star,
    SUM(CASE WHEN t.satisfaction_level = 2 THEN 1 ELSE 0 END) AS two_star,
    SUM(CASE WHEN t.satisfaction_level = 1 THEN 1 ELSE 0 END) AS one_star
FROM tickets t
JOIN categories cat ON t.category_id = cat.category_id
WHERE t.satisfaction_level IS NOT NULL
GROUP BY cat.name;

-- Create a procedure for full-text search on tickets
DELIMITER //
CREATE PROCEDURE search_tickets(IN p_search_term VARCHAR(255))
BEGIN
    SELECT 
        t.ticket_id, t.subject, LEFT(t.description, 200) AS description_preview,
        c.full_name AS customer_name, 
        cat.name AS category, p.name AS priority,
        ts.name AS status, a.username AS agent
    FROM tickets t
    JOIN customers c ON t.customer_id = c.customer_id
    JOIN categories cat ON t.category_id = cat.category_id
    JOIN priorities p ON t.priority_id = p.priority_id
    JOIN ticket_statuses ts ON t.status_id = ts.status_id
    LEFT JOIN agents a ON t.agent_id = a.agent_id
    WHERE MATCH(t.subject, t.description) AGAINST(p_search_term IN NATURAL LANGUAGE MODE)
    ORDER BY t.created_at DESC
    LIMIT 20;
END //
DELIMITER ;