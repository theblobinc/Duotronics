import asyncio

from app.duotronic_runtime.fusion_center_mcp import (
    call_fusion_tool,
    correlate_records,
    fusion_resources,
    fusion_tool_manifest,
    plan_analysis,
)


def test_manifest_and_resources_are_namespaced():
    names={item['name'] for item in fusion_tool_manifest()}
    assert len(names) >= 17
    assert all(name.startswith('fusion.') for name in names)
    assert {'fusion.search_news','fusion.detect_thermal_anomalies','fusion.correlate_records'} <= names
    assert {item['uri'] for item in fusion_resources()} == {'fusion://sources','fusion://methodology'}


def test_source_catalog_works_without_credentials():
    result=asyncio.run(call_fusion_tool('fusion.sources',{}))
    assert result['schema']=='xavi-fusion-sources-v1'
    assert len(result['sources']) >= 9
    assert any(item['id']=='gdelt' and item['enabled'] for item in result['sources'])


def test_plan_contains_verification_and_multiple_domains():
    plan=plan_analysis('Correlate a thermal anomaly with news and an internet outage',None,4)
    assert 'fusion.detect_thermal_anomalies' in plan['recommended_tools']
    assert 'fusion.check_connectivity' in plan['recommended_tools']
    assert len(plan['hypotheses'])==4
    assert any(stage['id']=='verify' for stage in plan['stages'])


def test_deterministic_cross_source_correlation():
    records=[
        {'source':'news','timestamp':'2026-08-05T00:00:00Z','latitude':53.9,'longitude':-122.7,'entities':['Example Person','Prince George']},
        {'source':'weather','timestamp':'2026-08-05T01:00:00Z','latitude':53.91,'longitude':-122.71,'entities':['Prince George']},
        {'source':'map','timestamp':'2026-08-07T00:00:00Z','latitude':60.0,'longitude':-130.0,'entities':['Other']},
    ]
    result=correlate_records(records,24,50,2)
    assert result['correlation_count'] >= 2
    assert any(c['type']=='shared_entity' and c['entity']=='prince george' for c in result['correlations'])
    assert any(c['type']=='record_pair' and c['record_indexes']==[0,1] for c in result['correlations'])
