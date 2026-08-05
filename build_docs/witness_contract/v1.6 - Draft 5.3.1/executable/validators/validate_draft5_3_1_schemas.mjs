#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const readJson = (relative) => JSON.parse(fs.readFileSync(path.join(root, relative), "utf8"));
const walk = (directory) => fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
  const full = path.join(directory, entry.name);
  return entry.isDirectory() ? walk(full) : [full];
});

const report = { phase: "json_schemas_and_fixtures", status: "failed", schemas_compiled: 0, valid_fixtures_passed: 0, invalid_fixtures_rejected: 0, errors: [] };
try {
  const ajv = new Ajv2020({ allErrors: true, strict: false, validateFormats: true });
  addFormats(ajv);
  const schemaFiles = walk(path.join(root, "schemas")).filter((file) => file.endsWith(".schema.json")).sort();
  const byRelative = new Map();
  for (const file of schemaFiles) {
    const relative = path.relative(root, file).split(path.sep).join("/");
    const schema = JSON.parse(fs.readFileSync(file, "utf8"));
    ajv.addSchema(schema, relative);
    byRelative.set(relative, schema);
    report.schemas_compiled += 1;
  }

  const fixtureRoot = path.join(root, "executable/tests/fixtures/draft5_3_1");
  for (const expected of ["valid", "invalid"]) {
    const files = walk(path.join(fixtureRoot, expected)).filter((file) => file.endsWith(".json")).sort();
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
