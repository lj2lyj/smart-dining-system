"""
数据库连接配置 - PHPStudy MySQL
"""
import os

# MySQL 连接配置（可通过环境变量覆盖）
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "root"),
    "db": os.getenv("MYSQL_DATABASE", "smart_dining"),
    "charset": "utf8mb4",
    "autocommit": True,
    "minsize": 1,
    "maxsize": 10,
}
