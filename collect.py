import asyncio, base64, socket, time, urllib.request, re, sys

SOURCES = [
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
]

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.0"})
        return urllib.request.urlopen(req, timeout=10).read().decode(errors="ignore")
    except:
        return ""

def decode_nodes(text):
    decoded = text
    try:
        b = base64.b64decode(text.strip() + "==").decode(errors="ignore")
        if "://" in b:
            decoded = b
    except:
        pass
    return [l.strip() for l in decoded.splitlines() if re.match(r"^(vless|vmess|ss|trojan)://", l.strip())]

def parse_host_port(node):
    try:
        m = re.match(r"^\w+://[^@]*@([^:/?#]+):?(\d+)?", node)
        if m:
            host = m.group(1)
            port = int(m.group(2)) if m.group(2) else 443
            return host, port
    except:
        pass
    return None, None

def tcp_test(host, port, timeout=2):
    try:
        t = time.monotonic()
        s = socket.create_connection((host, port), timeout=timeout)
        ms = int((time.monotonic() - t) * 1000)
        s.close()
        return ms
    except:
        return 9999

all_nodes = set()
for url in SOURCES:
    print(f"Fetching {url}", flush=True)
    nodes = decode_nodes(fetch(url))
    all_nodes.update(nodes)
    print(f"  -> {len(nodes)} nodes", flush=True)

print(f"Total unique: {len(all_nodes)}", flush=True)

# Test up to 500 nodes concurrently using threads
from concurrent.futures import ThreadPoolExecutor, as_completed
nodes = list(all_nodes)[:500]
results = []

def test_node(node):
    host, port = parse_host_port(node)
    if not host:
        return node, 9999
    ms = tcp_test(host, port)
    return node, ms

print(f"Testing {len(nodes)} nodes...", flush=True)
with ThreadPoolExecutor(max_workers=100) as ex:
    futs = {ex.submit(test_node, n): n for n in nodes}
    for f in as_completed(futs):
        results.append(f.result())

results.sort(key=lambda x: x[1])
top50 = [n for n, ms in results[:50] if ms < 9999]
print(f"Top 5 latencies: {[ms for _,ms in results[:5]]}", flush=True)

with open("sub.txt", "w") as f:
    f.write("\n".join(top50) + "\n")
print(f"Written {len(top50)} nodes to sub.txt")
