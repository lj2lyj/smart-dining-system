# 智慧餐饮结算系统 - 阿里云部署指南

## 一、阿里云服务器选购建议

### 推荐配置

| 配置项 | 推荐选择 | 说明 |
|--------|----------|------|
| **地域** | 华东1（杭州）或华东2（上海） | 选择距离用户最近的地域 |
| **实例规格** | ecs.g7.large (2vCPU 8GB) | 如需运行YOLOv13模型，建议 ecs.gn6i-c4g1.xlarge (GPU) |
| **操作系统** | **Ubuntu 22.04 LTS 64位** | 稳定、社区支持好、软件包新 |
| **系统盘** | ESSD云盘 40GB | 足够系统和应用使用 |
| **带宽** | 按固定带宽 5Mbps 或按流量 | 根据预计访问量选择 |
| **安全组** | 开放 22, 80, 443, 8000 端口 | SSH、HTTP、HTTPS、API |

> **预算参考**：基础配置约 200-400元/月，GPU版本约 1500-3000元/月

---

## 二、服务器初始化

### 2.1 首次登录

```bash
# 使用SSH连接（替换为你的公网IP）
ssh root@你的服务器IP
```

### 2.2 创建部署用户（推荐，避免使用root）

```bash
# 创建用户
adduser deploy
usermod -aG sudo deploy

# 切换到新用户
su - deploy
```

### 2.3 更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 三、安装预装软件

### 3.1 安装基础工具

```bash
sudo apt install -y git curl wget vim htop unzip
```

### 3.2 安装 Python 3.11

```bash
# 添加 deadsnakes PPA
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# 安装 Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 设置默认 Python
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 验证
python3 --version  # 应显示 Python 3.11.x
```

### 3.3 安装 Node.js 20到这111111111111111111111111111111111111111111111111111111

```bash
# 使用 NodeSource 安装
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 验证
node --version   # 应显示 v20.x.x
npm --version
```

### 3.4 安装 Nginx

```bash
sudo apt install -y nginx

# 启动并设置开机自启
sudo systemctl start nginx
sudo systemctl enable nginx

# 验证（浏览器访问服务器IP应能看到Nginx欢迎页）2
```

### 3.5 安装 PM2（进程管理）

```bash
sudo npm install -g pm2
```

### 3.6 安装 Certbot（可选，用于HTTPS）

```bash
sudo apt install -y certbot python3-certbot-nginx
```

---

## 四、部署后端 (FastAPI)

### 4.1 上传代码

```bash
# 创建项目目录
sudo mkdir -p /var/www/smart-dining
sudo chown -R deploy:deploy /var/www/smart-dining

# 方式1：使用 scp 上传（在本地执行）
scp -r smart-dining-backend deploy@服务器IP:/var/www/smart-dining/
scp -r smart-dining-backend deploy@172.23.110.175:/var/www/smart-dining/

# 方式2：使用 git clone（如果代码在Git仓库）
cd /var/www/smart-dining
git clone 你的仓库地址 smart-dining-backend
```

### 4.2 创建虚拟环境

```bash
cd /var/www/smart-dining/smart-dining-backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 安装生产服务器
pip install gunicorn uvicorn[standard]
```

### 4.3 测试后端

```bash
# 激活虚拟环境后测试
uvicorn main:app --host 0.0.0.0 --port 8000

# 访问 http://服务器IP:8000/docs 验证API正常
# Ctrl+C 停止
```

### 4.4 配置 Systemd 服务

```bash
sudo vim /etc/systemd/system/smart-dining-api.service
```

写入以下内容：

```ini
[Unit]
Description=Smart Dining API Server
After=network.target

[Service]
Type=simple
User=deploy
Group=deploy
WorkingDirectory=/var/www/smart-dining/smart-dining-backend
Environment="PATH=/var/www/smart-dining/smart-dining-backend/venv/bin"
ExecStart=/var/www/smart-dining/smart-dining-backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start smart-dining-api
sudo systemctl enable smart-dining-api

# 检查状态
sudo systemctl status smart-dining-api
```

---

## 五、部署前端 (Vue 3)

### 5.1 上传代码

```bash
# 上传到服务器（在本地执行）
scp -r smart-dining-frontend deploy@服务器IP:/var/www/smart-dining/
```

### 5.2 构建生产版本

```bash
cd /var/www/smart-dining/smart-dining-frontend

# 安装依赖
npm install

# 修改API地址（如果需要）
# 编辑 vite.config.js 中的 proxy 配置，或创建 .env.production 文件

# 构建
npm run build
```

构建完成后，静态文件在 `dist` 目录中。

---

## 六、配置 Nginx

### 6.1 创建站点配置

```bash
sudo vim /etc/nginx/sites-available/smart-dining
```

写入以下配置（替换 `your-domain.com` 为你的域名，如果没有域名可以先用IP）：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或服务器IP
    
    # 前端静态文件
    root /var/www/smart-dining/smart-dining-frontend/dist;
    index index.html;
    
    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
    
    # 前端路由（SPA）
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 文件上传大小限制（用于图片识别）
        client_max_body_size 10M;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 6.2 启用站点

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/smart-dining /etc/nginx/sites-enabled/

# 删除默认站点（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

---

## 七、配置 HTTPS（推荐）

如果你有域名，强烈建议配置HTTPS：

```bash
# 申请证书（替换为你的域名和邮箱）
sudo certbot --nginx -d your-domain.com -m your-email@example.com --agree-tos

# 自动续期测试
sudo certbot renew --dry-run
```

Certbot 会自动修改 Nginx 配置添加 SSL 相关设置。

---

## 八、防火墙配置

```bash
# 允许必要端口
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

---

## 九、服务管理命令

```bash
# 后端服务
sudo systemctl start smart-dining-api    # 启动
sudo systemctl stop smart-dining-api     # 停止
sudo systemctl restart smart-dining-api  # 重启
sudo systemctl status smart-dining-api   # 状态
journalctl -u smart-dining-api -f        # 查看日志

# Nginx
sudo systemctl reload nginx              # 重载配置
sudo nginx -t                            # 测试配置

# 查看服务器资源
htop
```

---

## 十、YOLOv13 模型部署（GPU服务器）

如果使用GPU服务器运行YOLOv13：

```bash
# 1. 安装 CUDA（阿里云GPU实例通常预装）
nvidia-smi  # 验证GPU驱动

# 2. 安装 PyTorch（GPU版本）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 3. 安装 Ultralytics
pip install ultralytics

# 4. 上传模型文件到服务器
scp your_model.pt deploy@服务器IP:/var/www/smart-dining/smart-dining-backend/models/

# 5. 修改 yolo_service.py 中的 MODEL_PATH
# 6. 重启后端服务
sudo systemctl restart smart-dining-api
```

---

## 十一、常见问题

### Q: 502 Bad Gateway
```bash
# 检查后端服务是否正常运行
sudo systemctl status smart-dining-api
journalctl -u smart-dining-api -n 50
```

### Q: 摄像头无法使用
- 摄像头需要 HTTPS 环境
- 确保已配置SSL证书

### Q: 静态文件404
```bash
# 检查文件权限
sudo chown -R www-data:www-data /var/www/smart-dining/smart-dining-frontend/dist
```

---

## 部署检查清单

- [ ] 服务器已购买并初始化
- [ ] Python 3.11 已安装
- [ ] Node.js 20 已安装
- [ ] Nginx 已安装并运行
- [ ] 后端服务正常运行
- [ ] 前端已构建并部署
- [ ] Nginx 配置已完成
- [ ] HTTPS 已配置（如有域名）
- [ ] 防火墙已配置
- [ ] 访问网站功能正常
