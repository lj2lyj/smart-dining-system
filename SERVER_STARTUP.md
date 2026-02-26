# 智慧餐饮结算系统 - 服务器启动指南

## 一、连接服务器

```bash
# 在本地电脑 PowerShell 或 CMD 中执行
ssh root@你的服务器公网IP
# 输入密码后进入服务器
```

---

## 二、启动后端服务

### 方式 A：使用 systemd（推荐 - 生产环境）

#### 1. 创建服务配置文件

```bash
sudo nano /etc/systemd/system/smart-dining-api.service
```

#### 2. 粘贴以下内容（一字不改）

```ini
[Unit]
Description=Smart Dining API Server
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/www/smart-dining/smart-dining-backend
Environment="PATH=/var/www/smart-dining/smart-dining-backend/venv/bin"
ExecStart=/var/www/smart-dining/smart-dining-backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 3. 保存并退出
- `Ctrl+O` → `Enter` 保存
- `Ctrl+X` 退出

#### 4. 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl start smart-dining-api
sudo systemctl enable smart-dining-api  # 设置开机自启
sudo systemctl status smart-dining-api  # 查看状态
```

---

### 方式 B：手动启动（测试用）

```bash
cd /var/www/smart-dining/smart-dining-backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

> 注意：手动启动后终端不能关闭，关闭后服务停止

---

## 三、启动 Nginx（前端服务）

```bash
# 确保 Nginx 正在运行
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
```

---

## 四、验证服务

| 检查项 | 命令 |
|--------|------|
| 后端状态 | `sudo systemctl status smart-dining-api` |
| Nginx 状态 | `sudo systemctl status nginx` |
| 端口监听 | `netstat -tlnp \| grep -E '80\|8000'` |
| 后端日志 | `journalctl -u smart-dining-api -n 50` |

### 浏览器访问测试

| 地址 | 说明 |
|------|------|
| `http://120.26.185.67` | 前端页面 |
| `http://120.26.185.67/api/` | 后端 API |
| `http://120.26.185.67:8000/docs` | API 文档（需开放8000端口）|

---

## 五、常用管理命令

```bash
# 后端服务
sudo systemctl start smart-dining-api    # 启动
sudo systemctl stop smart-dining-api     # 停止
sudo systemctl restart smart-dining-api  # 重启
journalctl -u smart-dining-api -f        # 实时日志

# Nginx
sudo systemctl reload nginx              # 重载配置
sudo nginx -t                            # 测试配置

# 查看资源
htop                                     # 系统资源监控
df -h                                    # 磁盘使用
free -m                                  # 内存使用
```

---

## 六、常见问题

### 问题1：502 Bad Gateway
```bash
# 检查后端是否运行
sudo systemctl status smart-dining-api
journalctl -u smart-dining-api -n 50
```

### 问题2：服务启动失败 (status=217/USER)
```bash
# 用户不存在，修改服务配置使用 root
sudo nano /etc/systemd/system/smart-dining-api.service
# 将 User=deploy 改为 User=root
# 将 Group=deploy 改为 Group=root
sudo systemctl daemon-reload
sudo systemctl restart smart-dining-api
```

### 问题3：端口被占用
```bash
# 查看占用进程
sudo lsof -i :8000
# 杀掉进程
sudo kill -9 进程ID
```

### 问题4：缺少依赖
```bash
cd /var/www/smart-dining/smart-dining-backend
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
sudo systemctl restart smart-dining-api
```

---

## 七、一键重启脚本

创建脚本：
```bash
sudo nano /var/www/smart-dining/restart.sh
```

内容：
```bash
#!/bin/bash
echo "========================================="
echo "  重启智慧餐饮结算系统"
echo "========================================="
sudo systemctl restart smart-dining-api
sudo systemctl reload nginx
echo ""
echo "服务状态："
sudo systemctl status smart-dining-api --no-pager -l
echo ""
echo "重启完成！"
```

设置权限并运行：
```bash
sudo chmod +x /var/www/smart-dining/restart.sh
/var/www/smart-dining/restart.sh
```

---

## 八、完整启动流程总结

```bash
# 1. SSH 连接服务器
ssh root@服务器IP

# 2. 启动后端
sudo systemctl start smart-dining-api

# 3. 启动 Nginx
sudo systemctl start nginx

# 4. 验证
sudo systemctl status smart-dining-api
sudo systemctl status nginx

# 5. 浏览器访问
# http://服务器公网IP
```
