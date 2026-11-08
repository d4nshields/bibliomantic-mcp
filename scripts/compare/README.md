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

## Judge the generated readings

With `OPENAI_API_KEY` set in your shell and `OPENAI_EVAL_MODEL` set to a
Responses API model that supports Structured Outputs, run:

```bash
python3 "$tooling/scripts/compare/judge_mcp.py" \
  "$out/main-a/capture.json" "$out/candidate/capture.json"
```

Optionally set `OPENAI_JUDGE_MODEL` to use a different model for judging. Pin
model snapshots when comparing across runs. The runner makes six API requests:
two readings and one blinded comparison per case, for a changing and a steady
cast. It selects the creative prompt when available and uses the general
consultation prompt otherwise. The report measures their combined effect with
the packet and server guidance. It includes both generated readings and the
judge's evidence. One sample per condition makes this an advisory check.

### GitHub Actions

Add `OPENAI_API_KEY` as a repository Actions **secret** and
`OPENAI_EVAL_MODEL` as an Actions **variable**. The optional
`OPENAI_JUDGE_MODEL` is also a variable. If storing the key in a named GitHub
Environment, set the judge job's `environment` to that name so the job can
access it.

The PR workflow captures the exact base and head SHAs and checks their cast
invariants. The judge workflow runs from the default branch after a successful
same-repository capture. It reads the capture artifact as JSON and writes its
report to its own Actions run summary. Fork PRs run the capture check only.
Both workflows and the judge script must be on the default branch for the
automatic judge to run. Use the local command to evaluate existing branches
before that happens.
