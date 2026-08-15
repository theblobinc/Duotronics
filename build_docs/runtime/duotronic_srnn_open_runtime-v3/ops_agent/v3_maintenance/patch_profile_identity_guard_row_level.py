from pathlib import Path

p = Path('/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/app/duotronic_runtime/api.py')
s = p.read_text(encoding='utf-8')
start = s.index('def _guard_profile_search_identity(messages: list[ChatMessage], response_text: str) -> str:\n')
end = s.index('\ndef ', start + 5)
new = '''def _guard_profile_search_identity(messages: list[ChatMessage], response_text: str) -> str:
    """Keep person/profile synthesis aligned to row-level disambiguating evidence."""
    query = _wgrnn_latest_user_query(messages).strip()
    low = query.lower()
    profile_markers = (
        "facebook user", "facebook profile", "instagram user", "instagram profile",
        "linkedin profile", "profile for", "user named", "person named",
    )
    if not any(marker in low for marker in profile_markers):
        return response_text
    match = re.search(r"\\bfrom\\s+([^?!.;,]+)", query, flags=re.I)
    if not match:
        return response_text
    location = re.sub(r"\\s+", " ", match.group(1)).strip()
    if not location:
        return response_text
    evidence = _parse_search_tool_output(_latest_search_tool_message(messages))
    if evidence is None:
        return response_text
    rows = [row for row in (evidence.get("results") or []) if isinstance(row, dict)]
    if not rows:
        return response_text

    location_tokens = [
        token for token in re.findall(r"[a-z0-9]+", location.lower())
        if len(token) > 1 and token not in {"the", "and"}
    ]

    def row_blob(row: dict[str, Any]) -> str:
        return " ".join([
            str(row.get("title") or ""),
            str(row.get("snippet") or row.get("content") or ""),
            str(row.get("url") or ""),
        ]).lower()

    location_matches = [
        row for row in rows
        if location_tokens and all(token in row_blob(row) for token in location_tokens)
    ]

    def render(row: dict[str, Any], *, snippet: bool = False) -> str:
        title = str(row.get("title") or "Untitled result").strip()
        url = str(row.get("url") or "").strip()
        text = str(row.get("snippet") or row.get("content") or "").strip()
        item = f"- {title}"
        if url:
            item += f" — {url}"
        if snippet and text:
            item += f" — {text}"
        return item

    # A row has to carry its own requested disambiguator. Never use one result's
    # location/employer/school evidence to authenticate neighboring result rows.
    if len(location_matches) == 1:
        strongest = location_matches[0]
        lines = [
            f"The strongest matching profile is:",
            render(strongest, snippet=True),
            f"That result explicitly mentions {location}, so it matches the location in your request.",
        ]
        alternatives = [row for row in rows if row is not strongest]
        if alternatives:
            lines.append("I also found other profiles/pages with the same name, but those results do not independently verify that location:")
            lines.extend(render(row) for row in alternatives[:4])
        lines.append("So I’d treat the first profile as the strongest public-web match, rather than assuming every same-name result is the same person.")
        return "\\n".join(lines)

    if len(location_matches) > 1:
        lines = [
            f"I found {len(location_matches)} profile results that independently mention {location}:",
        ]
        lines.extend(render(row, snippet=True) for row in location_matches[:5])
        lines.append("Because more than one result carries the requested location, the search evidence alone does not prove they are the same account/person.")
        return "\\n".join(lines)

    count = int(evidence.get("number_of_results") or len(rows))
    lines = [f"I found {count} candidate profile results:"]
    lines.extend(render(row) for row in rows[:5])
    lines.append(
        f"None of the returned result rows independently verifies the requested location ({location}), "
        "so I can't identify one of them as the intended person from this search alone."
    )
    return "\\n".join(lines)

'''
p.write_text(s[:start] + new + s[end:], encoding='utf-8')
print('patched', p)
