"""A long-prompt prefill measure: ~4K tokens in, 8 tokens out, greedy; prints prompt tokens and prefill rate."""
import json
import time
import urllib.request

sentence = ("The archive keeps a register of every shipment that passed through the northern depot, and each row "
            "records the date, the carrier, the weight and the destination yard. ")
PROMPT = sentence * 120          # roughly 4K tokens

body = json.dumps({
    "model": "qwen3.8-flash-next-iq3_s",
    "messages": [{"role": "user", "content": PROMPT + "\n\nIn one sentence: what does the register record?"}],
    "max_tokens": 8,
    "temperature": 0,
    "stream": True,
    "stream_options": {"include_usage": True},
}).encode()

req = urllib.request.Request("http://127.0.0.1:8090/v1/chat/completions", data=body,
                             headers={"Content-Type": "application/json"})
start = time.perf_counter()
first = None
usage = None
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
            if delta.get("content") or delta.get("reasoning_content"):
                if first is None:
                    first = time.perf_counter()
end = time.perf_counter()
prompt_tokens = (usage or {}).get("prompt_tokens")
ttft = (first - start) if first else None
print(f"prompt_tokens={prompt_tokens} ttft={ttft:.3f}s total={end - start:.3f}s")
if prompt_tokens and ttft:
    print(f"prefill_rate={prompt_tokens / ttft:.0f} tok/s")
