# Compare MCP responses with fixed coins

Run the same capture script from each target checkout. Each checkout uses its own
editable package and locked SDK. The script records the Git SHA, MCP version, and
import path and rejects imports from outside the target checkout. Use clean
checkouts so the SHA identifies the captured code.

```bash
# Set these paths to the tooling, baseline, and candidate checkouts.
capture="$tooling/scripts/compare/capture_mcp.py"
compare="$tooling/scripts/compare/compare_mcp.py"
out="$(mktemp -d)"

(
  set -e
  cd "$baseline"
  uv sync --locked
  env -u PYTHONPATH uv run --locked python "$capture" "$out/main-a"
  env -u PYTHONPATH uv run --locked python "$capture" "$out/main-b"
)
python3 "$compare" "$out/main-a/capture.json" "$out/main-b/capture.json"

(
  set -e
  cd "$candidate"
  uv sync --locked
  env -u PYTHONPATH uv run --locked python "$capture" "$out/candidate"
)
python3 "$compare" "$out/main-a/capture.json" "$out/candidate/capture.json" \
  --expect-reading-improvements
```

Stop on a sync or capture error. Each capture needs a fresh output directory.
Use `capture.json` once the capture command has finished successfully.

The in-memory SDK client exercises tool and prompt discovery, six fixed-coin
casts, hexagram lookup, and method description. The coin override lives in this
script. For a separate stdio smoke test, use Inspector with the target's installed
`bibliomantic-mcp` entry point. Stdio casts use fresh random coins.

Generic mode checks the cast invariants and hexagram lookup. The explicit
reading-improvements profile also checks the enriched source text and creative
prompt. The capture includes tool schemas, method data, prompt texts, and server
instructions for inspection. Text sizes are character counts. These checks
measure server behavior. Host-model interpretation requires a separate evaluation.
