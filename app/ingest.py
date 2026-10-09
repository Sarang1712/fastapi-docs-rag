import io, zipfile, pathlib, urllib.request

URL = "https://github.com/fastapi/fastapi/archive/refs/heads/master.zip"
OUT = pathlib.Path("data/docs")

def download_docs():
    data = urllib.request.urlopen(URL).read()
    n = 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if "/docs/en/docs/" in name and name.endswith(".md"):
                dest = OUT / name.split("/docs/en/docs/")[1]
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(name))
                n += 1
    print(f"saved {n} files to {OUT}")

if __name__ == "__main__":
    download_docs()