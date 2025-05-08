import dns.resolver
import concurrent.futures
import time
import sys
import ipaddress
import argparse
import requests
from urllib.parse import urlparse

def is_valid_ip(ip_str):
    """验证是否为合法IP地址"""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def is_valid_doh_url(url):
    """验证是否为有效的DoH URL（宽松模式）"""
    try:
        result = urlparse(url)
        return all([result.scheme == 'https',
                   result.netloc])  # 移除路径检查
    except:
        return False

def test_doh(server, domain, timeout):
    """增强版DoH测试，支持多种API格式"""
    params = {
        'name': domain,
        'type': 'A'
    }
    headers = {
        'accept': 'application/dns-json'
    }
    
    try:
        start = time.perf_counter()
        response = requests.get(
            server,
            params=params,
            headers=headers,
            timeout=timeout
        )
        end = time.perf_counter()
        
        if response.status_code == 200:
            data = response.json()
            # 兼容不同响应格式
            answers = data.get('Answer') or data.get('answers') or []
            if any(answer.get('data') for answer in answers):
                return server, round((end - start)*1000, 2), True
        return server, float('inf'), False
    except Exception as e:
        return server, float('inf'), False

def is_valid_domain(domain):
    """基本域名格式验证"""
    if len(domain) > 253:
        return False
    labels = domain.split('.')
    if len(labels) < 2:
        return False
    return all(label.isalnum() or label.startswith('-') or label.endswith('-') for label in labels)

def load_dns_servers(file_path):
    """从文件加载DNS服务器列表（增强版）"""
    servers = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                # 分割行内容（去除行内注释）
                cleaned_line = line.split('#')[0].strip()
                if not cleaned_line:
                    continue
                
                # 验证IP或DoH URL
                if is_valid_ip(cleaned_line) or is_valid_doh_url(cleaned_line):
                    servers.append(cleaned_line)
                else:
                    print(f"⚠️ 忽略无效条目: {cleaned_line}")
        return list(set(servers))
    except Exception as e:
        print(f"❌ 文件读取失败: {str(e)}")
        sys.exit(1)

def test_standard_dns(server, domain, timeout):
    """测试传统DNS服务器"""
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [server]
    resolver.lifetime = timeout
    
    try:
        start = time.perf_counter()
        answer = resolver.resolve(domain, 'A')
        end = time.perf_counter()
        return server, round((end - start)*1000, 2), True
    except Exception:
        return server, float('inf'), False

def test_doh(server, domain, timeout):
    """测试DNS-over-HTTPS服务器"""
    params = {
        'name': domain,
        'type': 'A'
    }
    headers = {
        'accept': 'application/dns-json'
    }
    
    try:
        start = time.perf_counter()
        response = requests.get(
            server,
            params=params,
            headers=headers,
            timeout=timeout
        )
        end = time.perf_counter()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('Answer'):
                return server, round((end - start)*1000, 2), True
        return server, float('inf'), False
    except Exception:
        return server, float('inf'), False

def test_dns(server, domain, timeout):
    """智能路由测试函数"""
    if server.startswith('https://'):
        return test_doh(server, domain, timeout)
    else:
        return test_standard_dns(server, domain, timeout)

def main():
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='DNS服务器性能测试工具')
    parser.add_argument('--domain', '-d', type=str, default='baidu.com',
                      help='指定测试域名（默认：baidu.com）')
    parser.add_argument('--timeout', '-t', type=int, default=5,
                      help='单次查询超时时间（秒，默认：5）')
    args = parser.parse_args()

    # 域名有效性验证
    if not is_valid_domain(args.domain):
        print(f"❌ 无效域名格式：{args.domain}")
        sys.exit(1)

    # 配置文件路径
    dns_file = "dns_servers.txt"
    max_workers = 20

    print(f"📁 正在加载DNS服务器文件: {dns_file}")
    dns_servers = load_dns_servers(dns_file)
    print(f"✅ 已加载 {len(dns_servers)} 个有效DNS服务器")
    print(f"🔄 测试域名: {args.domain}")
    print(f"⏱ 超时设置: {args.timeout} 秒\n")

    # 多线程并发测试
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(test_dns, s, args.domain, args.timeout) for s in dns_servers]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # 结果处理
    valid_servers = sorted(
        [r for r in results if r[2]], 
        key=lambda x: x[1]  # 按响应时间升序排列
    )
    failed_servers = [r[0] for r in results if not r[2]]

    # 输出结果
    print("\n🏆 可用服务器（响应时间升序）：")
    for i, (server, latency, _) in enumerate(valid_servers, 1):
        print(f"{i:>2}. {server:<45} {latency:>6} ms")

    if failed_servers:
        print("\n❌ 不可用服务器：")
        print(", ".join(failed_servers))

if __name__ == "__main__":
    main()
