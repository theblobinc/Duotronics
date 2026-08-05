from __future__ import annotations

import re
import time
from typing import Any

from fastapi import HTTPException

from .config import Settings
from .ops_mcp import XaviOpsTools
from .repo_mcp import XaviRepoTools

_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,96}$")
_SAFE_BRANCH = re.compile(r"^[A-Za-z0-9._/-]{1,160}$")


def dev_tool_manifest() -> list[dict[str, Any]]:
    return [
        {
            "name": "dev.concrete_block_scaffold",
            "description": "Generate a read-only Concrete CMS 9 block skeleton as a file map. Does not write files or install the block.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "required": ["handle", "name"],
                "properties": {
                    "handle": {"type": "string", "pattern": "^[a-z][a-z0-9_]{1,63}$"},
                    "name": {"type": "string", "minLength": 1, "maxLength": 120},
                    "description": {"type": "string", "default": ""},
                    "package_namespace": {"type": "string", "default": "Concrete\\Package\\Generated"},
                    "table": {"type": ["string", "null"]},
                    "web_component": {"type": ["string", "null"]},
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "type"],
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string", "enum": ["string", "text", "integer", "boolean", "datetime"]},
                                "size": {"type": "integer", "minimum": 1, "maximum": 65535},
                                "required": {"type": "boolean", "default": False},
                                "default": {}
                            }
                        },
                        "default": []
                    }
                },
                "additionalProperties": False
            }
        },
        {
            "name": "dev.apply_change_bundle",
            "description": (
                "Apply a full development change bundle in one call: create worktree, apply patch, run tests, "
                "commit, integrate into local main, optionally push, report rebuild intent, and clean up."
            ),
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["patch", "message"],
                "properties": {
                    "patch": {"type": "string", "minLength": 1},
                    "message": {"type": "string", "minLength": 1},
                    "branch_name": {"type": ["string", "null"]},
                    "worktree_id": {"type": ["string", "null"]},
                    "base_ref": {"type": "string", "default": "HEAD"},
                    "target_branch": {"type": "string", "default": "main"},
                    "test_command": {"type": "string", "enum": ["runtime_pytest"], "default": "runtime_pytest"},
                    "test_timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 900, "default": 300},
                    "push": {"type": "boolean", "default": False},
                    "rebuild": {"type": "boolean", "default": False, "description": "Request a separate rebuild recommendation. Rebuild is not executed inline."},
                    "rebuild_models": {"type": "boolean", "default": True},
                    "cleanup": {"type": "boolean", "default": True},
                },
            },
        }
    ]


class XaviDevBundleTools:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repo = XaviRepoTools(settings)
        self.ops = XaviOpsTools(settings)

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool == "dev.concrete_block_scaffold":
            return self.concrete_block_scaffold(args)
        if tool != "dev.apply_change_bundle":
            raise HTTPException(status_code=404, detail=f"unknown dev MCP tool: {tool}")
        return await self.apply_change_bundle(args)

    def concrete_block_scaffold(self, args: dict[str, Any]) -> dict[str, Any]:
        handle = str(args.get("handle", "")).strip()
        name = str(args.get("name", "")).strip()
        description = str(args.get("description", "")).strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", handle):
            raise HTTPException(status_code=422, detail="handle must match ^[a-z][a-z0-9_]{1,63}$")
        if not name:
            raise HTTPException(status_code=422, detail="name is required")

        camel = "".join(part.capitalize() for part in handle.split("_"))
        package_namespace = str(args.get("package_namespace") or r"Concrete\Package\Generated").strip().strip("\\")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?:\\[A-Za-z_][A-Za-z0-9_]*)*", package_namespace):
            raise HTTPException(status_code=422, detail="unsafe package_namespace")

        table = str(args.get("table") or f"bt{camel}").strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,63}", table):
            raise HTTPException(status_code=422, detail="unsafe table name")

        component = str(args.get("web_component") or handle.replace("_", "-")).strip().lower()
        if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)+", component):
            raise HTTPException(status_code=422, detail="web_component must be a valid hyphenated custom-element name")

        normalized: list[dict[str, Any]] = []
        for index, field in enumerate(args.get("fields") or []):
            if not isinstance(field, dict):
                raise HTTPException(status_code=422, detail=f"fields[{index}] must be an object")
            field_name = str(field.get("name", "")).strip()
            field_type = str(field.get("type", "string")).strip()
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", field_name):
                raise HTTPException(status_code=422, detail=f"unsafe field name: {field_name}")
            if field_type not in {"string", "text", "integer", "boolean", "datetime"}:
                raise HTTPException(status_code=422, detail=f"unsupported field type: {field_type}")
            normalized.append({
                "name": field_name,
                "type": field_type,
                "size": max(1, min(int(field.get("size", 255)), 65535)),
                "required": bool(field.get("required", False)),
                "default": field.get("default"),
            })

        properties: list[str] = []
        db_fields: list[str] = []
        form_fields: list[str] = []
        view_values: list[str] = []
        for field in normalized:
            default_php = "''" if field["default"] is None else repr(field["default"])
            properties.append(f"    public ${field['name']} = {default_php};")
            attrs = f' type="{field["type"]}"'
            if field["type"] == "string":
                attrs += f' size="{field["size"]}"'
            if field["default"] is not None and field["type"] in {"string", "integer", "boolean"}:
                default_text = str(field["default"]).lower() if isinstance(field["default"], bool) else str(field["default"])
                attrs += f' default="{default_text}"'
            db_fields.append(f'    <field name="{field["name"]}"{attrs}/>')
            label = field["name"].replace("_", " ").title()
            php_var = "$" + field["name"]
            form_fields.append(
                '<div class="form-group">'
                f'<label class="control-label" for="{field["name"]}"><?=t({label!r})?></label>'
                f'<input class="form-control" id="{field["name"]}" name="{field["name"]}" value="<?=h({php_var} ?? \'\')?>">'
                '</div>'
            )
            view_values.append(f'<span data-field="{field["name"]}"><?=h({php_var} ?? \'\')?></span>')

        properties_text = "\n".join(properties)
        fields_text = "\n".join(db_fields)
        controller = (
            "<?php\n"
            f"namespace {package_namespace}\\Block\\{camel};\n\n"
            "defined('C5_EXECUTE') or die('Access Denied.');\n\n"
            "use Concrete\\Core\\Block\\BlockController;\n\n"
            "class Controller extends BlockController\n{\n"
            f"    protected $btTable = '{table}';\n"
            "    protected $btInterfaceWidth = 720;\n"
            "    protected $btInterfaceHeight = 520;\n"
            f"{properties_text}\n"
            f"    public function getBlockTypeName() {{ return t({name!r}); }}\n"
            f"    public function getBlockTypeDescription() {{ return t({description!r}); }}\n"
            "}\n"
        )
        db_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<schema xmlns="http://www.concrete5.org/doctrine-xml/0.5">\n'
            f'  <table name="{table}">\n'
            '    <field name="bID" type="integer"><unsigned/><key/></field>\n'
            f'{fields_text}\n'
            '  </table>\n'
            '</schema>\n'
        )
        form = "<?php defined('C5_EXECUTE') or die('Access Denied.'); ?>\n" + "\n".join(form_fields) + "\n"
        view = (
            "<?php defined('C5_EXECUTE') or die('Access Denied.'); ?>\n"
            f'<{component} data-block-id="<?= (int) $bID ?>">'
            + "".join(view_values)
            + f'</{component}>\n'
        )
        return {
            "handle": handle,
            "name": name,
            "table": table,
            "web_component": component,
            "files": {
                "controller.php": controller,
                "db.xml": db_xml,
                "form.php": form,
                "add.php": "<?php $this->inc('form.php'); ?>\n",
                "edit.php": "<?php $this->inc('form.php'); ?>\n",
                "view.php": view,
            },
            "install_code": f"BlockType::installBlockTypeFromPackage('{handle}', $pkg);",
            "upstream_patterns": [
                "parasek/concretecms-block-builder",
                "MacareuxDigital/concretecms-skills/building-blocktypes",
            ],
            "written": False,
        }

    def _safe_worktree_id(self, value: str) -> str:
        value = value.strip()
        if not _SAFE_ID.fullmatch(value):
            raise HTTPException(status_code=422, detail="unsafe worktree_id")
        return value

    def _safe_branch(self, value: str) -> str:
        value = value.strip()
        if not _SAFE_BRANCH.fullmatch(value):
            raise HTTPException(status_code=422, detail="unsafe branch_name")
        if value.startswith("/") or ".." in value or value.endswith("/"):
            raise HTTPException(status_code=422, detail="unsafe branch_name")
        return value

    def _slug(self, message: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", message.lower()).strip("-")
        return (slug or "xavi-change")[:48]

    async def _maybe_ops(self, name: str, enabled: bool, results: dict[str, Any], args: dict[str, Any] | None = None) -> None:
        if not enabled:
            results[name] = {"skipped": True}
            return
        results[name] = await self.ops.call(name, args or {})

    async def apply_change_bundle(self, args: dict[str, Any]) -> dict[str, Any]:
        patch = str(args.get("patch", ""))
        message = str(args.get("message", "")).strip()
        if not patch.strip():
            raise HTTPException(status_code=422, detail="patch is required")
        if not message:
            raise HTTPException(status_code=422, detail="message is required")

        stamp = int(time.time())
        slug = self._slug(message)
        worktree_id = self._safe_worktree_id(str(args.get("worktree_id") or f"bundle-{slug}-{stamp}"))
        branch_name = self._safe_branch(str(args.get("branch_name") or f"xavi/bundle-{slug}-{stamp}"))
        base_ref = str(args.get("base_ref") or "HEAD").strip()
        target_branch = self._safe_branch(str(args.get("target_branch") or "main"))
        test_command = str(args.get("test_command") or "runtime_pytest")
        test_timeout_seconds = max(1, min(int(args.get("test_timeout_seconds", 300)), 900))
        cleanup = bool(args.get("cleanup", True))
        do_push = bool(args.get("push", False))
        do_rebuild = bool(args.get("rebuild", False))
        rebuild_models = bool(args.get("rebuild_models", True))

        results: dict[str, Any] = {
            "worktree_id": worktree_id,
            "branch_name": branch_name,
            "target_branch": target_branch,
            "message": message,
            "push_requested": do_push,
            "rebuild_requested": do_rebuild,
            "steps": {},
        }
        steps = results["steps"]

        created = False
        try:
            steps["create_worktree"] = self.repo.create_worktree(
                {"worktree_id": worktree_id, "branch_name": branch_name, "base_ref": base_ref}
            )
            created = True

            steps["apply_patch"] = self.repo.apply_patch({"worktree_id": worktree_id, "patch": patch})

            steps["run_tests_before_commit"] = self.repo.run_tests(
                {
                    "worktree_id": worktree_id,
                    "test_command": test_command,
                    "timeout_seconds": test_timeout_seconds,
                }
            )
            if not steps["run_tests_before_commit"].get("passed"):
                raise HTTPException(status_code=409, detail={"error": "tests_failed_before_commit", "result": steps["run_tests_before_commit"]})

            commit_approval = self.repo.prepare_commit({"worktree_id": worktree_id, "message": message})
            steps["prepare_commit"] = {k: v for k, v in commit_approval.items() if k != "approval_token"}

            commit_result = self.repo.commit(
                {
                    "worktree_id": worktree_id,
                    "message": message,
                    "approval_token": commit_approval["approval_token"],
                }
            )
            steps["commit"] = commit_result

            steps["run_tests_after_commit"] = self.repo.run_tests(
                {
                    "worktree_id": worktree_id,
                    "test_command": test_command,
                    "timeout_seconds": test_timeout_seconds,
                }
            )
            if not steps["run_tests_after_commit"].get("passed"):
                raise HTTPException(status_code=409, detail={"error": "tests_failed_after_commit", "result": steps["run_tests_after_commit"]})

            integration_approval = self.repo.prepare_integration(
                {"worktree_id": worktree_id, "message": message, "target_branch": target_branch}
            )
            steps["prepare_integration"] = {k: v for k, v in integration_approval.items() if k != "approval_token"}

            integration_result = self.repo.integrate_commit(
                {
                    "worktree_id": worktree_id,
                    "commit": commit_result["commit"],
                    "message": message,
                    "approval_token": integration_approval["approval_token"],
                    "target_branch": target_branch,
                    "expected_main_head": integration_approval["expected_main_head"],
                }
            )
            steps["integrate_commit"] = integration_result
            results["new_head"] = integration_result.get("new_head")

            await self._maybe_ops("ops.git_push", do_push, steps)

            # Never rebuild the runtime from inside this MCP request.
            # Rebuilding the same container that is serving the request cuts off
            # the HTTP connection and appears to ChatGPT as a 502/hang.
            # Return an explicit next action instead.
            rebuild_tool = "ops.runtime_rebuild_models" if rebuild_models else "ops.runtime_rebuild"
            results["rebuild_required"] = do_rebuild
            results["rebuild_tool"] = rebuild_tool if do_rebuild else None

            if do_rebuild:
                steps["ops.runtime_rebuild"] = {
                    "skipped": True,
                    "reason": "rebuilds are intentionally deferred outside dev.apply_change_bundle",
                    "next_tool": rebuild_tool,
                }
            else:
                steps["ops.runtime_rebuild"] = {
                    "skipped": True,
                    "reason": "not requested",
                }

            return results
        finally:
            if cleanup and created:
                try:
                    steps["remove_worktree"] = self.repo.remove_worktree({"worktree_id": worktree_id, "force": True})
                except Exception as exc:
                    steps["remove_worktree"] = {"error": exc.__class__.__name__, "message": str(exc)}
