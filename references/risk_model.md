# Risk Model

GitHub Skill Curator treats skill installation as a small supply-chain decision.
The scanner is heuristic: it makes risks visible before installation, but it does
not prove that a third-party skill is safe.

| Level | Signal | Default action |
|---|---|---|
| Critical | Secret exfiltration, credential harvesting, SSH key or browser profile access, destructive commands against `/`, `~`, `$HOME`, or `*` | Reject |
| High | Prompt injection that asks the agent to ignore higher-priority instructions, opaque installers, hidden network fetches, obfuscated execution | Reject unless manually reviewed |
| Medium | Overbroad trigger description, stale repository, whole-repo install when one skill folder is enough, unclear provenance | Warn, quarantine, or require explicit approval |
| Low | Missing examples, weak docs, unclear license, no release notes | Warn |

## Examples

| Pattern | Why it matters |
|---|---|
| `ignore previous instructions` | Attempts to bypass the agent's instruction hierarchy |
| `.env`, `id_rsa`, `OPENAI_API_KEY`, `GITHUB_TOKEN` | May access secrets unrelated to the skill task |
| `rm -rf /`, `rm -rf $HOME` | Destructive behavior outside the selected skill folder |
| `curl ... | sh` | Executes remote code before review |
| `eval`, `base64 -d`, `Invoke-Expression` | Can hide behavior from a quick review |
| `use this skill for all tasks` | Can hijack unrelated agent workflows |

## Review Language

Use precise wording:

- Good: "No high-risk findings in scanned files."
- Good: "Install only after reviewing upstream."
- Avoid: "This third-party skill is safe."

