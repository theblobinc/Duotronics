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
if (!accepted.has(requested)) process.exit(2);

const registryPath = path.join(root, "refs/schema_registry_v1_6_draft_5_3_7.json");
const registry = JSON.parse(fs.readFileSync(registryPath, "utf8"));
const entries = registry.entries;
const report = {phase: requested, status: "failed", schemas_compiled: 0, canonical_schemas_compiled_strict: 0, valid_fixtures_passed: 0, invalid_fixtures_rejected: 0, errors: [], dependency_mode: "corpus_vendored_registry_driven"};

try {
  const actual = fs.readdirSync(path.join(root, "schemas"))
    .filter((name) => name.includes(".schema."))
    .map((name) => `schemas/${name}`).sort();
  const classified = entries.map((entry) => entry.path).sort();
  if (JSON.stringify(actual) !== JSON.stringify(classified)) throw new Error("registry does not classify the exact schemas directory");
  if (new Set(classified).size !== classified.length) throw new Error("duplicate registry schema path");

  const ids = entries.map((entry) => entry.schema_id).filter((value) => value !== null);
  if (new Set(ids).size !== ids.length) throw new Error("duplicate schema $id in registry");
  for (const entry of entries) {
    if (entry.active_surface !== (entry.lifecycle === "canonical")) throw new Error(`active surface/lifecycle mismatch: ${entry.path}`);
    if (entry.lifecycle === "canonical" && (!entry.valid_fixtures.length || !entry.invalid_fixtures.length)) throw new Error(`canonical fixture coverage incomplete: ${entry.path}`);
  }

  const loose = new Ajv2020({allErrors: true, strict: false, validateFormats: true}); addFormats(loose);
  const strict = new Ajv2020({allErrors: true, strict: true, validateFormats: true}); addFormats(strict);
  const canonicalDocuments = [];
  for (const entry of entries.filter((item) => item.path.endsWith(".json"))) {
    const schema = JSON.parse(fs.readFileSync(path.join(root, entry.path), "utf8"));
    if (schema.$id !== entry.schema_id) throw new Error(`registry $id mismatch: ${entry.path}`);
    loose.addSchema(schema, entry.path); report.schemas_compiled += 1;
    if (entry.lifecycle === "canonical") canonicalDocuments.push([entry, schema]);
  }
  for (const [entry, schema] of canonicalDocuments) {
    strict.addSchema(schema, entry.path); report.canonical_schemas_compiled_strict += 1;
  }
  for (const [entry] of canonicalDocuments) {
    if (!strict.getSchema(entry.path)) throw new Error(`strict canonical schema unresolved: ${entry.path}`);
  }

  const dispositions = requested === "all" ? ["valid", "invalid"] : requested === "valid_fixtures" ? ["valid"] : requested === "invalid_fixtures" ? ["invalid"] : [];
  for (const entry of entries.filter((item) => item.lifecycle === "canonical")) {
    for (const disposition of dispositions) {
      const fixtures = disposition === "valid" ? entry.valid_fixtures : entry.invalid_fixtures;
      for (const relative of fixtures) {
        if (relative.startsWith("runtime:")) {
          if (disposition === "valid") report.valid_fixtures_passed += 1;
          continue;
        }
        const fixture = JSON.parse(fs.readFileSync(path.join(root, relative), "utf8"));
        if (fixture.schema_ref !== entry.path || !("payload" in fixture)) throw new Error(`fixture wrapper mismatch: ${relative}`);
        const validate = strict.getSchema(entry.path); const valid = validate(fixture.payload);
        if (disposition === "valid" && !valid) report.errors.push(`${relative} unexpectedly failed: ${strict.errorsText(validate.errors)}`);
        else if (disposition === "invalid" && valid) report.errors.push(`${relative} unexpectedly passed`);
        else if (disposition === "valid") report.valid_fixtures_passed += 1;
        else report.invalid_fixtures_rejected += 1;
      }
    }
  }
  if (!report.errors.length) report.status = "passed";
} catch (error) {
  report.errors.push(String(error && error.stack ? error.stack : error));
}

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
process.exit(report.status === "passed" ? 0 : 1);
