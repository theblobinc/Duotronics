from __future__ import annotations

import math
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from .fusion_center_tools.cyber import check_cloudflare_radar, check_internet_outages, get_ioda_outages
from .fusion_center_tools.geo import check_nasa_firms
from .fusion_center_tools.news import query_gdelt_events
from .fusion_center_tools.rss import fetch_rss_feed
from .fusion_center_tools.search import search_ddos_secrets_db, search_web
from .fusion_center_tools.telegram import get_telegram_channel_info, list_curated_channels, search_telegram_channels
from .fusion_center_tools.threat_intel import get_pulse_details, lookup_indicator, search_pulses

UPSTREAM = {
    "repository": "https://github.com/Draichi/fusion-center",
    "commit": "cfa25de6aedd3bd75ddef4ebf86e41a53368f05b",
    "license": "MIT",
}

SOURCES = [
    {"id": "gdelt", "name": "GDELT 2.0", "domain": "news", "auth": "none", "tool": "fusion.search_news"},
    {"id": "rss", "name": "Curated RSS feeds", "domain": "news", "auth": "none", "tool": "fusion.fetch_rss_news"},
    {"id": "duckduckgo", "name": "DuckDuckGo", "domain": "web_search", "auth": "none", "tool": "fusion.search_internet"},
    {"id": "ddosecrets", "name": "DDoS Secrets public catalogue", "domain": "public_archives", "auth": "none", "tool": "fusion.search_public_archives", "metadata_only": True},
    {"id": "nasa_firms", "name": "NASA FIRMS", "domain": "satellite", "auth": "NASA_FIRMS_API_KEY", "tool": "fusion.detect_thermal_anomalies"},
    {"id": "ioda", "name": "IODA", "domain": "internet_connectivity", "auth": "none", "tool": "fusion.check_connectivity"},
    {"id": "cloudflare_radar", "name": "Cloudflare Radar", "domain": "internet_traffic", "auth": "optional", "tool": "fusion.check_traffic_metrics"},
    {"id": "telegram", "name": "Telegram public channels", "domain": "social_osint", "auth": "TELEGRAM_API_ID + TELEGRAM_API_HASH", "tool": "fusion.search_telegram"},
    {"id": "alienvault_otx", "name": "AlienVault OTX", "domain": "threat_intelligence", "auth": "OTX_API_KEY", "tool": "fusion.check_ioc"},
]


def _obj(required: list[str] | None = None, properties: dict[str, Any] | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "object", "properties": properties or {}, "additionalProperties": False}
    if required:
        schema["required"] = required
    return schema


def fusion_tool_manifest() -> list[dict[str, Any]]:
    return [
        {"name": "fusion.sources", "description": "List Fusion Center source connectors and whether required credentials are configured.", "read_only": True, "input_schema": _obj()},
        {"name": "fusion.search_news", "description": "Search GDELT global news and return provenance-bearing article records.", "read_only": True, "input_schema": _obj(["keywords"], {"keywords": {"type": "string", "minLength": 1}, "source_country": {"type": ["string", "null"]}, "max_records": {"type": "integer", "minimum": 1, "maximum": 250, "default": 50}, "timespan": {"type": "string", "pattern": "^[0-9]+[dhm]$", "default": "7d"}})},
        {"name": "fusion.fetch_rss_news", "description": "Fetch a curated independent-news RSS feed.", "read_only": True, "input_schema": _obj(["source"], {"source": {"type": "string", "enum": ["meduza", "theinsider", "thecradle"]}, "max_articles": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20}})},
        {"name": "fusion.detect_thermal_anomalies", "description": "Query NASA FIRMS for recent thermal anomalies near a coordinate.", "read_only": True, "input_schema": _obj(["latitude", "longitude"], {"latitude": {"type": "number", "minimum": -90, "maximum": 90}, "longitude": {"type": "number", "minimum": -180, "maximum": 180}, "day_range": {"type": "integer", "minimum": 1, "maximum": 10, "default": 7}, "radius_km": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50}})},
        {"name": "fusion.check_connectivity", "description": "Check IODA country-level connectivity signals and recent outage indicators.", "read_only": True, "input_schema": _obj([], {"country_code": {"type": ["string", "null"], "pattern": "^[A-Za-z]{2}$"}, "region_name": {"type": ["string", "null"]}, "hours_back": {"type": "integer", "minimum": 1, "maximum": 168, "default": 24}})},
        {"name": "fusion.check_traffic_metrics", "description": "Check Cloudflare Radar country traffic or attack metrics.", "read_only": True, "input_schema": _obj(["country_code"], {"country_code": {"type": "string", "pattern": "^[A-Za-z]{2}$"}, "metric": {"type": "string", "default": "traffic"}})},
        {"name": "fusion.get_outages", "description": "Get IODA outage events for a country, region or ASN.", "read_only": True, "input_schema": _obj([], {"entity_type": {"type": "string", "enum": ["country", "region", "asn"], "default": "country"}, "entity_code": {"type": ["string", "null"]}, "days_back": {"type": "integer", "minimum": 1, "maximum": 90, "default": 7}, "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}})},
        {"name": "fusion.search_internet", "description": "Search the public web with DuckDuckGo through the pinned Fusion Center adapter.", "read_only": True, "input_schema": _obj(["query"], {"query": {"type": "string", "minLength": 1}, "max_results": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10}, "region": {"type": ["string", "null"]}, "time_range": {"type": "string", "enum": ["all", "day", "week", "month", "year"], "default": "all"}})},
        {"name": "fusion.search_public_archives", "description": "Search the public DDoS Secrets catalogue and return dataset-level metadata and links only.", "read_only": True, "input_schema": _obj(["query"], {"query": {"type": "string", "minLength": 2}, "max_results": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20}})},
        {"name": "fusion.list_osint_channels", "description": "List curated public Telegram OSINT channels without connecting to Telegram.", "read_only": True, "input_schema": _obj()},
        {"name": "fusion.search_telegram", "description": "Search configured public Telegram channels for recent messages.", "read_only": True, "input_schema": _obj([], {"keywords": {"type": ["string", "null"]}, "channels": {"type": ["array", "null"], "items": {"type": "string"}, "maxItems": 25}, "category": {"type": ["string", "null"]}, "hours_back": {"type": "integer", "minimum": 1, "maximum": 168, "default": 24}, "max_messages": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50}})},
        {"name": "fusion.get_channel_info", "description": "Get metadata for a public Telegram channel.", "read_only": True, "input_schema": _obj(["channel_username"], {"channel_username": {"type": "string", "minLength": 1}})},
        {"name": "fusion.check_ioc", "description": "Look up an indicator of compromise in AlienVault OTX.", "read_only": True, "input_schema": _obj(["indicator"], {"indicator": {"type": "string", "minLength": 1}, "indicator_type": {"type": "string", "enum": ["IPv4", "IPv6", "domain", "hostname", "URL", "FileHash-MD5", "FileHash-SHA1", "CVE", "email"], "default": "IPv4"}})},
        {"name": "fusion.get_threat_pulse", "description": "Get an AlienVault OTX pulse and its indicators.", "read_only": True, "input_schema": _obj(["pulse_id"], {"pulse_id": {"type": "string", "minLength": 1}})},
        {"name": "fusion.search_threats", "description": "Search AlienVault OTX threat pulses.", "read_only": True, "input_schema": _obj(["query"], {"query": {"type": "string", "minLength": 1}, "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20}})},
        {"name": "fusion.plan_analysis", "description": "Create a bounded collection, hypothesis, reflection and verification plan for a fusion question.", "read_only": True, "input_schema": _obj(["task"], {"task": {"type": "string", "minLength": 5}, "project_id": {"type": ["string", "null"]}, "max_hypotheses": {"type": "integer", "minimum": 1, "maximum": 8, "default": 4}})},
        {"name": "fusion.correlate_records", "description": "Deterministically correlate normalized records across sources by entities, time and location.", "read_only": True, "input_schema": _obj(["records"], {"records": {"type": "array", "minItems": 1, "maxItems": 2000, "items": {"type": "object"}}, "time_window_hours": {"type": "number", "minimum": 0, "maximum": 720, "default": 24}, "distance_km": {"type": "number", "minimum": 0, "maximum": 1000, "default": 50}, "minimum_sources": {"type": "integer", "minimum": 2, "maximum": 20, "default": 2}})},
    ]


def _credential_state() -> dict[str, bool]:
    return {
        "nasa_firms": bool(os.environ.get("NASA_FIRMS_API_KEY")),
        "cloudflare": bool(os.environ.get("CLOUDFLARE_API_TOKEN")),
        "telegram": bool(os.environ.get("TELEGRAM_API_ID") and os.environ.get("TELEGRAM_API_HASH")),
        "alienvault_otx": bool(os.environ.get("OTX_API_KEY")),
    }


def _envelope(tool: str, args: dict[str, Any], result: Any, source_ids: list[str]) -> dict[str, Any]:
    return {
        "schema": "xavi-fusion-result-v1",
        "tool": tool,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "query": args,
        "sources": [source for source in SOURCES if source["id"] in source_ids],
        "upstream": UPSTREAM,
        "result": result,
    }


def _public_archive_metadata(result: Any) -> Any:
    if not isinstance(result, dict):
        return result
    safe = {key: value for key, value in result.items() if key not in {"downloads", "files", "credentials", "secrets", "raw_data"}}
    for key in ("results", "datasets", "items"):
        if isinstance(safe.get(key), list):
            rows = []
            for item in safe[key]:
                if not isinstance(item, dict):
                    continue
                rows.append({k: item.get(k) for k in ("title", "name", "url", "link", "description", "summary", "date", "source") if item.get(k) is not None})
            safe[key] = rows
    safe["access_policy"] = "catalogue_metadata_only"
    return safe


def _parse_time(record: dict[str, Any]) -> datetime | None:
    for key in ("timestamp", "datetime", "date", "published_at", "seendate", "acquired_at", "acq_date"):
        value = record.get(key)
        if not value:
            continue
        text = str(value).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            for fmt in ("%Y%m%dT%H%M%SZ", "%Y-%m-%d", "%a, %d %b %Y %H:%M:%S %z"):
                try:
                    parsed = datetime.strptime(text, fmt)
                    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
    return None


def _coordinates(record: dict[str, Any]) -> tuple[float, float] | None:
    lat = record.get("latitude", record.get("lat"))
    lon = record.get("longitude", record.get("lon", record.get("lng")))
    try:
        return float(lat), float(lon)
    except (TypeError, ValueError):
        geometry = record.get("geometry")
        if isinstance(geometry, dict) and geometry.get("type") == "Point":
            coords = geometry.get("coordinates")
            if isinstance(coords, list) and len(coords) >= 2:
                try: return float(coords[1]), float(coords[0])
                except (TypeError, ValueError): pass
    return None


def _haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a); lat2, lon2 = map(math.radians, b)
    dlat=lat2-lat1; dlon=lon2-lon1
    value=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371.0088 * 2 * math.atan2(math.sqrt(value), math.sqrt(max(0.0, 1-value)))


def _entities(record: dict[str, Any]) -> set[str]:
    values: list[Any] = []
    for key in ("entities", "tags", "people", "organizations", "locations", "keywords"):
        value=record.get(key)
        if isinstance(value, list): values.extend(value)
        elif value: values.append(value)
    for key in ("person", "organization", "location", "country", "region", "case_id"):
        if record.get(key): values.append(record[key])
    return {re.sub(r"\s+", " ", str(v).strip().lower()) for v in values if str(v).strip()}


def correlate_records(records: list[dict[str, Any]], time_window_hours: float, distance_km: float, minimum_sources: int) -> dict[str, Any]:
    prepared=[]
    for index, record in enumerate(records):
        source=str(record.get("source") or record.get("data_source") or record.get("dataset") or "unknown")
        prepared.append({"index": index, "record": record, "source": source, "time": _parse_time(record), "coordinates": _coordinates(record), "entities": _entities(record)})
    correlations=[]
    entity_groups: dict[str,list[dict[str,Any]]]=defaultdict(list)
    for item in prepared:
        for entity in item["entities"]: entity_groups[entity].append(item)
    for entity, items in entity_groups.items():
        sources=sorted({i["source"] for i in items})
        if len(sources)>=minimum_sources:
            correlations.append({"type":"shared_entity","entity":entity,"record_indexes":sorted({i["index"] for i in items}),"sources":sources,"strength":min(1.0,len(sources)/max(minimum_sources,3))})
    for i,left in enumerate(prepared):
        for right in prepared[i+1:]:
            if left["source"]==right["source"]: continue
            reasons=[]; score=0.0
            shared=sorted(left["entities"] & right["entities"])
            if shared: reasons.append({"type":"entity","values":shared[:20]}); score+=0.45
            if left["time"] and right["time"]:
                delta=abs((left["time"]-right["time"]).total_seconds())/3600
                if delta<=time_window_hours: reasons.append({"type":"time","hours":round(delta,3)}); score+=0.25*(1-delta/max(time_window_hours,0.0001))
            if left["coordinates"] and right["coordinates"]:
                distance=_haversine(left["coordinates"],right["coordinates"])
                if distance<=distance_km: reasons.append({"type":"space","kilometres":round(distance,3)}); score+=0.30*(1-distance/max(distance_km,0.0001))
            if reasons and score>=0.2:
                correlations.append({"type":"record_pair","record_indexes":[left["index"],right["index"]],"sources":[left["source"],right["source"]],"reasons":reasons,"strength":round(min(score,1.0),4)})
    correlations.sort(key=lambda item:item.get("strength",0),reverse=True)
    return {"record_count":len(records),"source_count":len({p['source'] for p in prepared}),"correlation_count":len(correlations),"correlations":correlations[:1000],"parameters":{"time_window_hours":time_window_hours,"distance_km":distance_km,"minimum_sources":minimum_sources}}


def plan_analysis(task: str, project_id: str | None, max_hypotheses: int) -> dict[str, Any]:
    text=task.lower()
    recommended=["fusion.search_news","fusion.search_internet"]
    if any(word in text for word in ("fire","thermal","explosion","satellite","wildfire")): recommended.append("fusion.detect_thermal_anomalies")
    if any(word in text for word in ("internet","outage","shutdown","traffic","ddos","cyber")): recommended.extend(["fusion.check_connectivity","fusion.check_traffic_metrics"])
    if any(word in text for word in ("telegram","channel","social","sighting")): recommended.append("fusion.search_telegram")
    if any(word in text for word in ("ioc","malware","threat","hash","domain","ip address")): recommended.extend(["fusion.check_ioc","fusion.search_threats"])
    recommended=list(dict.fromkeys(recommended))
    templates=[
        "The primary reported event is corroborated by at least two independent source domains.",
        "The apparent relationship is explained by a shared time-and-location context rather than direct causation.",
        "Source reliability or publication lag explains material contradictions in the available records.",
        "A missing source class would substantially change the current assessment.",
        "The observed pattern is consistent with the baseline and does not indicate an exceptional event.",
    ][:max_hypotheses]
    return {
        "task":task,"project_id":project_id,"method":"decompose-hypothesize-gather-analyze-reflect-correlate-verify-synthesize",
        "stages":[
            {"id":"decompose","output":"bounded sub-questions and required fields"},
            {"id":"hypothesize","output":"testable competing hypotheses"},
            {"id":"gather","tools":recommended,"output":"source records with retrieval provenance"},
            {"id":"analyze","output":"support, contradiction, uncertainty and missingness"},
            {"id":"reflect","output":"bias, source dependence and alternate explanations"},
            {"id":"correlate","tool":"fusion.correlate_records","output":"cross-source entity/time/space links"},
            {"id":"verify","output":"claim-by-claim source check and confidence"},
            {"id":"synthesize","output":"bounded report separating fact, inference and unknown"},
        ],
        "hypotheses":[{"id":f"H{i+1}","statement":statement,"initial_confidence":0.5} for i,statement in enumerate(templates)],
        "recommended_tools":recommended,
        "verification_rules":["Do not treat correlated observations as proof of causation.","Preserve contradictory source assertions.","Record retrieval time, source URL and query parameters.","Require at least two independent source domains for high-confidence synthesis."],
        "upstream":UPSTREAM,
    }


async def call_fusion_tool(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    aliases={
        "search_news":"fusion.search_news","fetch_rss_news":"fusion.fetch_rss_news","detect_thermal_anomalies":"fusion.detect_thermal_anomalies",
        "check_connectivity":"fusion.check_connectivity","check_traffic_metrics":"fusion.check_traffic_metrics","get_outages":"fusion.get_outages",
        "search_internet":"fusion.search_internet","search_leaks":"fusion.search_public_archives","list_osint_channels":"fusion.list_osint_channels",
        "search_telegram":"fusion.search_telegram","get_channel_info":"fusion.get_channel_info","check_ioc":"fusion.check_ioc",
        "get_threat_pulse":"fusion.get_threat_pulse","search_threats":"fusion.search_threats",
    }
    tool=aliases.get(tool,tool)
    try:
        if tool=="fusion.sources":
            configured=_credential_state(); rows=[]
            for source in SOURCES:
                row=dict(source); auth=row.get("auth")
                row["enabled"] = auth in {"none","optional"} or configured.get(source["id"],False)
                rows.append(row)
            return {"schema":"xavi-fusion-sources-v1","sources":rows,"upstream":UPSTREAM}
        if tool=="fusion.search_news": return _envelope(tool,args,await query_gdelt_events(str(args["keywords"]),args.get("source_country"),int(args.get("max_records",50)),str(args.get("timespan","7d"))),["gdelt"])
        if tool=="fusion.fetch_rss_news": return _envelope(tool,args,await fetch_rss_feed(str(args["source"]),int(args.get("max_articles",20))),["rss"])
        if tool=="fusion.detect_thermal_anomalies": return _envelope(tool,args,await check_nasa_firms(float(args["latitude"]),float(args["longitude"]),int(args.get("day_range",7)),int(args.get("radius_km",50))),["nasa_firms"])
        if tool=="fusion.check_connectivity": return _envelope(tool,args,await check_internet_outages(args.get("country_code"),args.get("region_name"),int(args.get("hours_back",24))),["ioda"])
        if tool=="fusion.check_traffic_metrics": return _envelope(tool,args,await check_cloudflare_radar(str(args["country_code"]),str(args.get("metric","traffic"))),["cloudflare_radar"])
        if tool=="fusion.get_outages": return _envelope(tool,args,await get_ioda_outages(str(args.get("entity_type","country")),args.get("entity_code"),int(args.get("days_back",7)),int(args.get("limit",50))),["ioda"])
        if tool=="fusion.search_internet": return _envelope(tool,args,await search_web(str(args["query"]),int(args.get("max_results",10)),args.get("region"),str(args.get("time_range","all"))),["duckduckgo"])
        if tool=="fusion.search_public_archives": return _envelope(tool,args,_public_archive_metadata(await search_ddos_secrets_db(str(args["query"]),int(args.get("max_results",20)))),["ddosecrets"])
        if tool=="fusion.list_osint_channels": return _envelope(tool,args,list_curated_channels(),["telegram"])
        if tool=="fusion.search_telegram": return _envelope(tool,args,await search_telegram_channels(args.get("keywords"),args.get("channels"),args.get("category"),int(args.get("hours_back",24)),int(args.get("max_messages",50))),["telegram"])
        if tool=="fusion.get_channel_info": return _envelope(tool,args,await get_telegram_channel_info(str(args["channel_username"])),["telegram"])
        if tool=="fusion.check_ioc": return _envelope(tool,args,await lookup_indicator(str(args["indicator"]),str(args.get("indicator_type","IPv4"))),["alienvault_otx"])
        if tool=="fusion.get_threat_pulse": return _envelope(tool,args,await get_pulse_details(str(args["pulse_id"])),["alienvault_otx"])
        if tool=="fusion.search_threats": return _envelope(tool,args,await search_pulses(str(args["query"]),int(args.get("limit",20))),["alienvault_otx"])
        if tool=="fusion.plan_analysis": return plan_analysis(str(args["task"]),args.get("project_id"),int(args.get("max_hypotheses",4)))
        if tool=="fusion.correlate_records": return correlate_records(list(args["records"]),float(args.get("time_window_hours",24)),float(args.get("distance_km",50)),int(args.get("minimum_sources",2)))
    except KeyError as exc:
        raise HTTPException(status_code=422,detail=f"missing argument: {exc.args[0]}") from exc
    except (TypeError,ValueError) as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
    raise HTTPException(status_code=404,detail=f"unknown Fusion Center MCP tool: {tool}")


def fusion_resources() -> list[dict[str,str]]:
    return [
        {"uri":"fusion://sources","name":"Fusion Center source catalog","description":"Source connectors, credential requirements and tool mappings.","mimeType":"application/json"},
        {"uri":"fusion://methodology","name":"Fusion analysis methodology","description":"Decomposition, hypothesis, correlation, reflection and verification workflow.","mimeType":"application/json"},
    ]


async def read_fusion_resource(uri: str) -> dict[str,Any] | None:
    if uri=="fusion://sources": return {"uri":uri,"mimeType":"application/json","contents":await call_fusion_tool("fusion.sources",{})}
    if uri=="fusion://methodology": return {"uri":uri,"mimeType":"application/json","contents":plan_analysis("General multi-source information-fusion analysis",None,4)}
    return None
