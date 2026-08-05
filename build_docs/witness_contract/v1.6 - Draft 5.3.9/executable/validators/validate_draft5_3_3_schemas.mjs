#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Ajv2020 from "./vendor/node_modules/ajv/dist/2020.js";
import addFormats from "./vendor/node_modules/ajv-formats/dist/index.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const requested = process.argv[2] === "--phase" ? process.argv[3] : "all";
const accepted = new Set(["all", "json_schemas", "valid_fixtures", "invalid_fixtures"]);
if (!accepted.has(requested)) {
  process.stderr.write(`unknown schema validation phase: ${requested}\n`);
  process.exit(2);
}

const walk = (directory) => fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
  const full = path.join(directory, entry.name);
  return entry.isDirectory() ? walk(full) : [full];
});

const report = {
  phase: requested,
  status: "failed",
  schemas_compiled: 0,
  valid_fixtures_passed: 0,
  invalid_fixtures_rejected: 0,
  errors: [],
  dependency_mode: "corpus_vendored"
};

try {
  const ajv = new Ajv2020({ allErrors: true, strict: false, validateFormats: true });
  addFormats(ajv);
  const schemaFiles = walk(path.join(root, "schemas")).filter((file) => file.endsWith(".schema.json")).sort();
  for (const file of schemaFiles) {
    const relative = path.relative(root, file).split(path.sep).join("/");
    const schema = JSON.parse(fs.readFileSync(file, "utf8"));
    ajv.addSchema(schema, relative);
    report.schemas_compiled += 1;
  }

  const expectations = requested === "all"
    ? ["valid", "invalid"]
    : requested === "valid_fixtures"
      ? ["valid"]
      : requested === "invalid_fixtures"
        ? ["invalid"]
        : [];

  const fixtureRoot = path.join(root, "executable/tests/fixtures/draft5_3_3");
  for (const expected of expectations) {
    const files = walk(path.join(fixtureRoot, expected)).filter((file) => file.endsWith(".json")).sort();
    if (!files.length) throw new Error(`no ${expected} fixtures found`);
    for (const file of files) {
      const fixture = JSON.parse(fs.readFileSync(file, "utf8"));
      if (!fixture.schema_ref || !("payload" in fixture)) throw new Error(`fixture wrapper missing schema_ref/payload: ${file}`);
      const validate = ajv.getSchema(fixture.schema_ref);
      if (!validate) throw new Error(`fixture references unregistered schema: ${fixture.schema_ref}`);
      const valid = validate(fixture.payload);
      if (expected === "valid" && !valid) {
        report.errors.push(`${path.relative(root, file)} unexpectedly failed: ${ajv.errorsText(validate.errors)}`);
      } else if (expected === "invalid" && valid) {
        report.errors.push(`${path.relative(root, file)} unexpectedly passed`);
      } else if (expected === "valid") {
        report.valid_fixtures_passed += 1;
      } else {
        report.invalid_fixtures_rejected += 1;
      }
    }
  }
  if (!report.errors.length) report.status = "passed";
} catch (error) {
  report.errors.push(String(error && error.stack ? error.stack : error));
}

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
process.exit(report.status === "passed" ? 0 : 1);
