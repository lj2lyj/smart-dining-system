-- ============================================
-- 智慧餐饮结算系统 - MySQL 数据库建表脚本
-- 适用于 PHPStudy MySQL 5.7+ / 8.0+
-- ============================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS smart_dining
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE smart_dining;

-- ============================================
-- 1. 菜品表 dishes
-- ============================================
CREATE TABLE IF NOT EXISTS dishes (
    id VARCHAR(50) PRIMARY KEY COMMENT '菜品ID',
    name VARCHAR(100) NOT NULL COMMENT '菜品中文名',
    name_en VARCHAR(100) DEFAULT NULL COMMENT '菜品英文名',
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '价格',
    category VARCHAR(50) DEFAULT 'other' COMMENT '分类: meat/vegetable/staple/drink/other',
    source VARCHAR(20) DEFAULT 'manual' COMMENT '来源: yolo/manual',
    yolo_class_id INT DEFAULT NULL COMMENT 'YOLO模型类别ID',
    description TEXT COMMENT '菜品描述',
    allergens JSON COMMENT '过敏原列表',
    nutrition JSON COMMENT '营养信息',
    stock INT DEFAULT 100 COMMENT '库存数量',
    is_available TINYINT(1) DEFAULT 1 COMMENT '是否可用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_yolo_class_id (yolo_class_id),
    INDEX idx_category (category),
    INDEX idx_source (source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='菜品表';

-- ============================================
-- 2. 订单表 orders
-- ============================================
CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(50) PRIMARY KEY COMMENT '订单ID',
    total_amount DECIMAL(10,2) DEFAULT 0.00 COMMENT '订单总金额',
    original_amount DECIMAL(10,2) DEFAULT 0.00 COMMENT '原始金额',
    discount_amount DECIMAL(10,2) DEFAULT 0.00 COMMENT '优惠金额',
    payment_method VARCHAR(50) DEFAULT NULL COMMENT '支付方式',
    status VARCHAR(20) DEFAULT 'completed' COMMENT '订单状态',
    items JSON COMMENT '订单详情（菜品列表）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';

-- ============================================
-- 3. 促销表 promotions
-- ============================================
CREATE TABLE IF NOT EXISTS promotions (
    id VARCHAR(50) PRIMARY KEY COMMENT '促销ID',
    name VARCHAR(100) NOT NULL COMMENT '促销名称',
    type VARCHAR(50) DEFAULT NULL COMMENT '促销类型',
    discount_value DECIMAL(10,2) DEFAULT 0.00 COMMENT '折扣值',
    min_amount DECIMAL(10,2) DEFAULT 0.00 COMMENT '最低消费',
    applicable_dishes JSON COMMENT '适用菜品',
    start_time DATETIME DEFAULT NULL COMMENT '开始时间',
    end_time DATETIME DEFAULT NULL COMMENT '结束时间',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_active (is_active),
    INDEX idx_time_range (start_time, end_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='促销表';

-- ============================================
-- 4. 识别日志表 recognition_logs
-- ============================================
CREATE TABLE IF NOT EXISTS recognition_logs (
    id VARCHAR(50) PRIMARY KEY COMMENT '日志ID',
    image_size INT DEFAULT 0 COMMENT '图片大小(bytes)',
    dishes_count INT DEFAULT 0 COMMENT '识别菜品数',
    unrecognized_count INT DEFAULT 0 COMMENT '未识别数',
    processing_time_ms DECIMAL(10,2) DEFAULT 0.00 COMMENT '处理耗时(ms)',
    source VARCHAR(50) DEFAULT NULL COMMENT '来源: camera/upload',
    filename VARCHAR(255) DEFAULT NULL COMMENT '文件名',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='识别日志表';

-- ============================================
-- 5. 系统设置表 settings
-- ============================================
CREATE TABLE IF NOT EXISTS settings (
    setting_key VARCHAR(100) PRIMARY KEY COMMENT '设置键名',
    setting_value TEXT COMMENT '设置值(JSON)',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统设置表';

-- ============================================
-- 初始化默认设置
-- ============================================
INSERT IGNORE INTO settings (setting_key, setting_value) VALUES
    ('confidence_threshold', '0.15'),
    ('auto_recognize_interval', '3000'),
    ('model_path', 'null'),
    ('enable_logging', 'true');

-- ============================================
-- 初始化 36 种 YOLO 菜品数据
-- ============================================
INSERT IGNORE INTO dishes (id, name, name_en, price, category, source, yolo_class_id, description, allergens, nutrition, stock, is_available) VALUES
('dish_001', 'AW可乐', 'AW Cola', 5.00, 'drink', 'yolo', 0, 'AW根汁汽水', '[]', '{"calories":170,"protein":0,"carbohydrates":46,"fat":0,"fiber":0,"sodium":65}', 100, 1),
('dish_002', '北京牛肉', 'Beijing Beef', 22.00, 'meat', 'yolo', 1, '甜辣酱汁牛肉配青红椒', '["大豆"]', '{"calories":470,"protein":26,"carbohydrates":36,"fat":24,"fiber":2,"sodium":890}', 50, 1),
('dish_003', '炒面', 'Chow Mein', 12.00, 'staple', 'yolo', 2, '经典中式炒面', '["小麦"]', '{"calories":510,"protein":13,"carbohydrates":80,"fat":16,"fiber":4,"sodium":980}', 80, 1),
('dish_004', '炒饭', 'Fried Rice', 14.00, 'staple', 'yolo', 3, '蛋炒饭', '["鸡蛋","大豆"]', '{"calories":520,"protein":12,"carbohydrates":85,"fat":16,"fiber":1,"sodium":850}', 80, 1),
('dish_005', '薯饼', 'Hashbrown', 6.00, 'other', 'yolo', 4, '香脆薯饼', '[]', '{"calories":150,"protein":1,"carbohydrates":15,"fat":9,"fiber":1,"sodium":310}', 100, 1),
('dish_006', '核桃虾', 'Honey Walnut Shrimp', 28.00, 'meat', 'yolo', 5, '蜂蜜核桃虾仁', '["虾","核桃","鸡蛋"]', '{"calories":360,"protein":13,"carbohydrates":35,"fat":19,"fiber":1,"sodium":440}', 40, 1),
('dish_007', '宫保鸡丁', 'Kung Pao Chicken', 20.00, 'meat', 'yolo', 6, '花生与鸡肉的经典搭配', '["花生"]', '{"calories":290,"protein":16,"carbohydrates":14,"fat":19,"fiber":1,"sodium":780}', 60, 1),
('dish_008', '四季豆鸡胸', 'String Bean Chicken Breast', 18.00, 'meat', 'yolo', 7, '四季豆配嫩滑鸡胸肉', '[]', '{"calories":190,"protein":14,"carbohydrates":13,"fat":9,"fiber":2,"sodium":560}', 60, 1),
('dish_009', '时蔬拼盘', 'Super Greens', 10.00, 'vegetable', 'yolo', 8, '混合新鲜蔬菜', '[]', '{"calories":90,"protein":6,"carbohydrates":10,"fat":3,"fiber":5,"sodium":420}', 80, 1),
('dish_010', '橙汁鸡', 'The Original Orange Chicken', 22.00, 'meat', 'yolo', 9, '经典橙汁鸡块', '["小麦","鸡蛋"]', '{"calories":490,"protein":25,"carbohydrates":51,"fat":21,"fiber":0,"sodium":820}', 50, 1),
('dish_011', '白米饭', 'White Steamed Rice', 3.00, 'staple', 'yolo', 10, '香软白米饭', '[]', '{"calories":380,"protein":7,"carbohydrates":87,"fat":0,"fiber":0,"sodium":0}', 200, 1),
('dish_012', '黑椒饭', 'Black Pepper Rice Bowl', 16.00, 'staple', 'yolo', 11, '黑椒酱配米饭', '["大豆"]', '{"calories":450,"protein":15,"carbohydrates":70,"fat":12,"fiber":2,"sodium":730}', 60, 1),
('dish_013', '汉堡', 'Burger', 18.00, 'other', 'yolo', 12, '经典汉堡', '["小麦","鸡蛋"]', '{"calories":540,"protein":25,"carbohydrates":40,"fat":30,"fiber":2,"sodium":950}', 50, 1),
('dish_014', '胡萝卜炒蛋', 'Carrot Eggs', 10.00, 'vegetable', 'yolo', 13, '胡萝卜炒鸡蛋', '["鸡蛋"]', '{"calories":160,"protein":10,"carbohydrates":8,"fat":10,"fiber":2,"sodium":350}', 70, 1),
('dish_015', '芝士汉堡', 'Cheese Burger', 22.00, 'other', 'yolo', 14, '芝士牛肉汉堡', '["小麦","牛奶","鸡蛋"]', '{"calories":630,"protein":30,"carbohydrates":42,"fat":38,"fiber":2,"sodium":1100}', 40, 1),
('dish_016', '鸡肉华夫饼', 'Chicken Waffle', 20.00, 'other', 'yolo', 15, '炸鸡配华夫饼', '["小麦","鸡蛋","牛奶"]', '{"calories":580,"protein":28,"carbohydrates":48,"fat":30,"fiber":1,"sodium":870}', 40, 1),
('dish_017', '鸡块', 'Chicken Nuggets', 12.00, 'meat', 'yolo', 16, '香酥鸡块', '["小麦"]', '{"calories":270,"protein":14,"carbohydrates":16,"fat":17,"fiber":0,"sodium":540}', 80, 1),
('dish_018', '大白菜', 'Chinese Cabbage', 8.00, 'vegetable', 'yolo', 17, '清炒大白菜', '[]', '{"calories":60,"protein":2,"carbohydrates":8,"fat":2,"fiber":3,"sodium":280}', 90, 1),
('dish_019', '中式香肠', 'Chinese Sausage', 12.00, 'meat', 'yolo', 18, '广式腊肠', '[]', '{"calories":320,"protein":16,"carbohydrates":6,"fat":26,"fiber":0,"sodium":700}', 60, 1),
('dish_020', '脆玉米', 'Crispy Corn', 8.00, 'other', 'yolo', 19, '酥脆玉米粒', '[]', '{"calories":200,"protein":3,"carbohydrates":28,"fat":10,"fiber":2,"sodium":400}', 70, 1),
('dish_021', '咖喱', 'Curry', 16.00, 'meat', 'yolo', 20, '日式咖喱', '["小麦"]', '{"calories":350,"protein":14,"carbohydrates":30,"fat":18,"fiber":3,"sodium":650}', 50, 1),
('dish_022', '薯条', 'French Fries', 8.00, 'other', 'yolo', 21, '金黄薯条', '[]', '{"calories":340,"protein":4,"carbohydrates":44,"fat":16,"fiber":4,"sodium":230}', 100, 1),
('dish_023', '炸鸡', 'Fried Chicken', 18.00, 'meat', 'yolo', 22, '美式炸鸡', '["小麦"]', '{"calories":400,"protein":28,"carbohydrates":15,"fat":26,"fiber":0,"sodium":680}', 50, 1),
('dish_024', '中式炸鸡', 'Chinese Fried Chicken', 16.00, 'meat', 'yolo', 23, '中式香炸鸡块', '["小麦"]', '{"calories":380,"protein":26,"carbohydrates":14,"fat":24,"fiber":0,"sodium":620}', 50, 1),
('dish_025', '煎饺', 'Fried Dumplings', 12.00, 'staple', 'yolo', 24, '香脆煎饺', '["小麦"]', '{"calories":280,"protein":12,"carbohydrates":30,"fat":12,"fiber":1,"sodium":600}', 60, 1),
('dish_026', '煎蛋', 'Fried Eggs', 5.00, 'other', 'yolo', 25, '香煎荷包蛋', '["鸡蛋"]', '{"calories":90,"protein":6,"carbohydrates":0,"fat":7,"fiber":0,"sodium":150}', 100, 1),
('dish_027', '芒果鸡肉口袋饼', 'Mango Chicken Pocket', 20.00, 'other', 'yolo', 26, '芒果鸡肉口袋饼', '["小麦"]', '{"calories":420,"protein":22,"carbohydrates":45,"fat":16,"fiber":2,"sodium":580}', 40, 1),
('dish_028', '马苏里拉汉堡', 'Mozza Burger', 24.00, 'other', 'yolo', 27, '马苏里拉芝士汉堡', '["小麦","牛奶"]', '{"calories":650,"protein":32,"carbohydrates":44,"fat":40,"fiber":2,"sodium":1050}', 40, 1),
('dish_029', '绿豆芽', 'Mung Bean Sprouts', 8.00, 'vegetable', 'yolo', 28, '清炒绿豆芽', '[]', '{"calories":50,"protein":3,"carbohydrates":6,"fat":1,"fiber":2,"sodium":200}', 90, 1),
('dish_030', '鸡米花', 'Nugget', 10.00, 'meat', 'yolo', 29, '一口鸡米花', '["小麦"]', '{"calories":250,"protein":12,"carbohydrates":15,"fat":15,"fiber":0,"sodium":500}', 80, 1),
('dish_031', '印尼土豆饼', 'Perkedel', 8.00, 'other', 'yolo', 30, '印尼风味土豆饼', '["鸡蛋"]', '{"calories":180,"protein":5,"carbohydrates":20,"fat":9,"fiber":2,"sodium":350}', 60, 1),
('dish_032', '米饭', 'Rice', 3.00, 'staple', 'yolo', 31, '普通米饭', '[]', '{"calories":130,"protein":2.5,"carbohydrates":28,"fat":0.3,"fiber":0.4,"sodium":1}', 200, 1),
('dish_033', '雪碧', 'Sprite', 5.00, 'drink', 'yolo', 32, '冰镇雪碧', '[]', '{"calories":140,"protein":0,"carbohydrates":38,"fat":0,"fiber":0,"sodium":65}', 100, 1),
('dish_034', '芝士蘸酱', 'Tostitos Cheese Dip Sauce', 6.00, 'other', 'yolo', 33, '多力多滋芝士蘸酱', '["牛奶"]', '{"calories":40,"protein":1,"carbohydrates":3,"fat":3,"fiber":0,"sodium":280}', 80, 1),
('dish_035', '三角薯饼', 'Triangle Hash Brown', 6.00, 'other', 'yolo', 34, '三角形香脆薯饼', '[]', '{"calories":140,"protein":1,"carbohydrates":14,"fat":8,"fiber":1,"sodium":290}', 100, 1),
('dish_036', '空心菜', 'Water Spinach', 10.00, 'vegetable', 'yolo', 35, '清炒空心菜', '[]', '{"calories":70,"protein":3,"carbohydrates":8,"fat":2,"fiber":3,"sodium":250}', 80, 1);

-- 手动添加菜品
INSERT IGNORE INTO dishes (id, name, name_en, price, category, source, yolo_class_id, description, allergens, nutrition, stock, is_available) VALUES
('manual_001', '鱼香肉丝', 'Yu-Shiang Pork', 16.00, 'meat', 'manual', NULL, '经典川菜', '[]', '{"calories":280,"protein":18,"carbohydrates":15,"fat":16,"fiber":2,"sodium":750}', 40, 1),
('manual_002', '麻婆豆腐', 'Mapo Tofu', 14.00, 'vegetable', 'manual', NULL, '麻辣鲜香', '["大豆"]', '{"calories":200,"protein":14,"carbohydrates":8,"fat":12,"fiber":2,"sodium":900}', 45, 1),
('manual_003', '宫保鸡丁', 'Kung Pao Chicken', 18.00, 'meat', 'manual', NULL, '花生与鸡肉的完美搭配', '["花生"]', '{"calories":320,"protein":22,"carbohydrates":12,"fat":20,"fiber":1,"sodium":680}', 35, 1);
