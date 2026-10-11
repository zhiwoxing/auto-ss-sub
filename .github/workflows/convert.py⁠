import base64
import urllib.parse
import os

# 补全 base64 可能缺失的等号 padding
def decode_base64(s):
    return base64.b64decode(s + '=' * (-len(s) % 4)).decode('utf-8')

# 国家 Emoji 映射表
emoji_map = {
    "美国": "🇺🇸", "US": "🇺🇸", "South Africa": "🇿🇦",
    "加拿大": "🇨🇦", "新加坡": "🇸🇬", "日本": "🇯🇵",
    "香港": "🇭🇰", "台湾": "🇨🇳", "法国": "🇫🇷",
    "泰国": "🇹🇭", "澳大利亚": "🇦🇺", "意大利": "🇮🇹",
    "英国": "🇬🇧", "西班牙": "🇪🇸", "俄罗斯": "🇷🇺",
    "Finland": "🇫🇮"
}

def get_emoji(name):
    for key, value in emoji_map.items():
        if key in name or key.lower() in name.lower():
            return value + " "
    return ""

def main():
    # 直接读取未经二次 Base64 编码的 raw.txt
    if not os.path.exists("raw.txt"):
        print("raw.txt not found!")
        return

    with open("raw.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    surge_lines = []
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

            # 1. 解码节点名称并匹配 Emoji
            name = urllib.parse.unquote(name_url)
            emoji = get_emoji(name)

            # 2. 解码节点配置信息
            decoded_config = decode_base64(base64_str)
            
            # 分离加密/密码 和 IP/端口 (格式: method:password@ip:port)
            method_pass, ip_port = decoded_config.split("@")
            method, password = method_pass.split(":", 1)
            ip, port = ip_port.split(":")

            # 3. 组合为 Surge 格式
            surge_node = f"{emoji}{name} = ss, {ip}, {port}, encrypt-method={method}, password={password}, tfo=false, udp-relay=false"
            surge_lines.append(surge_node)
        except Exception as e:
            print(f"解析出错跳过该行: {line}\n错误: {e}")

    # 将结果写入你要求的 surge_sub.txt
    with open("surge_sub.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(surge_lines))
    print(f"转换完成，共生成 {len(surge_lines)} 个 Surge 节点。")

if __name__ == "__main__":
    main()
