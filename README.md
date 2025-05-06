# DNS服务器性能测试工具

## 工具简介
本工具用于测试多个DNS服务器的响应性能和可用性，支持以下核心功能：
- **多DNS服务器测试**：从文件批量加载DNS服务器列表
- **自定义测试域名**：运行时指定任意可解析域名
- **智能排序**：按响应时间自动升序排列
- **多线程检测**：快速完成大规模服务器测试
- **兼容性保障**：支持Windows/Linux/macOS系统

---

## 环境准备

### 1. 安装Python
- **最低版本要求**：Python 3.8+
- **验证安装**：
  ```bash
  python --version
  ```
### 2. 安装依赖库
  ```bash
  pip install dnspython ipaddress
  ```
### 文件准备
#### DNS服务器列表文件
创建 dns_servers.txt 文件，格式示例：
  ```text
  # 公共DNS服务器列表（支持行内注释）
  8.8.8.8            # Google DNS
  1.1.1.1            # Cloudflare
  114.114.114.114    # 114DNS
  223.5.5.5          # 阿里DNS
  ```

#### 格式要求：
 * 每行一个IP地址（IPv4/IPv6）
 *  允许 # 开头的注释行
 *  支持行内注释（IP地址后的说明）

### 基本用法
```bash
python dns_check.py
```
* 默认测试域名：baidu.com
* 默认超时时间：5秒

#### 高级参数
```text
--domain	-d	指定测试域名	google.com
--timeout	-t	设置查询超时时间（秒）	3
```
#### 示例：
```
# 测试google.com域名，超时3秒
python dns_check.py -d google.com -t 3
```
### 成功输出示例
```
📁 正在加载DNS服务器文件: dns_servers.txt
✅ 已加载 4 个有效DNS服务器
🔄 测试域名: google.com
⏱ 超时设置: 3 秒

🏆 可用服务器（响应时间升序）：
 1. 8.8.8.8          32.15 ms
 2. 1.1.1.1          45.67 ms
 3. 223.5.5.5        78.23 ms
 4. 114.114.114.114  102.56 ms

❌ 不可用服务器：
9.9.9.9, 208.67.222.222
```
