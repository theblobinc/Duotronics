#!/usr/bin/env bash
# Acceptance gate: must exit 0 for the conformance suite to be considered green.
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-.venv/bin/python}"
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"
SCHEMA_VERSION="${DUOTRONIC_SCHEMA_VERSION:-v1.2}"
TARGET_SCHEMA_VERSION="${DUOTRONIC_TARGET_SCHEMA_VERSION:-$SCHEMA_VERSION}"
REPORT_PATH="$(pwd)/conformance_report.json"
PYTEST_STAGE_REPORT="$(pwd)/.pytest-stage-report.json"

cleanup() {
	rm -f "$PYTEST_STAGE_REPORT"
}

trap cleanup EXIT

run_stage() {
	local stage_id="$1"
	local label="$2"
	local kind="$3"
	shift 3

	echo "==> $label"

	local output_file
	local command_string
	local exit_code
	local duration
	local start_seconds
	output_file="$(mktemp)"
	command_string="$(printf '%q ' "$@")"
	start_seconds=$SECONDS

	set +e
	if [[ "$kind" == "pytest" ]]; then
		rm -f "$PYTEST_STAGE_REPORT"
		DUOTRONIC_REPORT_PATH="$PYTEST_STAGE_REPORT" "$@" 2>&1 | tee "$output_file"
		exit_code=${PIPESTATUS[0]}
	else
		"$@" 2>&1 | tee "$output_file"
		exit_code=${PIPESTATUS[0]}
	fi
	set -e

	duration=$((SECONDS - start_seconds))

	local stage_args=(
		add-stage
		--path "$REPORT_PATH"
		--stage-id "$stage_id"
		--label "$label"
		--kind "$kind"
		--exit-code "$exit_code"
		--duration-seconds "$duration"
		--command "${command_string% }"
		--output-file "$output_file"
	)
	if [[ "$kind" == "pytest" && -f "$PYTEST_STAGE_REPORT" ]]; then
		stage_args+=(--pytest-report "$PYTEST_STAGE_REPORT")
	fi
	"$PYTHON" tools/acceptance_report.py "${stage_args[@]}"
	rm -f "$output_file" "$PYTEST_STAGE_REPORT"

	if [[ "$exit_code" -ne 0 ]]; then
		"$PYTHON" tools/acceptance_report.py finalize --path "$REPORT_PATH" --status failed
		return "$exit_code"
	fi
}

"$PYTHON" tools/acceptance_report.py init \
	--path "$REPORT_PATH" \
	--schema-version "$SCHEMA_VERSION" \
	--target-schema-version "$TARGET_SCHEMA_VERSION"

run_stage spec_target "spec target" metadata \
	"$PYTHON" tools/print_spec_target.py \
		--schema-version "$SCHEMA_VERSION" \
		--target-schema-version "$TARGET_SCHEMA_VERSION"

run_stage self_test "reference self-tests" self_test \
	"$PYTHON" tools/run_self_test.py

run_stage fixture_drift "fixture YAML/JSON twin drift check" drift_check \
	"$PYTHON" tools/extract_fixtures.py --check

run_stage normative "normative pytest --strict-markers" pytest \
	"$PYTHON" -m pytest -m normative --strict-markers -q \
		--schema-version "$SCHEMA_VERSION" \
		--target-schema-version "$TARGET_SCHEMA_VERSION"

run_stage meta_runtime "meta-runtime conformance slice" pytest \
	"$PYTHON" -m pytest conformance/test_meta_fixture_runner.py conformance/test_meta_golden_traces.py -m "normative and meta_runtime" --strict-markers -q \
		--schema-version "$SCHEMA_VERSION" \
		--target-schema-version "$TARGET_SCHEMA_VERSION"

run_stage full_suite "full pytest (all markers)" pytest \
	"$PYTHON" -m pytest --strict-markers -q \
		--schema-version "$SCHEMA_VERSION" \
		--target-schema-version "$TARGET_SCHEMA_VERSION"

"$PYTHON" tools/acceptance_report.py finalize --path "$REPORT_PATH" --status passed

echo "==> report artifact"
echo "wrote $REPORT_PATH"

echo "OK: acceptance gate green"
