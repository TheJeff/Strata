"""One greedy streaming request against the local Strata server; prints TTFT, decode rate and usage."""
import json
import time
import urllib.request

PROMPT = ("Explain in plain words how a mixture-of-experts language model decides which experts to use for "
          "each token, why that choice has to be made quickly, and what happens when the experts a token needs "
          "are not in memory yet. Keep it short.")

body = json.dumps({
    "model": "qwen3.8-flash-next-iq3_s",
    "messages": [{"role": "user", "content": PROMPT}],
    "max_tokens": 120,
    "temperature": 0,
    "stream": True,
    "stream_options": {"include_usage": True},
}).encode()

req = urllib.request.Request("http://127.0.0.1:8090/v1/chat/completions", data=body,
                             headers={"Content-Type": "application/json"})

start = time.perf_counter()
first = None
chunks = 0
usage = None
text = []
with urllib.request.urlopen(req, timeout=900) as resp:
    for raw in resp:
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            event = json.loads(payload)
        except ValueError:
            continue
        if event.get("usage"):
            usage = event["usage"]
        for choice in event.get("choices") or []:
            delta = choice.get("delta") or {}
            piece = delta.get("content") or delta.get("reasoning_content") or ""
            if piece:
                if first is None:
                    first = time.perf_counter()
                chunks += 1
                text.append(piece)
end = time.perf_counter()

ttft = (first - start) if first else None
gen = (end - first) if first else None
out_tokens = (usage or {}).get("completion_tokens") or chunks
prompt_tokens = (usage or {}).get("prompt_tokens")
print(f"prompt_tokens={prompt_tokens} completion_tokens={out_tokens} chunks={chunks}")
print(f"ttft={ttft:.3f}s  generation={gen:.3f}s")
if gen and out_tokens > 1:
    print(f"decode_rate={(out_tokens - 1) / gen:.1f} tok/s")
if ttft and prompt_tokens:
    print(f"prompt_rate={prompt_tokens / ttft:.1f} tok/s (includes load/first-token latency)")
print("answer_head:", "".join(text)[:200].replace("\n", " "))
