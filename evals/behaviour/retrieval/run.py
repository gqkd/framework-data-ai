#!/usr/bin/env python3
"""Opt-in synthetic A/B capture: prepare by default, preflight without a model, execute explicitly."""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dataset = load("retrieval_run_prepare", HERE / "prepare.py")
capture = load("retrieval_run_capture", HERE.parent / "memory/qualify.py")
metrics = load("retrieval_run_metrics", HERE / "metrics.py")
save, digest = dataset.save, dataset.digest
DISABLED = (*capture.DISABLED, "browser_use_external", "in_app_browser", "remote_plugin",
            "external_agent_memory_import", "workspace_dependencies", "tool_suggest",
            "goals", "code_mode", "code_mode_only", "view_image")
REQUIRED_FEATURES = ("code_mode_host", "shell_tool", "unified_exec")
PROFILE = "retrieval-eval"
MODE = "instrumented-source-retrieval-v1"
ADAPTER_PROMPT = """

Protocollo comune di osservazione:
- Per leggere documenti, regole e codice originali usa {python} ../tools/read_source.py
  project PERCORSO_RELATIVO (oppure framework PERCORSO_RELATIVO).
  Parti dalla pagina 1; se serve continua con --start N indicato da next_line.
  Una pagina per comando, senza pipe, riassunti o tagli dell'output.
  Sei tu a scegliere le fonti: il lettore non suggerisce documenti né risposte.
- Ricerca testuale, elenchi, Git e comandi del framework restano disponibili.
  Le letture non strumentate rimangono nel log ma non ricevono credito automatico.
- Fonti e framework sono in sola lettura. L'unico spazio scrivibile è ../scratch.
  Usa le modalità senza pubblicazione (--dry-run, quando disponibile) per i derivati
  e redirigi eventuali output in ../scratch. Non aggiungere mapping o metadati alle fonti.
- Per gli script Python del framework usa {python}; le dipendenze sono già disponibili.
  Non installare provider. Le capacità non disponibili vanno dichiarate tali.
- AGENTS.md non è precaricato automaticamente: leggilo ora con il lettore.
"""


def absent_output(output, source):
    if not output.is_absolute() or output.resolve() != output or output.exists() or output.is_symlink() or any(
            p.is_symlink() for p in output.parents):
        raise ValueError("output must be an absent absolute directory without symlink parents")
    if output.is_relative_to(source) or source.is_relative_to(output) or any(
            (p / ".git").exists() for p in output.parents):
        raise ValueError("output must be separate from prepared inputs and repository checkouts")


def selection(schedule, questions, repetitions, max_trials, pair_order="scheduled"):
    if pair_order not in ("scheduled", "AB", "BA"):
        raise ValueError("pair order must be scheduled, AB or BA")
    if not questions or len(set(questions)) != len(questions) or not 1 <= repetitions <= 3:
        raise ValueError("select distinct question IDs and one to three repetitions")
    if set(questions) - {row["question"] for row in schedule}:
        raise ValueError("unknown question")
    rows = [dict(row) for row in schedule if row["question"] in questions and
            row["repetition"] <= repetitions]
    if len(rows) != len(questions) * repetitions * 2 or not 1 <= len(rows) <= max_trials:
        raise ValueError("paired selection exceeds explicit --max-trials (default 6)")
    if pair_order != "scheduled":
        pairs = {}
        for row in rows:
            pairs.setdefault((row["question"], row["repetition"]), []).append(row)
        rows = [row for pair in pairs.values() for arm in pair_order
                for row in pair if row["arm"] == arm]
    for row in rows:
        row["id"] = f'{row["question"]}-{row["repetition"]}-{row["arm"]}'
    return rows


def review_attestation(path, oracle_bytes, selected_questions, prepared_manifest_sha256):
    if path is None:
        raise ValueError("--execute requires an independent human oracle-review JSON")
    review = json.loads(path.read_bytes())
    if not isinstance(review, dict) or review.get("status") != "independently-reviewed" or (
            review.get("oracle_sha256") != digest(oracle_bytes) or
            review.get("prepared_manifest_sha256") != prepared_manifest_sha256 or
            review.get("independent_of_dataset_author") is not True or
            not isinstance(review.get("reviewer"), str) or not review["reviewer"].strip()):
        raise ValueError("missing or mismatched independent review attestation")
    covered = review.get("reviewed_questions")
    known = set(json.loads(oracle_bytes)["cases"])
    if not isinstance(covered, list) or not covered or any(type(q) is not str for q in covered):
        raise ValueError("review must explicitly name the reviewed questions")
    if len(covered) != len(set(covered)) or set(covered) - known or (
            not selected_questions or not set(selected_questions) <= set(covered)):
        raise ValueError("independent review does not cover the selected questions")
    datetime.date.fromisoformat(review.get("reviewed_on", ""))
    return review


def review_material(output, selected):
    """Evaluator-only packets of original source text; never an approval or a model answer."""
    evaluator = output / "evaluator"
    oracle = json.loads((evaluator / "oracle.json").read_bytes())
    questions = {q["id"]: q for q in json.loads((evaluator / "questions.json").read_bytes())["questions"]}
    requirements = json.loads((evaluator / "source-requirements.json").read_bytes())
    directory = evaluator / "review"
    directory.mkdir()
    index = ["# Revisione delle rubriche selezionate", "",
             "Stato: da revisionare da parte di una persona diversa dall'autore del dataset.",
             "La generazione delle schede non approva i criteri e non esegue il modello.", ""]
    for identifier in sorted({row["question"] for row in selected}):
        row = next(r for r in selected if r["question"] == identifier)
        project = output / "trials" / row["id"] / "project"
        case = oracle["cases"][identifier]
        lines = [f"# {identifier} — revisione della risposta attesa", "",
                 f"Split: {questions[identifier]['split']}. Materiale riservato al valutatore.", "",
                 "## Domanda esatta", "", questions[identifier]["prompt"], "",
                 "## Criteri semantici originali", "",
                 "Da verificare per significato; non sono stringhe da cercare nella risposta.", "",
                 "La risposta deve includere:", "",
                 *("- " + c for c in case["must_include"]), "",
                 "La risposta non deve affermare:", "",
                 *("- " + c for c in case["must_not"]), "",
                 "## Requisiti di retrieval", "",
                 "Tutti i gruppi sono richiesti; dentro un gruppo basta una delle alternative.", ""]
        for number, group in enumerate(case["sources"], 1):
            lines.append(f"- Gruppo {number}: " + " oppure ".join(group))
        for key in ("observations", "absences"):
            if case.get(key):
                lines.extend(["", f"Ulteriori controlli ({key}):", "",
                              *("- " + item for item in case[key])])
        lines.extend(["", "## Fonti originali integrali", "",
                      "I numeri di riga sono aggiunti per la revisione; gli hash si riferiscono ai file originali."])
        for source in sorted({s for group in case["sources"] for s in group}):
            requirement = requirements[source]
            content = metrics.reader.source_path(project, requirement["path"]).read_bytes()
            if digest(content) != requirement["file_sha256"]:
                raise ValueError("review source differs from the authored requirement")
            text = content.decode("utf-8")
            fence = "~" * max(3, 1 + max((len(m[0]) for m in re.finditer(r"~+", text)), default=0))
            spans = ", ".join(f'{s["start_line"]}–{s["end_line"]}' for s in requirement["required_spans"])
            lines.extend(["", f"### {source}: {requirement['path']}", "",
                          f"SHA-256: {requirement['file_sha256']}", "",
                          "Righe obbligatorie per il retrieval: " + spans, "", fence + "text",
                          "".join(f"{n:04d} | {line}" for n, line in enumerate(text.splitlines(keepends=True), 1)).rstrip("\n"),
                          fence])
        lines.extend(["", "## Esito della revisione umana", "",
                      "- [ ] I criteri sono sostenuti dalle fonti e rispondono alla domanda.",
                      "- [ ] I gruppi e le sezioni richiesti per il retrieval sono appropriati.",
                      "- [ ] Ho segnalato ambiguità o correzioni prima dell'esecuzione.",
                      "", "Questa scheda non è un'approvazione. L'attestazione deve nominare solo i casi",
                      "effettivamente revisionati e gli hash della preparazione e dell'oracle.",
                      "La scheda è uno snapshot: registra l'esito nella copia di",
                      "oracle-review.template.json, senza modificare questa scheda.", ""])
        (directory / f"{identifier}.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
        index.append(f"- [{identifier}]({identifier}.md) — {questions[identifier]['prompt']}")
    (directory / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8", newline="\n")


def prepare_run(source, output, questions, repetitions=1, max_trials=6, pair_order="scheduled"):
    source, output = Path(source), Path(output)
    if not source.is_absolute() or source.resolve() != source or source.is_symlink() or any(p.is_symlink() for p in source.parents):
        raise ValueError("prepared input must be an absolute non-symlink directory")
    absent_output(output, source)
    original = json.loads((source / "evaluator/manifest.json").read_bytes())
    if original.get("schema") != "framework/synthetic-retrieval-preparation/v1":
        raise ValueError("not a synthetic retrieval preparation")
    # Reconstruct from the authored fiction and exact LOCAL Git objects. Never trust
    # a caller-editable manifest/oracle alone, and never copy caller-provided .git files.
    with tempfile.TemporaryDirectory(prefix="retrieval-verify-") as temp:
        expected = Path(temp) / "expected"
        dataset.prepare(expected, original["versions"]["A"]["commit"], original["versions"]["B"]["commit"])
        if dataset.inventory(source) != dataset.inventory(expected):
            raise ValueError("prepared bytes differ from reproducible authored inputs; prepare anew")
        evaluator = expected / "evaluator"
        schedule = json.loads((evaluator / "schedule.json").read_bytes())
        selected = selection(schedule, questions, repetitions, max_trials, pair_order)
        output.mkdir(parents=True, exist_ok=False)
        shutil.copytree(evaluator, output / "evaluator")
        for row in selected:
            trial = output / "trials" / row["id"]
            for scope in ("project", "framework"):
                shutil.copytree(expected / "arms" / row["arm"] / scope, trial / scope)
            (trial / "tools").mkdir()
            shutil.copyfile(HERE / "read_source.py", trial / "tools/read_source.py")
            (trial / "scratch").mkdir()
            prompt = (evaluator / "prompts" / (row["question"] + ".txt")).read_text()
            prompt += ADAPTER_PROMPT.format(python=shlex.quote(sys.executable))
            (trial / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
            save(trial / "before.json", {scope: capture.inventory(trial / scope)
                                       for scope in ("project", "framework", "tools")})
            save(trial / "result.json", dict(row, status="not-run"))
        inputs = [HERE / name for name in ("run.py", "metrics.py", "read_source.py", "prepare.py")]
        inputs += [HERE.parent / "memory/qualify.py"]
        review_material(output, selected)
        prepared_hash = digest((source / "evaluator/manifest.json").read_bytes())
        save(output / "run.json", {
            "schema": "framework/synthetic-retrieval-run/v1", "mode": MODE, "selected": selected,
            "pair_order": pair_order,
            "prepared_manifest_sha256": prepared_hash,
            "evaluator_hashes": {p: info["sha256"] for p, info in dataset.inventory(output / "evaluator").items()},
            "runner_inputs": {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in inputs},
            "python": sys.version, "python_executable": sys.executable,
            "prompt_hashes": {r["id"]: digest((output / "trials" / r["id"] / "prompt.txt").read_bytes())
                              for r in selected},
            "model_invocations_attempted": 0, "status": "prepared-not-executed",
            "precomputed_context": False, "grading": "independent-review-required"})
        save(output / "oracle-review.template.json", {
            "status": "pending-independent-human-review", "reviewer": "",
            "reviewed_on": "", "independent_of_dataset_author": False,
            "reviewed_questions": sorted({r["question"] for r in selected}),
            "prepared_manifest_sha256": prepared_hash,
            "oracle_sha256": digest((evaluator / "oracle.json").read_bytes())})
    return selected


def toml_map(values):
    return "{" + ",".join(json.dumps(k) + "=" + json.dumps(v) for k, v in values.items()) + "}"


def feature_options():
    # code_mode_host is tool infrastructure in CLI 0.150.1, not an optional
    # integration. Disabling it leaves declared tools unusable even with a sound OS sandbox.
    return [p for feature in DISABLED for p in ("--disable", feature)] + [
        p for feature in REQUIRED_FEATURES for p in ("--enable", feature)]


def feature_status(text):
    states = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[-1] in ("true", "false"):
            states[parts[0]] = parts[-1] == "true"
    expected = {**{name: False for name in DISABLED}, **{name: True for name in REQUIRED_FEATURES}}
    observed = {name: states.get(name) for name in expected}
    return {"status": "passed" if observed == expected else "unavailable", "observed": observed,
            "scope": "effective feature switches; does not attest a live model tool call"}


def settings(trial, helper=None, disabled_skills=()):
    filesystem = {":minimal": "read", str(trial / "project"): "read",
                  str(trial / "framework"): "read", str(trial / "tools"): "read",
                  str(trial / "scratch"): "write"}
    # Existing interpreter/dependencies only, not a broad /tmp grant.
    if Path(sys.prefix) not in (Path("/usr"), Path("/usr/local")):
        if not (Path(sys.prefix) / "pyvenv.cfg").is_file():
            raise ValueError("nonstandard Python runtime must be an existing virtual environment")
        if trial.is_relative_to(Path(sys.prefix)):
            raise ValueError("trial must not live inside the readable Python environment")
        filesystem[str(Path(sys.prefix))] = "read"
    if helper is not None:
        if not helper.is_file():
            raise ValueError("native sandbox helper is unavailable")
        filesystem[str(helper.resolve())] = "read"
    environment = {"PATH": str(Path(sys.executable).parent) + ":/usr/bin:/bin",
                   "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
                   "GIT_OPTIONAL_LOCKS": "0", "GIT_CONFIG_NOSYSTEM": "1",
                   "GIT_CONFIG_GLOBAL": "/dev/null", "TMPDIR": str(trial / "scratch"),
                   "LC_ALL": "C.UTF-8"}
    return ['approval_policy="never"', 'default_permissions="' + PROFILE + '"',
            f"permissions.{PROFILE}.filesystem=" + toml_map(filesystem),
            f"permissions.{PROFILE}.network.enabled=false", 'web_search="disabled"',
            "project_doc_max_bytes=0", 'project_root_markers=["AGENTS.md"]',
            "mcp_servers={}", "tool_output_token_limit=10000", 'shell_environment_policy.inherit="none"',
            "shell_environment_policy.ignore_default_excludes=false",
            "shell_environment_policy.experimental_use_profile=false",
            "shell_environment_policy.set=" + toml_map(environment),
            "skills.config=[" + ",".join('{path=' + json.dumps(p) + ',enabled=false}'
                                         for p in disabled_skills) + "]"]


def skill_paths():
    """Enumerate directory names only; disable discovered global/system skill catalogs.

    Do not read personal SKILL contents. Symlink cycles / excessive discovery fail closed.
    The pinned CLI's bundled defaults/managed policy still require pilot inspection.
    """
    cli_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    roots = (Path.home() / ".agents/skills", cli_home / "skills", Path("/etc/codex/skills"))
    result, visited = set(), set()
    pending = [p for p in roots if p.is_dir()]
    while pending:
        path = pending.pop()
        if (path / "SKILL.md").is_file():
            result.update((str(path), str(path.resolve())))
        resolved = path.resolve()
        if resolved in visited:
            continue
        visited.add(resolved)
        if len(visited) > 4096:
            raise ValueError("unbounded global skill discovery; use a controlled CLI installation")
        pending.extend(p for p in path.iterdir() if p.is_dir())
    return sorted(result)


PROBE = """
import json, pathlib, socket, subprocess, sys
import yaml, jsonschema
trial, outside, sibling = map(pathlib.Path, sys.argv[1:])
result = {"source_read": bool((trial/"project/AGENTS.md").read_bytes()),
          "runtime_read": bool((trial/"framework/FRAMEWORK.md").read_bytes()),
          "dependencies": True}
for name, action in [
    ("source_write", lambda: (trial/"project/.probe-write").write_text("probe")),
    ("runtime_write", lambda: (trial/"framework/.probe-write").write_text("probe")),
    ("outside_read", lambda: outside.read_bytes()),
    ("sibling_read", lambda: sibling.read_bytes()),
    ("network", lambda: socket.socket().connect(("127.0.0.1", 9)))]:
    try:
        action()
        result[name] = "allowed"
    except OSError as error:
        denied = error.errno in (1, 13, 30) or (name.endswith("_read") and error.errno == 2)
        result[name] = "denied" if denied else "unproven"
probe = trial/"scratch/probe.txt"
probe.write_text("synthetic scratch")
result["scratch_write"] = probe.read_text() == "synthetic scratch"
probe.unlink()
read = subprocess.run([sys.executable, "-B", str(trial/"tools/read_source.py"),
                       "project", "AGENTS.md"], capture_output=True, text=True)
result["reader"] = read.returncode == 0 and "<<<end-retrieval-source-v1>>>" in read.stdout
entry = trial/"framework/memory.py"
if not entry.is_file():
    entry = trial/"framework/skills/audit/scripts/validate.py"
check = subprocess.run([sys.executable, "-B", str(entry), "--help"], capture_output=True)
result["framework_cli"] = check.returncode == 0
print(json.dumps(result))
"""


def preflight(codex, trial, output, sibling, helper=None):
    # features list is read-only and does not invoke a model. It cannot take
    # --ignore-user-config; every feature checked here is explicitly overridden,
    # identically to model_command. It does not export personal configuration contents.
    feature_command = [codex, "features", "list", *capture.options(settings(trial, helper)),
                       *feature_options()]
    save(trial / "feature-command.json", feature_command)
    feature_process = capture.capture_process(feature_command, cwd=trial / "project",
                                              output=trial, prefix="features", timeout=30)
    feature_check = feature_status((trial / "features.stdout").read_text(encoding="utf-8", errors="replace"))
    if feature_process["status"] != "completed" or feature_check["status"] != "passed":
        result = {"status": "unavailable", "reason": "required-tool-features-not-proven",
                  "feature_check": feature_check, "feature_process": feature_process}
        save(trial / "preflight.json", result)
        return result
    canary = output / "evaluator/canary.txt"
    canary.write_text("Synthetic evaluator canary.\n")
    if not sibling.is_file():
        raise ValueError("sibling canary must exist outside allowed roots")
    command = [codex, "sandbox", *capture.options(settings(trial, helper)),
               "-P", PROFILE, "-C", str(trial / "project"), "--", sys.executable, "-B", "-c",
               PROBE, str(trial), str(canary), str(sibling)]
    save(trial / "preflight-command.json", command)
    result = capture.capture_process(command, cwd=trial / "project", output=trial,
                                     prefix="preflight", timeout=30)
    try:
        observed = json.loads((trial / "preflight.stdout").read_bytes())
    except (ValueError, OSError):
        observed = {}
    expected = {"source_read": True, "runtime_read": True, "dependencies": True,
                "source_write": "denied", "runtime_write": "denied", "outside_read": "denied",
                "sibling_read": "denied", "network": "denied", "scratch_write": True, "reader": True,
                "framework_cli": True}
    result.update(observed=observed, feature_check=feature_check,
                  status="passed" if result["status"] == "completed" and
                  observed == expected else "unavailable")
    save(trial / "preflight.json", result)
    return result


def changes(trial):
    before = json.loads((trial / "before.json").read_bytes())
    return [dict(change, scope=scope) for scope in before for change in
            capture.differences(before[scope], capture.inventory(trial / scope))]


def model_command(codex, trial, model, reasoning, helper, skills):
    return [codex, "exec", "--strict-config", "--ignore-user-config", "--ignore-rules",
            "--ephemeral", "--json", "--skip-git-repo-check", "-C", str(trial / "project"),
            "-m", model, "-c", "model_reasoning_effort=" + json.dumps(reasoning),
            *capture.options(settings(trial, helper, skills)),
            *feature_options(),
            "-o", str(trial / "answer.md"), "-"]


def execute(output, selected, codex, helper=None, *, model=None, reasoning=None,
            timeout=600, preflight_only=False, review=None, expected_cli="0.150.1"):
    if timeout is not None and (type(timeout) is not int or timeout <= 0):
        raise ValueError("timeout must be a positive integer or None for unrestricted duration")
    if sys.platform != "linux":
        raise ValueError("Linux/WSL sandbox required; no weaker fallback")
    state = json.loads((output / "run.json").read_bytes())
    if state.get("status") != "prepared-not-executed" or selected != state["selected"]:
        raise ValueError("execution requires a fresh untouched trial plan; no resume")
    if any(digest((ROOT / path).read_bytes()) != sha for path, sha in state["runner_inputs"].items()):
        raise ValueError("runner changed after preparation")
    if any(digest((output / "trials" / name / "prompt.txt").read_bytes()) != sha
           for name, sha in state["prompt_hashes"].items()):
        raise ValueError("prompt changed after preparation")
    if not state.get("evaluator_hashes") or any(
            digest((output / "evaluator" / path).read_bytes()) != sha
            for path, sha in state["evaluator_hashes"].items()):
        raise ValueError("evaluator inputs changed after preparation; prepare anew")
    oracle_bytes = (output / "evaluator/oracle.json").read_bytes()
    if not preflight_only:
        if not model or not reasoning:
            raise ValueError("explicit identical model and reasoning settings required")
        save(output / "oracle-review.json", review_attestation(
            review, oracle_bytes, {r["question"] for r in selected}, state["prepared_manifest_sha256"]))
    version = subprocess.run([codex, "--version"], capture_output=True, text=True, timeout=30, check=True)
    if version.stdout.strip() != "codex-cli " + expected_cli:
        raise ValueError("CLI version changed; qualify adapter and explicitly choose --expected-cli")
    skills = [] if preflight_only else skill_paths()
    state.update(cli=version.stdout.strip(), requested_model=model, requested_reasoning=reasoning,
                 actual_model_identity=None, timeout_seconds_per_trial=timeout,
                 disabled_skill_paths=skills, status="preflight-running" if preflight_only else "running",
                 command_network=False, inference_network="authenticated CLI; not local inference")
    save(output / "run.json", state)
    oracle = json.loads(oracle_bytes)
    requirements = json.loads((output / "evaluator/source-requirements.json").read_bytes())
    results = []
    for index, row in enumerate(selected):
        trial = output / "trials" / row["id"]
        sibling = output / "trials" / selected[(index + 1) % len(selected)]["id"] / "project/AGENTS.md"
        changed = changes(trial)
        checked = preflight(codex, trial, output, sibling, helper) if not changed else {"status": "unavailable"}
        changed = changes(trial)
        if changed:
            result = {"status": "critical-failure", "reason": "unauthorized-write", "changes": changed}
        elif checked["status"] != "passed":
            result = {"status": "unavailable", "reason": "sandbox-preflight-not-proven"}
        elif preflight_only:
            result = {"status": "preflight-passed", "reason": "no-model-invoked"}
        else:
            command = model_command(codex, trial, model, reasoning, helper, skills)
            save(trial / "command.json", command)
            state["model_invocations_attempted"] += 1
            save(output / "run.json", state)
            process = capture.capture_process(command, cwd=trial / "project", output=trial,
                                              prefix="events", timeout=timeout,
                                              stdin=(trial / "prompt.txt").read_bytes())
            answer_file = trial / "answer.md"
            answer = answer_file.read_text(encoding="utf-8") if answer_file.is_file() else ""
            result = metrics.analyze((trial / "events.stdout").read_text(encoding="utf-8", errors="replace"),
                                     answer, {s: trial / s for s in ("project", "framework")},
                                     oracle["cases"][row["question"]], requirements, process, changes(trial),
                                     stderr=(trial / "events.stderr").read_text(encoding="utf-8", errors="replace"))
            result["model_invocation_attempted"] = True
        result.setdefault("model_invocation_attempted", False)
        result.update({k: row[k] for k in ("id", "question", "arm", "repetition", "split")})
        save(trial / "result.json", result)
        results.append(result)
        save(output / "results.json", {"results": results, "summary": metrics.summarize(results),
             "not_run": [r["id"] for r in selected if r["id"] not in {x["id"] for x in results}]})
        print(row["id"], result["status"], flush=True)
        if result["status"] in ("unavailable", "critical-failure"):
            break
    successful_status = "preflight-passed" if preflight_only else "pending-review"
    success = len(results) == len(selected) and all(r["status"] == successful_status for r in results)
    state["status"] = successful_status if success else "incomplete"
    save(output / "run.json", state)
    return 0 if success else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--question", action="append", required=True)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--max-trials", type=int, default=6)
    parser.add_argument("--pair-order", choices=("scheduled", "AB", "BA"), default="scheduled",
                        help="Explicit pair-order override, recorded separately from the frozen calendar")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--preflight-only", action="store_true")
    modes.add_argument("--execute", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--reasoning", choices=("minimal", "low", "medium", "high", "xhigh"))
    parser.add_argument("--oracle-review", type=Path)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--sandbox-helper", type=Path)
    parser.add_argument("--expected-cli", default="0.150.1")
    duration = parser.add_mutually_exclusive_group()
    duration.add_argument("--timeout", type=int, default=600)
    duration.add_argument("--no-timeout", action="store_true",
                          help="Observe completion without a wall-clock deadline for model trials")
    args = parser.parse_args(argv)
    if args.timeout <= 0 or (args.execute and (not args.model or not args.reasoning or not args.oracle_review)):
        parser.error("positive timeout and, for execution, explicit model, reasoning and oracle review required")
    try:
        selected = prepare_run(args.from_prepared, args.output, args.question,
                               args.repetitions, args.max_trials, args.pair_order)
        if args.execute or args.preflight_only:
            return execute(args.output, selected, args.codex, args.sandbox_helper,
                           model=args.model, reasoning=args.reasoning,
                           timeout=None if args.no_timeout else args.timeout,
                           preflight_only=args.preflight_only, review=args.oracle_review,
                           expected_cli=args.expected_cli)
        print(json.dumps({"status": "prepared-not-executed", "trials": len(selected),
                          "model_invocations_attempted": 0}))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError, KeyError, TypeError) as error:
        parser.exit(1, f"Retrieval run stopped: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
