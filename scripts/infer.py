import os, subprocess, requests

prompt = os.environ["PROMPT"]
rid    = os.environ["REQUEST_ID"]
token  = os.environ["GITHUB_TOKEN"]
repo   = os.environ["REPO"]
issue  = os.environ["ISSUE_NUMBER"]

LLAMA_CLI = "llama/build/bin/llama-cli"
MODEL     = "models/qwen2.5-0.5b-instruct-q4_k_m.gguf"

if not os.path.exists(LLAMA_CLI):
    raise SystemExit(f"llama-cli not found at {LLAMA_CLI}")

full_prompt = (
    "<|im_start|>system\n你是一个简洁的助手，用中文回答。<|im_end|>\n"
    f"<|im_start|>user\n{prompt}<|im_end|>\n"
    "<|im_start|>assistant\n"
)

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = os.path.abspath("llama/build/bin") + ":" + env.get("LD_LIBRARY_PATH", "")

cmd = [
    LLAMA_CLI,
    "-m", MODEL,
    "-p", full_prompt,
    "-n", "512",
    "-t", "2",
    "--no-display-prompt",
    "--temp", "0.7",
    "-no-cnv",
]
print("running:", " ".join(cmd))
result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env)
print("--- stdout ---")
print(result.stdout)
print("--- stderr ---")
print(result.stderr[-1000:])

if result.returncode != 0:
    raise SystemExit(f"llama-cli failed: {result.returncode}")

reply = result.stdout.strip()
reply = reply.replace("<|im_end|>", "").replace("[end of text]", "").strip()
if not reply:
    reply = "[空回复]"

body = f"<!-- request_id:{rid} -->\n{reply}"
r = requests.post(
    f"https://api.github.com/repos/{repo}/issues/{issue}/comments",
    headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    json={"body": body}, timeout=30,
)
r.raise_for_status()
print("comment posted", r.status_code)
