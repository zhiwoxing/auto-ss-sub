import base64
import urllib.parse
import os

def decode_base64(s):
    return base64.b64decode(s + '=' * (-len(s) % 4)).decode('utf-8')

# 国家 Emoji 映射 (供 Surge 使用)
emoji_map = {
    "美国": "🇺🇸", "US": "🇺🇸", "South Africa": "🇿🇦",
    "加拿大": "🇨🇦", "新加坡": "🇸🇬", "日本": "🇯🇵",
    "香港": "🇭🇰", "台湾": "🇨🇳", "法国": "🇫🇷",
    "泰国": "🇹🇭", "澳大利亚": "🇦🇺", "意大利": "🇮🇹",
    "英国": "🇬🇧", "西班牙": "🇪🇸", "俄罗斯": "🇷🇺",
    "Finland": "🇫🇮", "韩国": "🇰🇷"
}

def get_emoji(name):
    for key, value in emoji_map.items():
        if key in name or key.lower() in name.lower():
            return value + " "
    return ""

def main():
    if not os.path.exists("raw.txt"):
        print("raw.txt not found!")
        return

    with open("raw.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    surge_lines = []
    clash_proxies = []
    node_names = []
    
    # 地区分组容器 (给 Clash 使用)
    hk_nodes, us_nodes, tw_nodes, sg_nodes, kr_nodes = [], [], [], [], []

    for line in lines:
        line = line.strip()
        if not line.startswith("ss://"):
            continue
            
        try:
            content = line[5:]
            if "#" in content:
                base64_str, name_url = content.split("#", 1)
            else:
                base64_str = content
                name_url = "Unnamed"

            name = urllib.parse.unquote(name_url)
            emoji = get_emoji(name)

            decoded_config = decode_base64(base64_str)
            method_pass, ip_port = decoded_config.split("@")
            method, password = method_pass.split(":", 1)
            ip, port = ip_port.split(":")

            # 1. 生成 Surge 格式
            surge_node = f"{emoji}{name} = ss, {ip}, {port}, encrypt-method={method}, password={password}, tfo=false, udp-relay=false"
            surge_lines.append(surge_node)

            # 2. 收集 Clash 数据
            clash_proxies.append({
                "name": name, "server": ip, "port": port, 
                "cipher": method, "password": password
            })
            node_names.append(name)

            # 3. Clash 地区分类
            name_lower = name.lower()
            if "香港" in name or "hk" in name_lower: hk_nodes.append(name)
            if "美国" in name or "us" in name_lower: us_nodes.append(name)
            if "台湾" in name or "tw" in name_lower: tw_nodes.append(name)
            if "新加坡" in name or "sg" in name_lower or "狮城" in name: sg_nodes.append(name)
            if "韩国" in name or "kr" in name_lower: kr_nodes.append(name)

        except Exception as e:
            print(f"解析出错跳过该行: {line}\n错误: {e}")

    # ================= 写入 Surge 文件 =================
    with open("surge_sub.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(surge_lines))
    print(f"Surge 转换完成，共生成 {len(surge_lines)} 个节点。")

    # ================= 写入 Clash 文件 =================
    yaml_lines = [
        "# Generated locally by Actions for Clash",
        "# Rules: ACL4SSR",
        "mixed-port: 7890",
        "allow-lan: false",
        "mode: rule",
        "log-level: warning",
        "ipv6: true",
        "",
        "dns:",
        "  enable: true",
        "  enhanced-mode: fake-ip",
        "  fake-ip-range: 198.18.0.1/16",
        "  fake-ip-filter:",
        '    - "*.lan"',
        '    - "+.local"',
        '    - "+.msftconnecttest.com"',
        '    - "+.msftncsi.com"',
        "  default-nameserver:",
        "    - 223.5.5.5",
        "    - 119.29.29.29",
        "  proxy-server-nameserver:",
        "    - https://223.5.5.5/dns-query",
        "    - https://doh.pub/dns-query",
        "  nameserver:",
        "    - https://223.5.5.5/dns-query",
        "    - https://doh.pub/dns-query",
        "",
        "proxies:"
    ]

    for p in clash_proxies:
        yaml_lines.append(f'  - name: "{p["name"]}"')
        yaml_lines.append(f'    type: ss')
        yaml_lines.append(f'    server: "{p["server"]}"')
        yaml_lines.append(f'    port: {p["port"]}')
        yaml_lines.append(f'    cipher: "{p["cipher"]}"')
        yaml_lines.append(f'    password: "{p["password"]}"')
        yaml_lines.append(f'    udp: true')

    yaml_lines.append("\nproxy-groups:")

    def add_group(name, type_str, proxies_list, extra_proxies=None, url=None, interval=None, tolerance=None):
        yaml_lines.append(f'  - name: "{name}"')
        yaml_lines.append(f'    type: {type_str}')
        if url: yaml_lines.append(f'    url: "{url}"')
        if interval: yaml_lines.append(f'    interval: {interval}')
        if tolerance: yaml_lines.append(f'    tolerance: {tolerance}')
        yaml_lines.append(f'    proxies:')
        if extra_proxies:
            for ep in extra_proxies: yaml_lines.append(f'      - "{ep}"')
        for p in proxies_list:
            yaml_lines.append(f'      - "{p}"')

    # 生成基础策略组
    add_group("🚀 节点选择", "select", node_names, extra_proxies=["♻️ 自动选择", "DIRECT"])
    add_group("♻️ 自动选择", "url-test", node_names, url="http://www.gstatic.com/generate_204", interval=300, tolerance=50)
    add_group("🌍 国外媒体", "select", node_names, extra_proxies=["🚀 节点选择", "♻️ 自动选择", "🎯 全球直连"])
    add_group("📲 电报信息", "select", node_names, extra_proxies=["🚀 节点选择", "🎯 全球直连"])
    add_group("Ⓜ️ 微软服务", "select", node_names, extra_proxies=["🎯 全球直连", "🚀 节点选择"])
    add_group("🍎 苹果服务", "select", node_names, extra_proxies=["🚀 节点选择", "🎯 全球直连"])
    add_group("📢 谷歌FCM", "select", node_names, extra_proxies=["🚀 节点选择", "🎯 全球直连", "♻️ 自动选择"])
    add_group("🎯 全球直连", "select", ["🚀 节点选择", "♻️ 自动选择"], extra_proxies=["DIRECT"])
    add_group("🛑 全球拦截", "select", ["DIRECT"], extra_proxies=["REJECT"])
    add_group("🍃 应用净化", "select", ["DIRECT"], extra_proxies=["REJECT"])
    add_group("Emby代理", "select", [], extra_proxies=["🚀 节点选择", "🇭🇰 香港节点", "🇺🇸 美国节点", "🇨🇳 台湾节点", "🇸🇬 狮城节点", "🇰🇷 韩国节点"])
    add_group("🐟 漏网之鱼", "select", node_names, extra_proxies=["🚀 节点选择", "🎯 全球直连", "♻️ 自动选择"])

    # 生成地区策略组
    add_group("🇭🇰 香港节点", "url-test", hk_nodes, url="http://www.gstatic.com/generate_204", interval=300, tolerance=50)
    add_group("🇺🇸 美国节点", "url-test", us_nodes, url="http://www.gstatic.com/generate_204", interval=300, tolerance=50)
    add_group("🇨🇳 台湾节点", "url-test", tw_nodes, url="http://www.gstatic.com/generate_204", interval=300, tolerance=50)
    add_group("🇸🇬 狮城节点", "url-test", sg_nodes, url="http://www.gstatic.com/generate_204", interval=300, tolerance=50)
    add_group("🇰🇷 韩国节点", "url-test", kr_nodes, url="http://www.gstatic.com/generate_204", interval=300, tolerance=50)

    # 写入 Clash 配置文件头部和节点
    with open("clash_sub.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(yaml_lines) + "\n\n")

    # 注入 rules.txt 分流规则
    if os.path.exists(".github/rules.txt"):
        with open(".github/rules.txt", "r", encoding="utf-8") as r:
            with open("clash_sub.yaml", "a", encoding="utf-8") as f:
                f.write(r.read())
        print("Clash 转换完成并成功注入规则！")
    else:
        print("警告：未找到 rules.txt，Clash 配置文件将缺少分流规则。")

if __name__ == "__main__":
    main()
