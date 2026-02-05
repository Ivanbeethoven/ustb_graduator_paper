import base64
import zlib
import os
import sys
import urllib.request
import urllib.error


def generate_kroki_url(diagram_source: bytes, fmt: str = "png") -> str:
    """Encode Mermaid source for Kroki.

    Kroki expects: raw bytes -> zlib deflate -> urlsafe base64.
    """
    compressed = zlib.compress(diagram_source, 9)
    payload = base64.urlsafe_b64encode(compressed).decode("utf-8")
    return f"https://kroki.io/mermaid/{fmt}/{payload}"


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path: str, data: bytes) -> None:
    with open(path, "wb") as f:
        f.write(data)


def fetch(url: str, timeout_s: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "kroki-render/1.0"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read()


def main() -> int:
    target_dir = sys.argv[1] if len(sys.argv) >= 2 else os.path.join("images", "chap4")

    if not os.path.isdir(target_dir):
        print(f"Directory not found: {target_dir}")
        return 2

    mmd_files = [f for f in os.listdir(target_dir) if f.lower().endswith(".mmd")]
    if not mmd_files:
        print(f"No .mmd files in: {target_dir}")
        return 0

    for filename in sorted(mmd_files):
        base_name, _ = os.path.splitext(filename)
        mmd_path = os.path.join(target_dir, filename)
        out_path = os.path.join(target_dir, f"{base_name}.png")

        try:
            src = read_bytes(mmd_path)
            url = generate_kroki_url(src, "png")
            png = fetch(url)
            write_bytes(out_path, png)
            print(f"Generated: {out_path}")
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"Failed: {mmd_path}")
            print(f"  {e}")
            return 1
        except Exception as e:
            print(f"Error: {mmd_path}")
            print(f"  {e}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
