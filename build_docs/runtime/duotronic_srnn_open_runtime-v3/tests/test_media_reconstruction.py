import json
import shutil
from pathlib import Path
import math
import numpy as np

from duotronic_runtime.media_reconstruction import MediaReconstructionManager, SCHEMA_VERSION, _note_name, _color_name


class RegistryStub:
    def scheduler_candidates(self, **kwargs):
        return {"candidates": []}
    def nodes(self):
        return []


def manager(tmp_path):
    return MediaReconstructionManager(tmp_path, RegistryStub(), max_workers=1)


def test_note_and_color_helpers():
    assert _note_name(440.0)[0] == "A4"
    assert _color_name([230, 20, 20]) == "red"


def test_anchor_selection_keeps_change_points(tmp_path):
    m = manager(tmp_path)
    metrics = [{"sample_index": i, "time_seconds": i / 4, "change_score": 40 if i in {12, 28} else 1} for i in range(40)]
    rows = m._select_anchors(metrics, interval_seconds=2.0, max_anchors=12)
    ids = {r["sample_index"] for r in rows}
    assert 12 in ids and 28 in ids and 0 in ids and 39 in ids
    m.shutdown()


def test_audio_features_detects_a4(tmp_path):
    m = manager(tmp_path)
    sr = 16000
    t = np.arange(sr * 2, dtype=np.float32) / sr
    pcm = (0.2 * np.sin(2 * math.pi * 440 * t)).astype(np.float32)
    out = m._audio_features(pcm, sr)
    assert out["note_intervals"]
    assert any(row["note"] == "A4" for row in out["note_intervals"])
    assert out["frames"]
    m.shutdown()


def test_transcript_words_and_non_geographic_accent(tmp_path):
    m = manager(tmp_path)
    audio = {"frames": [{"time_seconds": 0.5, "rms": 0.1, "pitch_hz": 120.0}, {"time_seconds": 1.0, "rms": 0.2, "pitch_hz": 140.0}]}
    transcript = {"segments": [{"text": " hello world", "start": 0.0, "end": 1.5, "words": [{"word": " hello", "start": 0.1, "end": 0.6, "probability": 0.9}, {"word": " world", "start": 0.7, "end": 1.2, "probability": 0.8}]}]}
    words, segments = m._transcript_witnesses(transcript, audio)
    assert len(words) == 2
    assert segments[0]["delivery"]["accent"]["status"] == "not_geographically_inferred"
    m.shutdown()


def test_state_intervals_are_frame_addressable(tmp_path):
    m = manager(tmp_path)
    anchors = [{"time_seconds": 0.0, "frame_id": "a", "people": [], "objects": [], "setting": "room", "lighting": "dim", "camera_shot": "wide", "camera_motion": "static", "visible_text": [], "overall_action": "sitting", "confidence": 0.9}, {"time_seconds": 2.0, "frame_id": "b", "people": [], "objects": [], "setting": "room", "lighting": "dim", "camera_shot": "wide", "camera_motion": "static", "visible_text": [], "overall_action": "standing", "confidence": 0.9}]
    out = m._state_intervals(anchors, 60.0, 4.0)
    assert out[0]["start_frame"] == 0 and out[0]["end_frame"] == 119
    assert out[1]["start_frame"] == 120
    assert out[0]["gate"]["schema_version"] == "wgrnn_temporal_witness_gate/v2"
    m.shutdown()


def test_range_timeline_offsets_shared_words_exactly_once(tmp_path):
    class Registry:
        def scheduler_candidates(self, **kwargs): return {"candidates": []}
        def nodes(self): return []
    manager = MediaReconstructionManager(tmp_path / "jobs", Registry())
    shared_word = {"word": "hello", "start_seconds": 0.25, "end_seconds": 0.5, "probability": 0.9}
    words = [shared_word]
    segments = [{"start_seconds": 0.2, "end_seconds": 0.8, "words": [shared_word]}]
    metrics = [{"time_seconds": 0.0}]
    vision = [{"time_seconds": 0.4}]
    audio = {
        "frames": [{"time_seconds": 0.1}],
        "onsets": [0.3],
        "note_intervals": [{"start_seconds": 0.4, "end_seconds": 0.6}],
        "chord_intervals": [{"start_seconds": 0.5, "end_seconds": 0.7}],
    }
    manager._offset_analysis_timeline(
        offset=2.0,
        metrics=metrics,
        vision=vision,
        audio=audio,
        words=words,
        transcript_segments=segments,
    )
    assert shared_word["start_seconds"] == 2.25
    assert shared_word["end_seconds"] == 2.5
    assert segments[0]["start_seconds"] == 2.2
    assert segments[0]["end_seconds"] == 2.8
    assert metrics[0]["time_seconds"] == 2.0
    assert vision[0]["time_seconds"] == 2.4
    assert audio["frames"][0]["time_seconds"] == 2.1
    assert audio["onsets"] == [2.3]
    manager.shutdown()


def test_transcription_normalizes_to_wav_and_retries_transient_disconnect(tmp_path, monkeypatch):
    m = manager(tmp_path)
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"not-real-media")
    normalized = tmp_path / "transcription-16k-mono.wav"
    normalized.write_bytes(b"RIFFfake")
    monkeypatch.setattr(m, "_normalize_transcription_audio", lambda _source: normalized)
    monkeypatch.setattr(m, "_service", lambda _name: {"candidate": {"node_id": "vm1", "service_endpoint": "http://10.77.0.3:8790"}, "record": {"inference_path": "/inference", "model": "ggml-small.bin", "image": "whisper", "image_id": "img"}})
    seen = []
    class Response:
        status_code = 200
        def raise_for_status(self): return None
        def json(self): return {"segments": []}
    class Client:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def post(self, url, files=None, data=None):
            filename, fh, mime = files["file"]
            seen.append((url, filename, mime, fh.read(), data))
            if len(seen) == 1:
                raise __import__('httpx').RemoteProtocolError("disconnect")
            return Response()
    monkeypatch.setattr("duotronic_runtime.media_reconstruction.httpx.Client", Client)
    payload, worker = m._transcription(source, "video/mp4")
    assert payload == {"segments": []}
    assert len(seen) == 2
    assert all(row[1] == "transcription-16k-mono.wav" and row[2] == "audio/wav" for row in seen)
    assert worker["status"] == "completed"
    assert worker["attempts"] == 2 and worker["retried"] is True
    assert worker["normalized_audio"] is True
    m.shutdown()

def test_job_history_persists_result_and_allows_terminal_delete(tmp_path, monkeypatch):
    import time
    m = manager(tmp_path)
    def fake_analyze(source, *, filename, mime_type, options, progress):
        progress("fake", 0.5)
        return {"summary": {"ok": True}, "nodes": [{"witness": {"reconstruction": {"schema_version": SCHEMA_VERSION}}}]}
    monkeypatch.setattr(m, "analyze", fake_analyze)
    started = m.start_job(b"fixture", filename="x.bin", mime_type="application/octet-stream")
    job_id = started["job_id"]
    for _ in range(100):
        state = m.status(job_id)
        if state["status"] == "completed":
            break
        time.sleep(0.01)
    assert state["status"] == "completed"
    history = m.list_jobs(limit=10)
    assert history["jobs"][0]["job_id"] == job_id
    assert history["jobs"][0]["has_result"] is True
    assert m.result(job_id)["summary"]["ok"] is True
    deleted = m.delete(job_id)
    assert deleted["deleted"] is True
    import pytest
    with pytest.raises(KeyError):
        m.status(job_id)
    m.shutdown()


def test_cancel_running_job_is_cooperative(tmp_path, monkeypatch):
    import time
    m = manager(tmp_path)
    def fake_analyze(source, *, filename, mime_type, options, progress):
        for i in range(200):
            progress("fake_work", min(0.9, i / 200))
            time.sleep(0.002)
        return {"summary": {}, "nodes": []}
    monkeypatch.setattr(m, "analyze", fake_analyze)
    job_id = m.start_job(b"fixture", filename="x.bin", mime_type="application/octet-stream")["job_id"]
    for _ in range(100):
        if m.status(job_id)["status"] == "running":
            break
        time.sleep(0.005)
    requested = m.cancel(job_id)
    assert requested["status"] in {"cancelling", "cancelled"}
    for _ in range(200):
        state = m.status(job_id)
        if state["status"] == "cancelled":
            break
        time.sleep(0.005)
    assert state["status"] == "cancelled"
    assert state["cancel_requested"] is True
    m.shutdown()


def test_startup_recovery_marks_stale_running_job_interrupted(tmp_path):
    import json
    root = tmp_path / "mediarec-1234567890abcdef12345678"
    root.mkdir()
    (root / "source.bin").write_bytes(b"x")
    (root / "state.json").write_text(json.dumps({
        "schema_version": SCHEMA_VERSION,
        "job_id": root.name,
        "status": "running",
        "stage": "vision_semantics",
        "progress": 0.4,
        "created_at_ms": 1,
    }))
    m = MediaReconstructionManager(tmp_path, RegistryStub(), max_workers=1)
    state = m.status(root.name)
    assert state["status"] == "interrupted"
    assert state["detail"] == "runtime_restart_interrupted_job"
    assert m.list_jobs(status="interrupted")["jobs"][0]["job_id"] == root.name
    m.shutdown()


def test_transcript_witnesses_include_measured_prosody_and_token_kind(tmp_path):
    m = manager(tmp_path)
    audio = {"frames": [
        {"time_seconds": 0.2, "rms": 0.02, "pitch_hz": 110.0, "spectral_centroid_hz": 700.0, "spectral_flux": 0.1},
        {"time_seconds": 0.8, "rms": 0.08, "pitch_hz": 150.0, "spectral_centroid_hz": 1100.0, "spectral_flux": 0.3},
    ]}
    transcript = {"segments": [{"text": " hello (laughs)", "start": 0.0, "end": 1.0, "words": [
        {"word": " hello", "start": 0.1, "end": 0.4, "probability": 0.9},
        {"word": " (laughs)", "start": 0.6, "end": 0.9, "probability": 0.7},
    ]}]}
    words, segments = m._transcript_witnesses(transcript, audio)
    assert words[0]["token_kind"] == "lexical"
    assert words[1]["token_kind"] == "nonverbal_caption"
    assert words[1]["pause_before_seconds"] == 0.2
    delivery = segments[0]["delivery"]
    assert delivery["segment_asr_probability_mean"] == 0.8
    assert delivery["prosody"]["pace_band"] == "moderate"
    assert delivery["prosody"]["authority"] == "heuristic_labels_from_measured_acoustics"
    assert delivery["affect"]["status"] == "not_inferred_from_acoustics_alone"
    m.shutdown()


def test_state_intervals_preserve_rich_visual_semantics(tmp_path):
    m = manager(tmp_path)
    anchors = [{"time_seconds": 0.0, "frame_id": "f", "people": [{"local_id":"p1","visible_skin_tone":"medium brown","hair":"dark short","clothing":["blue shirt"],"facial_expression":"smiling","action":"sitting"}],
                "objects": [{"name":"couch","color":"gray","material":"fabric","state":"occupied","position":"center"}],
                "setting":"living room","foreground":"coffee table","background":"wall art","dominant_colors":["gray","blue"],
                "spatial_relations":["person seated on couch"],"lighting":"warm","camera_shot":"medium","camera_angle":"eye-level","camera_motion":"static",
                "visible_text":[],"text_regions":[],"overall_action":"person sitting","quality_issues":[],"confidence":0.9}]
    out=m._state_intervals(anchors, 30.0, 1.0)
    st=out[0]["state"]
    assert st["foreground"] == "coffee table"
    assert st["objects"][0]["material"] == "fabric"
    assert st["people"][0]["facial_expression"] == "smiling"
    assert st["camera_angle"] == "eye-level"
    m.shutdown()


def test_vision_semantics_recovers_truncated_batch_with_single_frame_fallback(tmp_path, monkeypatch):
    import json as _json
    m = manager(tmp_path)
    anchors=[]
    for i in range(2):
        img=tmp_path / f"a{i}.jpg"; img.write_bytes(b"jpeg")
        anchors.append({"image_path":str(img),"anchor_index":i,"time_seconds":float(i),"sample_index":i})
    monkeypatch.setattr(m, "_service", lambda _name: {"candidate":{"node_id":"prod3","service_endpoint":"http://vision"},"record":{"inference_path":"/api/generate","model":"gemma3:4b"}})
    calls=[]
    class Resp:
        def __init__(self, body): self._body=body
        def raise_for_status(self): return None
        def json(self): return self._body
    class Client:
        def __init__(self,*a,**k): pass
        def __enter__(self): return self
        def __exit__(self,*a): return False
        def post(self,url,json=None):
            calls.append(json)
            if len(json["images"]) > 1:
                return Resp({"response":"{\\\"frames\\\":[{\\\"frame_id\\\":\\\"f0000@0.000s\\\",\\\"setting\\\":\\\"room"})
            fid="f0000@0.000s" if len(calls)==2 else "f0001@1.000s"
            frame={"frame_id":fid,"people":[],"objects":[],"setting":"room","lighting":"day","camera_shot":"wide","camera_motion":"static","visible_text":[],"overall_action":"none","confidence":.9}
            return Resp({"response":_json.dumps({"frames":[frame]})})
    monkeypatch.setattr("duotronic_runtime.media_reconstruction.httpx.Client", Client)
    out, worker=m._vision_semantics(anchors, lambda *a: None)
    assert len(out)==2 and all(x["setting"]=="room" for x in out)
    assert worker["structured_fallback_batches"]==1
    assert worker["structured_fallback_frames"]==2
    assert len(calls)==3
    assert calls[0]["options"]["num_predict"]==2600
    assert calls[1]["options"]["num_predict"]==3200
    m.shutdown()


def test_entity_tracks_are_ephemeral_and_associate_visible_continuity(tmp_path):
    m=manager(tmp_path)
    vision=[
      {"time_seconds":0.0,"frame_id":"f0","people":[{"local_id":"p1","hair":"short dark","clothing":["blue jacket"],"bbox":[.1,.1,.2,.5],"confidence":.9}],"objects":[{"name":"chair","color":"brown","attributes":["wooden"],"bbox":[.6,.3,.2,.4],"confidence":.9}]},
      {"time_seconds":1.0,"frame_id":"f1","people":[{"local_id":"p9","hair":"dark short","clothing":["blue jacket"],"bbox":[.13,.1,.2,.5],"confidence":.88}],"objects":[{"name":"chair","color":"brown","attributes":["wooden"],"bbox":[.61,.3,.2,.4],"confidence":.9}]},
      {"time_seconds":2.0,"frame_id":"f2","people":[{"local_id":"p2","hair":"long light","clothing":["white coat"],"bbox":[.75,.1,.18,.5],"confidence":.8}],"objects":[]},
    ]
    tracks=m._entity_tracks(vision)
    assert vision[0]["people"][0]["ephemeral_track_id"] == vision[1]["people"][0]["ephemeral_track_id"]
    assert vision[2]["people"][0]["ephemeral_track_id"] != vision[0]["people"][0]["ephemeral_track_id"]
    assert vision[0]["objects"][0]["ephemeral_track_id"] == vision[1]["objects"][0]["ephemeral_track_id"]
    assert all(t["identity_claim"] is False for t in tracks)
    assert all(t["authority"] == "ephemeral_visual_association_hypothesis" for t in tracks)
    assert max(t["observation_count"] for t in tracks) == 2
    m.shutdown()


def test_recurrence_prefers_ephemeral_track_signature(tmp_path):
    m=manager(tmp_path)
    vision=[
      {"time_seconds":0.0,"people":[{"ephemeral_track_id":"person-track-0001","clothing":["blue"]}],"objects":[]},
      {"time_seconds":1.0,"people":[{"ephemeral_track_id":"person-track-0001","clothing":["red"]}],"objects":[]},
    ]
    recurrence=m._recurrence(vision,[],{"chord_intervals":[]})
    assert recurrence["recurrence_edges"] == 1
    assert recurrence["temporal_links"][0]["signature"] == "person:person-track-0001"
    m.shutdown()


def test_vision_semantics_aligns_single_valid_frame_even_with_wrong_model_frame_id(tmp_path, monkeypatch):
    import json as _json
    m=manager(tmp_path)
    img=tmp_path/'a.jpg'; img.write_bytes(b'jpeg')
    anchor={"image_path":str(img),"anchor_index":0,"time_seconds":1.25,"sample_index":5}
    monkeypatch.setattr(m,"_service",lambda _name:{"candidate":{"node_id":"prod3","service_endpoint":"http://vision"},"record":{"inference_path":"/api/generate","model":"gemma3:4b"}})
    class Resp:
        def raise_for_status(self): return None
        def json(self): return {"response":_json.dumps({"frames":[{"frame_id":"frame-1","people":[],"objects":[],"setting":"office","lighting":"bright","camera_shot":"wide","camera_motion":"static","visible_text":[],"overall_action":"none","confidence":.91}]})}
    class Client:
        def __init__(self,*a,**k): pass
        def __enter__(self): return self
        def __exit__(self,*a): return False
        def post(self,*a,**k): return Resp()
    monkeypatch.setattr("duotronic_runtime.media_reconstruction.httpx.Client",Client)
    out,worker=m._vision_semantics([anchor],lambda *a:None)
    assert len(out)==1 and out[0]["setting"]=="office"
    assert out[0]["frame_id"]=="f0000@1.250s"
    assert worker["structured_fallback_batches"]==0
    m.shutdown()


def test_vision_schema_bounds_rich_arrays(tmp_path):
    m=manager(tmp_path); schema=m._vision_schema(); frame=schema["properties"]["frames"]["items"]
    assert frame["properties"]["people"]["maxItems"]==16
    assert frame["properties"]["objects"]["maxItems"]==48
    assert frame["properties"]["text_regions"]["maxItems"]==24
    assert frame["properties"]["dominant_colors"]["maxItems"]==12
    m.shutdown()


def test_entity_tracks_emit_screen_space_trajectory_and_held_object_delta(tmp_path):
    m = manager(tmp_path)
    vision = [
        {
            "time_seconds": 1.0, "frame_id": "f1",
            "people": [{
                "local_id": "p1", "hair": "short dark", "clothing": ["blue jacket"],
                "held_objects": [], "action": "reaching", "pose": "standing",
                "hand_state": "right hand open", "bbox": [0.10, 0.10, 0.20, 0.50], "confidence": 0.92,
            }],
            "objects": [],
            "camera_motion": "static", "overall_action": "person reaches",
        },
        {
            "time_seconds": 2.0, "frame_id": "f2",
            "people": [{
                "local_id": "p7", "hair": "dark short", "clothing": ["blue jacket"],
                "held_objects": ["cup"], "action": "holding cup", "pose": "standing",
                "hand_state": "right hand holding cup", "bbox": [0.30, 0.10, 0.20, 0.50], "confidence": 0.90,
            }],
            "objects": [],
            "camera_motion": "pan right", "overall_action": "person holds cup",
        },
    ]
    tracks = m._entity_tracks(vision)
    person = next(t for t in tracks if t["kind"] == "person")
    assert person["identity_claim"] is False
    assert person["trajectory"]["net_screen_direction"] == "right"
    assert person["trajectory"]["moving_step_count"] == 1
    assert person["trajectory"]["net_dx_normalized"] == 0.2
    motion = person["observations"][1]["motion_from_previous"]
    assert motion["screen_direction"] == "right"
    assert motion["speed_normalized_per_second"] == 0.2
    assert motion["coordinate_space"] == "normalized_frame_xy_y_down"
    held = next(x for x in person["state_transitions"] if x["field"] == "held_objects")
    assert held["transition_kind"] == "held_object_change"
    assert held["added"] == ["cup"]
    assert held["removed"] == []
    assert "sometime after" in held["time_semantics"]
    m.shutdown()


def test_temporal_transitions_bound_motion_entity_and_scene_changes(tmp_path):
    m = manager(tmp_path)
    vision = [
        {
            "time_seconds": 1.0, "frame_id": "f1",
            "people": [{
                "local_id": "p1", "hair": "short dark", "clothing": ["blue jacket"],
                "held_objects": [], "action": "reaching", "pose": "standing",
                "bbox": [0.10, 0.10, 0.20, 0.50], "confidence": 0.92,
            }],
            "objects": [], "camera_motion": "static", "setting": "room",
            "overall_action": "person reaches",
        },
        {
            "time_seconds": 2.0, "frame_id": "f2",
            "people": [{
                "local_id": "p2", "hair": "dark short", "clothing": ["blue jacket"],
                "held_objects": ["cup"], "action": "holding cup", "pose": "standing",
                "bbox": [0.30, 0.10, 0.20, 0.50], "confidence": 0.90,
            }],
            "objects": [], "camera_motion": "pan right", "setting": "room",
            "overall_action": "person holds cup",
        },
    ]
    tracks = m._entity_tracks(vision)
    events = m._temporal_transitions(vision, tracks)
    types = {e["transition_type"] for e in events}
    assert "screen_space_motion" in types
    assert "held_object_change" in types
    assert "entity_state_change" in types
    assert "scene_state_change" in types
    motion = next(e for e in events if e["transition_type"] == "screen_space_motion")
    assert motion["transition_window_seconds"] == {"start_seconds": 1.0, "end_seconds": 2.0}
    assert motion["observed_by_seconds"] == 2.0
    assert motion["delta"]["screen_direction"] == "right"
    camera = next(e for e in events if e["transition_type"] == "scene_state_change" and e["field"] == "camera_motion")
    assert camera["before"] == "static" and camera["after"] == "pan right"
    assert "exact change instant is not asserted" in camera["time_semantics"]
    m.shutdown()



def test_comparison_signatures_are_source_independent_and_multimodal(tmp_path):
    m = manager(tmp_path)
    vision = [
        {
            "time_seconds": 0.0,
            "setting": "living room",
            "lighting": "warm",
            "camera_shot": "medium",
            "camera_angle": "eye level",
            "camera_motion": "static",
            "overall_action": "person reaches for cup",
            "people": [{"ephemeral_track_id": "person-track-A"}],
            "objects": [{"ephemeral_track_id": "object-track-A"}],
        },
        {
            "time_seconds": 1.0,
            "setting": "living room",
            "lighting": "warm",
            "camera_shot": "medium",
            "camera_angle": "eye level",
            "camera_motion": "pan right",
            "overall_action": "person holds cup",
            "people": [{"ephemeral_track_id": "person-track-B"}],
            "objects": [{"ephemeral_track_id": "object-track-B"}],
        },
    ]
    tracks = [{
        "track_id": "person-track-A",
        "kind": "person",
        "trajectory": {
            "net_screen_direction": "right",
            "path_length_normalized": 0.3,
            "net_displacement_normalized": 0.2,
            "moving_step_count": 3,
            "measured_step_count": 4,
        },
    }]
    transitions = [
        {
            "transition_type": "screen_space_motion", "entity_kind": "person", "track_id": "person-track-A",
            "delta": {"screen_direction": "right", "speed_normalized_per_second": 0.4},
        },
        {
            "transition_type": "held_object_change", "entity_kind": "person", "track_id": "person-track-A",
            "field": "held_objects", "added": ["cup"], "removed": [],
        },
        {
            "transition_type": "scene_state_change", "field": "camera_motion",
            "before": "static", "after": "pan right",
        },
    ]
    segments = [{
        "text": "hello there",
        "delivery": {
            "word_rate_per_second": 1.5,
            "prosody": {"energy_band": "medium", "pace_band": "moderate", "pitch_dynamics": "variable"},
        },
    }]
    audio = {
        "tempo_bpm_hypothesis": 120,
        "chord_intervals": [{"chord": "C"}, {"chord": "G"}],
        "note_intervals": [{"note": "C4"}, {"note": "G4"}],
    }
    sig = m._comparison_signatures(vision, segments, audio, tracks, transitions)
    assert sig["schema_version"] == "media_cross_comparison_signature/v1"
    assert sig["signature"].startswith("duoid:shake256-512:")
    assert sig["token_count"] > 10
    assert "person-track-a" not in "\n".join(sig["tokens"])
    assert "person-track-b" not in "\n".join(sig["tokens"])
    assert any(x.startswith("person:net=right") for x in sig["families"]["motion"])
    assert any("held_object_change" in x for x in sig["families"]["state_change"])
    assert any("camera_motion" in x for x in sig["families"]["scene_change"])
    assert "word=hello" in sig["families"]["speech_text"]
    assert "pace_band=moderate" in sig["families"]["speech_prosody"]
    assert "chord=c" in sig["families"]["music"]
    assert "pitch_class=c" in sig["families"]["music"]
    assert sig["identity_semantics"].startswith("no_person_identity_claim")
    m.shutdown()


def test_comparison_signature_is_stable_across_ephemeral_track_ids(tmp_path):
    m = manager(tmp_path)
    vision = [{"time_seconds": 0.0, "setting": "room", "people": [], "objects": []}]
    base_track = {
        "kind": "person",
        "trajectory": {
            "net_screen_direction": "left",
            "path_length_normalized": 0.2,
            "net_displacement_normalized": 0.15,
            "moving_step_count": 2,
            "measured_step_count": 3,
        },
    }
    event = {
        "transition_type": "screen_space_motion",
        "entity_kind": "person",
        "delta": {"screen_direction": "left", "speed_normalized_per_second": 0.2},
    }
    a = m._comparison_signatures(
        vision, [], {"chord_intervals": [], "note_intervals": []},
        [{**base_track, "track_id": "person-track-0001"}],
        [{**event, "track_id": "person-track-0001"}],
    )
    b = m._comparison_signatures(
        vision, [], {"chord_intervals": [], "note_intervals": []},
        [{**base_track, "track_id": "person-track-9999"}],
        [{**event, "track_id": "person-track-9999"}],
    )
    assert a["signature"] == b["signature"]
    assert a["tokens"] == b["tokens"]
    m.shutdown()



def test_compare_signature_bundles_is_explainable_and_identity_safe(tmp_path):
    m = manager(tmp_path)
    left = {
        "signature": "duoid:shake256-512:left",
        "tokens": ["motion:person:net=right", "music:chord=c", "speech_text:word=hello"],
        "families": {
            "visual_context": [], "motion": ["person:net=right"], "state_change": [], "scene_change": [],
            "speech_text": ["word=hello"], "speech_prosody": [], "music": ["chord=c"],
        },
        "sequence_sketches": {"chords": ["c", "g", "c"], "transitions": ["motion:right", "state:hold"]},
    }
    right = {
        "signature": "duoid:shake256-512:right",
        "tokens": ["motion:person:net=right", "music:chord=c", "speech_text:word=world"],
        "families": {
            "visual_context": [], "motion": ["person:net=right"], "state_change": [], "scene_change": [],
            "speech_text": ["word=world"], "speech_prosody": [], "music": ["chord=c"],
        },
        "sequence_sketches": {"chords": ["c", "f", "c"], "transitions": ["motion:right", "state:release"]},
    }
    out = m._compare_signature_bundles(left, right)
    assert out["schema_version"] == "media_cross_comparison/v1"
    assert 0 < out["overall_similarity"] < 1
    assert out["family_overlap"]["motion"]["score"] == 1.0
    assert out["family_overlap"]["speech_text"]["score"] == 0.0
    assert out["sequence_overlap"]["chords"]["score"] > 0.5
    assert "motion:person:net=right" in out["common_tokens"]
    assert out["exact_normalized_signature_match"] is False
    assert out["identity_semantics"].startswith("not_person_identity_evidence")
    m.shutdown()


def test_compare_signature_bundles_exact_match_scores_one(tmp_path):
    m = manager(tmp_path)
    bundle = {
        "signature": "duoid:shake256-512:same",
        "tokens": ["motion:person:net=left"],
        "families": {
            "visual_context": [], "motion": ["person:net=left"], "state_change": [], "scene_change": [],
            "speech_text": [], "speech_prosody": [], "music": [],
        },
        "sequence_sketches": {"transitions": ["motion:left"]},
    }
    out = m._compare_signature_bundles(bundle, bundle)
    assert out["exact_normalized_signature_match"] is True
    assert out["overall_similarity"] == 1.0
    assert out["token_jaccard"] == 1.0
    m.shutdown()


def test_find_similar_jobs_ranks_exact_then_partial_and_excludes_query(tmp_path):
    m = manager(tmp_path)
    query_id = "mediarec-" + "1" * 24
    exact_id = "mediarec-" + "2" * 24
    partial_id = "mediarec-" + "3" * 24
    unrelated_id = "mediarec-" + "4" * 24

    def bundle(signature, tokens, motion):
        return {
            "schema_version": "media_cross_comparison_signature/v1",
            "signature": signature,
            "tokens": tokens,
            "families": {
                "visual_context": ["setting:room"],
                "motion": motion,
                "state_change": [],
                "scene_change": [],
                "speech_text": ["speech:hello"] if "hello" in tokens else [],
                "speech_prosody": [],
                "music": [],
            },
            "sequence_sketches": {"motion": motion},
        }

    records = {
        query_id: (100, "query.mp4", bundle("sig-same", ["hello", "room", "right"], ["right"])),
        exact_id: (90, "exact.mp4", bundle("sig-same", ["hello", "room", "right"], ["right"])),
        partial_id: (80, "partial.mp4", bundle("sig-partial", ["hello", "room"], ["right"])),
        unrelated_id: (70, "other.mp4", bundle("sig-other", ["outdoor"], ["left"])),
    }
    for job_id, (created, filename, sig) in records.items():
        root = tmp_path / job_id
        root.mkdir(parents=True)
        (root / "state.json").write_text(json.dumps({
            "job_id": job_id, "status": "completed", "created_at_ms": created,
            "filename": filename, "progress": 1.0,
        }))
        (root / "result.json").write_text(json.dumps({
            "analysis_profile": "full",
            "nodes": [{"label": filename, "witness": {"comparison_signatures": sig}}],
        }))

    out = m.find_similar_jobs(query_id, limit=3)
    assert out["schema_version"] == "media_similarity_search/v1"
    assert out["identity_semantics"].startswith("not_person_identity_evidence")
    assert out["query_job_id"] == query_id
    assert out["count"] == 3
    assert [row["job_id"] for row in out["matches"]] == [exact_id, partial_id, unrelated_id]
    assert out["matches"][0]["exact_normalized_signature_match"] is True
    assert out["matches"][0]["overall_similarity"] == 1.0
    assert out["matches"][1]["overall_similarity"] > out["matches"][2]["overall_similarity"]
    assert all(row["job_id"] != query_id for row in out["matches"])

    thresholded = m.find_similar_jobs(query_id, limit=10, min_similarity=0.5)
    assert exact_id in [row["job_id"] for row in thresholded["matches"]]
    assert unrelated_id not in [row["job_id"] for row in thresholded["matches"]]
    m.shutdown()



def test_compare_signature_bundles_excludes_unavailable_legacy_families(tmp_path):
    m = manager(tmp_path)
    families = {
        "visual_context": ["setting=room"],
        "motion": ["person:net=right"],
        "state_change": ["person:pose:sit>stand"],
        "scene_change": ["camera_motion:static>pan right"],
        "speech_text": ["word=hello"],
        "speech_prosody": ["pace_band=moderate"],
        "music": ["pitch_class=c"],
    }
    current = {
        "signature": "duoid:shake256-512:current",
        "tokens": [f"{family}:{token}" for family, values in families.items() for token in values],
        "families": families,
        "sequence_sketches": {"transitions": ["motion:right"], "pitch_classes": ["c"]},
        "evidence_coverage": {family: "observed" for family in families},
    }
    legacy = {
        "signature": "duoid:shake256-512:legacy",
        "tokens": ["visual_context:setting=room", "speech_text:word=hello", "speech_prosody:pace_band=moderate", "music:pitch_class=c"],
        "families": {
            "visual_context": ["setting=room"], "motion": [], "state_change": [], "scene_change": [],
            "speech_text": ["word=hello"], "speech_prosody": ["pace_band=moderate"], "music": ["pitch_class=c"],
        },
        "sequence_sketches": {"pitch_classes": ["c"]},
        "evidence_coverage": {
            "visual_context": "observed", "motion": "unavailable", "state_change": "unavailable", "scene_change": "unavailable",
            "speech_text": "observed", "speech_prosody": "observed", "music": "observed",
        },
    }
    out = m._compare_signature_bundles(current, legacy)
    assert set(out["comparison_coverage"]["excluded_families"]) == {"motion", "scene_change", "state_change"}
    assert out["family_overlap"]["motion"]["score"] is None
    assert out["family_overlap"]["motion"]["comparable"] is False
    assert out["sequence_overlap"]["transitions"]["score"] is None
    assert out["token_jaccard"] == 1.0
    assert out["family_weighted_similarity"] == 1.0
    assert out["sequence_similarity"] == 1.0
    assert out["overall_similarity"] == 1.0
    m.shutdown()


def test_compare_signature_bundles_observed_empty_is_not_unavailable(tmp_path):
    m = manager(tmp_path)
    left = {
        "signature": "left", "tokens": ["speech_text:word=hello"],
        "families": {"visual_context": [], "motion": [], "state_change": [], "scene_change": [], "speech_text": ["word=hello"], "speech_prosody": [], "music": []},
        "sequence_sketches": {},
        "evidence_coverage": {"speech_text": "observed"},
    }
    right = {
        "signature": "right", "tokens": [],
        "families": {"visual_context": [], "motion": [], "state_change": [], "scene_change": [], "speech_text": [], "speech_prosody": [], "music": []},
        "sequence_sketches": {},
        "evidence_coverage": {"speech_text": "observed"},
    }
    out = m._compare_signature_bundles(left, right)
    assert out["family_overlap"]["speech_text"]["comparable"] is True
    assert out["family_overlap"]["speech_text"]["score"] == 0.0
    m.shutdown()



def test_temporal_alignment_locates_best_target_window(tmp_path):
    m = manager(tmp_path)
    query_id = "mediarec-" + "a" * 24
    target_id = "mediarec-" + "b" * 24

    def frame(t, setting, action):
        return {"time_seconds": t, "frame_id": f"f{t}", "people": [], "objects": [], "setting": setting,
                "lighting": "daylight", "camera_shot": "wide", "camera_motion": "static",
                "visible_text": [], "overall_action": action, "confidence": 0.9}

    query_vision = [frame(10.0,"forest","running"), frame(10.8,"forest","running"), frame(11.6,"forest","running")]
    target_vision = [
        frame(0.0,"room","sitting"), frame(1.0,"room","sitting"), frame(2.0,"room","standing"),
        frame(3.0,"forest","running"), frame(4.0,"forest","running"), frame(5.0,"forest","running"),
        frame(6.0,"street","walking"), frame(7.0,"street","walking"), frame(8.0,"street","walking"),
    ]
    empty_audio = {"frames": [], "onsets": [], "note_intervals": [], "chord_intervals": [], "tempo_bpm_hypothesis": None,
                   "transcript": {"segments": [], "words": [], "text": "", "language": None}}

    def write_job(job_id, label, vision, start, end):
        root=tmp_path/job_id; root.mkdir()
        tracks=m._entity_tracks(vision); transitions=m._temporal_transitions(vision,tracks)
        sig=m._comparison_signatures(vision,[],empty_audio,tracks,transitions)
        reconstruction={"analysis_range":{"start_seconds":start,"end_seconds":end,"duration_seconds":end-start,"profile":"forensic_range"},
                        "source_clock":{"duration_seconds":end},
                        "visual":{"semantic_anchors":vision,"entity_tracks":tracks,"temporal_transitions":transitions},
                        "audio":empty_audio}
        result={"nodes":[{"label":label,"witness":{"reconstruction":reconstruction,"comparison_signatures":sig}}]}
        (root/"state.json").write_text(json.dumps({"job_id":job_id,"status":"completed","filename":label,"created_at_ms":1}))
        (root/"result.json").write_text(json.dumps(result))

    write_job(query_id,"query.mp4",query_vision,10.0,12.0)
    write_job(target_id,"target.mp4",target_vision,0.0,8.0)
    out=m.align_jobs(query_id,target_id,window_seconds=2.0,step_seconds=0.5,limit=4)
    assert out["schema_version"] == "media_temporal_alignment/v1"
    assert out["matches"]
    best=out["matches"][0]
    assert 2.5 <= best["start_seconds"] <= 4.0, best
    assert best["overall_similarity"] > 0.45, best
    assert out["windows_scanned"] >= 10
    m.shutdown()


def test_temporal_alignment_defaults_window_to_query_duration(tmp_path):
    m = manager(tmp_path)
    # Validate the explicit guard independently; full ranking is covered above.
    reconstruction={"analysis_range":{"start_seconds":1.0,"end_seconds":3.5},"visual":{"semantic_anchors":[]},
                    "audio":{"transcript":{"segments":[]},"note_intervals":[],"chord_intervals":[]}}
    sig=m._window_signature_from_reconstruction(reconstruction,start_seconds=1.0,end_seconds=3.5)
    assert sig["window"]["duration_seconds"] == 2.5
    assert sig["evidence_coverage"]["motion"] == "unavailable"
    m.shutdown()


def test_measured_alignment_similarity_peaks_at_matching_signal_window(tmp_path):
    m = manager(tmp_path)
    query = {
        "visual": {"deterministic_samples": [
            {"time_seconds": 10.0, "mean_luma": 10.0, "change_score": 0.0},
            {"time_seconds": 10.5, "mean_luma": 35.0, "change_score": 18.0},
            {"time_seconds": 11.0, "mean_luma": 18.0, "change_score": 4.0},
            {"time_seconds": 11.5, "mean_luma": 42.0, "change_score": 24.0},
            {"time_seconds": 12.0, "mean_luma": 22.0, "change_score": 6.0},
        ]},
        "audio": {"frames": [
            {"time_seconds": 10.0, "rms": 0.05, "spectral_centroid_hz": 800.0, "spectral_flux": 0.02},
            {"time_seconds": 10.5, "rms": 0.20, "spectral_centroid_hz": 1600.0, "spectral_flux": 0.25},
            {"time_seconds": 11.0, "rms": 0.08, "spectral_centroid_hz": 950.0, "spectral_flux": 0.05},
            {"time_seconds": 11.5, "rms": 0.23, "spectral_centroid_hz": 1800.0, "spectral_flux": 0.30},
            {"time_seconds": 12.0, "rms": 0.09, "spectral_centroid_hz": 1000.0, "spectral_flux": 0.06},
        ]},
    }
    target = {
        "visual": {"deterministic_samples": [
            {"time_seconds": 0.0, "mean_luma": 45.0, "change_score": 22.0},
            {"time_seconds": 0.5, "mean_luma": 20.0, "change_score": 3.0},
            {"time_seconds": 1.0, "mean_luma": 40.0, "change_score": 20.0},
            {"time_seconds": 1.5, "mean_luma": 15.0, "change_score": 2.0},
            {"time_seconds": 2.0, "mean_luma": 38.0, "change_score": 18.0},
            {"time_seconds": 3.0, "mean_luma": 10.0, "change_score": 0.0},
            {"time_seconds": 3.5, "mean_luma": 35.0, "change_score": 18.0},
            {"time_seconds": 4.0, "mean_luma": 18.0, "change_score": 4.0},
            {"time_seconds": 4.5, "mean_luma": 42.0, "change_score": 24.0},
            {"time_seconds": 5.0, "mean_luma": 22.0, "change_score": 6.0},
        ]},
        "audio": {"frames": [
            {"time_seconds": 0.0, "rms": 0.22, "spectral_centroid_hz": 1700.0, "spectral_flux": 0.28},
            {"time_seconds": 0.5, "rms": 0.08, "spectral_centroid_hz": 900.0, "spectral_flux": 0.04},
            {"time_seconds": 1.0, "rms": 0.19, "spectral_centroid_hz": 1500.0, "spectral_flux": 0.20},
            {"time_seconds": 1.5, "rms": 0.07, "spectral_centroid_hz": 850.0, "spectral_flux": 0.03},
            {"time_seconds": 2.0, "rms": 0.18, "spectral_centroid_hz": 1450.0, "spectral_flux": 0.19},
            {"time_seconds": 3.0, "rms": 0.05, "spectral_centroid_hz": 800.0, "spectral_flux": 0.02},
            {"time_seconds": 3.5, "rms": 0.20, "spectral_centroid_hz": 1600.0, "spectral_flux": 0.25},
            {"time_seconds": 4.0, "rms": 0.08, "spectral_centroid_hz": 950.0, "spectral_flux": 0.05},
            {"time_seconds": 4.5, "rms": 0.23, "spectral_centroid_hz": 1800.0, "spectral_flux": 0.30},
            {"time_seconds": 5.0, "rms": 0.09, "spectral_centroid_hz": 1000.0, "spectral_flux": 0.06},
        ]},
    }
    wrong = m._measured_alignment_similarity(
        query, target,
        query_start_seconds=10.0, query_end_seconds=12.0,
        target_start_seconds=0.0, target_end_seconds=2.0,
    )
    right = m._measured_alignment_similarity(
        query, target,
        query_start_seconds=10.0, query_end_seconds=12.0,
        target_start_seconds=3.0, target_end_seconds=5.0,
    )
    assert right["schema_version"] == "media_measured_temporal_alignment/v1"
    assert right["score"] > 0.99, right
    assert right["score"] > wrong["score"] + 0.2, (right, wrong)
    assert set(right["modalities_used"]) == {"video", "audio"}
    assert right["video"]["fields"]["mean_luma"]["correlation"] > 0.99
    m.shutdown()


def test_refine_from_job_reuses_retained_source_with_lineage(tmp_path, monkeypatch):
    m = manager(tmp_path)
    parent_id = "mediarec-" + "a" * 24
    parent = tmp_path / parent_id
    parent.mkdir(parents=True)
    source = parent / "source.mp4"
    source.write_bytes(b"retained-source-bytes")
    (parent / "state.json").write_text(json.dumps({
        "schema_version": "media_reconstruction_witness/v1",
        "job_id": parent_id,
        "status": "completed",
        "stage": "completed",
        "progress": 1.0,
        "filename": "parent.mp4",
        "mime_type": "video/mp4",
        "source_bytes": source.stat().st_size,
        "created_at_ms": 1,
    }))

    submitted = {}
    class DummyFuture:
        def cancel(self): return False
    def fake_submit(*args):
        submitted["args"] = args
        return DummyFuture()
    monkeypatch.setattr(m.executor, "submit", fake_submit)

    child = m.refine_from_job(
        parent_id,
        range_start_seconds=1.25,
        range_end_seconds=2.75,
        analysis_profile="forensic_range",
    )
    child_root = tmp_path / child["job_id"]
    child_source = next(p for p in child_root.iterdir() if p.name.startswith("source"))
    assert child_source.read_bytes() == b"retained-source-bytes"
    assert child["parent_job_id"] == parent_id
    assert child["lineage"]["relation"] == "retained_source_refinement"
    assert child["lineage"]["requested_range"] == {
        "start_seconds": 1.25,
        "end_seconds": 2.75,
        "analysis_profile": "forensic_range",
    }
    assert child["lineage"]["source_reuse"] in {"hardlink", "copy"}
    options = submitted["args"][-1]
    assert options["range_start_seconds"] == 1.25
    assert options["range_end_seconds"] == 2.75
    assert options["analysis_profile"] == "forensic_range"

    shutil.rmtree(parent)
    assert child_source.read_bytes() == b"retained-source-bytes"
    m.shutdown()


def test_refine_from_job_rejects_missing_source_and_invalid_range(tmp_path, monkeypatch):
    m = manager(tmp_path)
    parent_id = "mediarec-" + "b" * 24
    parent = tmp_path / parent_id
    parent.mkdir(parents=True)
    (parent / "state.json").write_text(json.dumps({
        "schema_version": "media_reconstruction_witness/v1",
        "job_id": parent_id,
        "status": "completed",
        "stage": "completed",
        "progress": 1.0,
        "filename": "parent.mp4",
        "mime_type": "video/mp4",
        "source_bytes": 0,
        "created_at_ms": 1,
    }))
    try:
        m.refine_from_job(parent_id, range_start_seconds=1.0, range_end_seconds=2.0)
        assert False, "expected missing retained source"
    except RuntimeError as exc:
        assert str(exc) == "media_reconstruction_retained_source_missing"

    source = parent / "source.mp4"
    source.write_bytes(b"x")
    try:
        m.refine_from_job(parent_id, range_start_seconds=2.0, range_end_seconds=2.01)
        assert False, "expected invalid range"
    except ValueError as exc:
        assert str(exc) == "media_reconstruction_invalid_range"
    m.shutdown()


def test_run_job_embeds_retained_refinement_lineage_in_result_and_witness(tmp_path, monkeypatch):
    m = manager(tmp_path)
    job_id = "mediarec-" + "c" * 24
    parent_id = "mediarec-" + "d" * 24
    root = tmp_path / job_id
    root.mkdir(parents=True)
    source = root / "source.mp4"
    source.write_bytes(b"child-source")
    lineage = {
        "schema_version": "media_reconstruction_lineage/v1",
        "relation": "retained_source_refinement",
        "parent_job_id": parent_id,
        "source_reuse": "hardlink",
        "requested_range": {
            "start_seconds": 1.0,
            "end_seconds": 3.0,
            "analysis_profile": "forensic_range",
        },
    }
    (root / "state.json").write_text(json.dumps({
        "schema_version": "media_reconstruction_witness/v1",
        "job_id": job_id,
        "status": "queued",
        "stage": "queued",
        "progress": 0.0,
        "filename": "child.mp4",
        "mime_type": "video/mp4",
        "source_bytes": source.stat().st_size,
        "created_at_ms": 1,
        "parent_job_id": parent_id,
        "lineage": lineage,
    }))

    monkeypatch.setattr(m, "analyze", lambda *args, **kwargs: {
        "schema_version": "test-result/v1",
        "nodes": [{"id": "n1", "witness": {"source": {"filename": "child.mp4"}}}],
        "summary": {"item_count": 1},
    })
    m._run_job(job_id, source, "child.mp4", "video/mp4", {})
    result = json.loads((root / "result.json").read_text())
    assert result["parent_job_id"] == parent_id
    assert result["lineage"] == lineage
    assert result["nodes"][0]["witness"]["lineage"] == lineage
    assert result["nodes"][0]["witness"]["source"]["lineage"] == lineage
    assert json.loads((root / "state.json").read_text())["status"] == "completed"
    m.shutdown()


def test_investigation_graph_persists_relationships_and_lineage_with_tombstone(tmp_path):
    m = manager(tmp_path)
    parent_id = "mediarec-" + "1" * 24
    child_id = "mediarec-" + "2" * 24
    for job_id, created in ((parent_id, 10), (child_id, 20)):
        root = tmp_path / job_id
        root.mkdir(parents=True)
        state = {
            "schema_version": "media_reconstruction_witness/v1",
            "job_id": job_id,
            "status": "completed",
            "stage": "completed",
            "progress": 1.0,
            "filename": job_id + ".mp4",
            "mime_type": "video/mp4",
            "source_bytes": 1,
            "created_at_ms": created,
        }
        if job_id == child_id:
            state["parent_job_id"] = parent_id
            state["lineage"] = {
                "schema_version": "media_reconstruction_lineage/v1",
                "relation": "retained_source_refinement",
                "parent_job_id": parent_id,
                "source_reuse": "hardlink",
                "requested_range": {"start_seconds": 1.0, "end_seconds": 2.0, "analysis_profile": "forensic_range"},
            }
        (root / "state.json").write_text(json.dumps(state))

    first = m._record_relationship(
        relation_type="temporal_alignment",
        source_job_id=child_id,
        target_job_id=parent_id,
        relationship_key="test-alignment",
        authority="measured_temporal_alignment_plus_heuristic_semantic_evidence",
        evidence={"best_match": {"start_seconds": 1.0, "end_seconds": 2.0, "overall_similarity": 0.9}},
    )
    second = m._record_relationship(
        relation_type="temporal_alignment",
        source_job_id=child_id,
        target_job_id=parent_id,
        relationship_key="test-alignment",
        authority="measured_temporal_alignment_plus_heuristic_semantic_evidence",
        evidence={"best_match": {"start_seconds": 1.0, "end_seconds": 2.0, "overall_similarity": 0.91}},
    )
    assert first["relation_id"] == second["relation_id"]
    assert second["observation_count"] == 2

    graph = m.investigation_graph(limit=20)
    kinds = [edge["relation_type"] for edge in graph["edges"]]
    assert "retained_source_refinement" in kinds
    assert "temporal_alignment" in kinds
    rel = next(edge for edge in graph["edges"] if edge["relation_type"] == "temporal_alignment")
    assert rel["observation_count"] == 2
    assert rel["evidence"]["best_match"]["overall_similarity"] == 0.91

    shutil.rmtree(tmp_path / parent_id)
    graph = m.investigation_graph(limit=20)
    parent = next(node for node in graph["nodes"] if node["job_id"] == parent_id)
    assert parent["tombstone"] is True
    assert parent["status"] == "missing_or_deleted"
    assert any(edge["relation_type"] == "retained_source_refinement" and edge["source_job_id"] == parent_id for edge in graph["edges"])
    m.shutdown()


def test_compare_jobs_records_deduplicated_investigation_relationship(tmp_path, monkeypatch):
    m = manager(tmp_path)
    monkeypatch.setattr(m, "result", lambda job_id: {"nodes": [{"label": job_id}]})
    monkeypatch.setattr(m, "_comparison_signature_from_result", lambda result: {"signature": "sig"})
    monkeypatch.setattr(m, "_compare_signature_bundles", lambda left, right: {
        "authority": "heuristic_similarity_evidence_only",
        "overall_similarity": 0.75,
        "token_jaccard": 0.5,
        "family_weighted_similarity": 0.7,
        "sequence_similarity": 0.8,
    })
    a = "mediarec-" + "3" * 24
    b = "mediarec-" + "4" * 24
    m.compare_jobs(a, b)
    m.compare_jobs(b, a)
    rows = m._relationship_store()["relationships"]
    assert len(rows) == 1
    assert rows[0]["relation_type"] == "cross_media_comparison"
    assert rows[0]["observation_count"] == 2
    m.shutdown()


def test_atomic_json_supports_concurrent_writers(tmp_path):
    import json
    import threading
    from duotronic_runtime.media_reconstruction import _atomic_json

    path = tmp_path / "state.json"
    errors = []
    barrier = threading.Barrier(12)

    def writer(index):
        try:
            barrier.wait(timeout=2)
            for seq in range(40):
                _atomic_json(path, {"writer": index, "seq": seq, "payload": "x" * 128})
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(12)]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=10)
    assert not errors, errors
    assert all(not thread.is_alive() for thread in threads)
    result = json.loads(path.read_text())
    assert 0 <= int(result["writer"]) < 12
    assert 0 <= int(result["seq"]) < 40
    assert not list(tmp_path.glob("state.json.*.tmp"))



def test_window_signature_uses_only_timed_words_inside_window(tmp_path):
    m = manager(tmp_path)
    words = [
        {"word": " alpha", "start_seconds": 0.1, "end_seconds": 0.6, "segment_index": 0, "word_index": 0, "probability": 0.9},
        {"word": " beta", "start_seconds": 1.1, "end_seconds": 1.6, "segment_index": 0, "word_index": 1, "probability": 0.9},
        {"word": " gamma", "start_seconds": 2.1, "end_seconds": 2.6, "segment_index": 0, "word_index": 2, "probability": 0.9},
    ]
    reconstruction = {
        "analysis_range": {"start_seconds": 0.0, "end_seconds": 3.0},
        "visual": {"semantic_anchors": []},
        "audio": {
            "frames": [
                {"time_seconds": 0.25, "rms": 0.02, "spectral_centroid_hz": 500.0, "spectral_flux": 0.01, "pitch_hz": 100.0},
                {"time_seconds": 1.25, "rms": 0.18, "spectral_centroid_hz": 1500.0, "spectral_flux": 0.20, "pitch_hz": 260.0},
                {"time_seconds": 1.50, "rms": 0.20, "spectral_centroid_hz": 1600.0, "spectral_flux": 0.24, "pitch_hz": 340.0},
                {"time_seconds": 2.25, "rms": 0.04, "spectral_centroid_hz": 800.0, "spectral_flux": 0.03, "pitch_hz": 130.0},
            ],
            "transcript": {
                "text": "alpha beta gamma",
                "words": words,
                "segments": [{
                    "segment_index": 0, "text": "alpha beta gamma", "start_seconds": 0.0, "end_seconds": 3.0,
                    "words": words,
                    "delivery": {"prosody": {"energy_band": "moderate", "pace_band": "moderate", "pitch_dynamics": "steady"}},
                }],
            },
            "note_intervals": [],
            "chord_intervals": [],
            "onsets": [],
            "tempo_bpm_hypothesis": 120.0,
        },
    }
    sig = m._window_signature_from_reconstruction(reconstruction, start_seconds=1.0, end_seconds=2.0)
    speech = sig["families"]["speech_text"]
    assert "word=beta" in speech
    assert "word=alpha" not in speech
    assert "word=gamma" not in speech
    assert sig["window_evidence"]["transcript_text"] == "beta"
    assert sig["window_evidence"]["word_count"] == 1
    assert sig["window_evidence"]["text_timing"] == "word_timestamps"
    # Global source tempo must not leak into a window with no local onset estimate.
    assert sig["window_evidence"]["tempo_bpm_hypothesis"] is None
    assert not any(token.startswith("tempo=") for token in sig["families"]["music"])
    m.shutdown()


def test_window_signature_recomputes_local_prosody_from_window_audio(tmp_path):
    m = manager(tmp_path)
    words = [
        {"word": " low", "start_seconds": 0.1, "end_seconds": 0.7, "segment_index": 0, "word_index": 0, "probability": 0.9},
        {"word": " high", "start_seconds": 1.1, "end_seconds": 1.7, "segment_index": 0, "word_index": 1, "probability": 0.9},
    ]
    reconstruction = {
        "analysis_range": {"start_seconds": 0.0, "end_seconds": 2.0},
        "visual": {"semantic_anchors": []},
        "audio": {
            "frames": [
                {"time_seconds": 0.2, "rms": 0.01, "spectral_centroid_hz": 400.0, "spectral_flux": 0.01, "pitch_hz": 100.0},
                {"time_seconds": 0.5, "rms": 0.02, "spectral_centroid_hz": 500.0, "spectral_flux": 0.01, "pitch_hz": 102.0},
                {"time_seconds": 1.2, "rms": 0.18, "spectral_centroid_hz": 1700.0, "spectral_flux": 0.22, "pitch_hz": 180.0},
                {"time_seconds": 1.5, "rms": 0.22, "spectral_centroid_hz": 1900.0, "spectral_flux": 0.30, "pitch_hz": 420.0},
            ],
            "transcript": {
                "words": words,
                "segments": [{"segment_index": 0, "text": "low high", "start_seconds": 0.0, "end_seconds": 2.0, "words": words,
                              "delivery": {"prosody": {"energy_band": "moderate", "pace_band": "moderate", "pitch_dynamics": "steady"}}}],
            },
            "note_intervals": [], "chord_intervals": [], "onsets": [],
        },
    }
    low = m._window_signature_from_reconstruction(reconstruction, start_seconds=0.0, end_seconds=0.9)
    high = m._window_signature_from_reconstruction(reconstruction, start_seconds=1.0, end_seconds=1.9)
    assert "energy_band=low" in low["families"]["speech_prosody"], low
    assert "energy_band=high" in high["families"]["speech_prosody"], high
    assert "word=low" in low["families"]["speech_text"] and "word=high" not in low["families"]["speech_text"]
    assert "word=high" in high["families"]["speech_text"] and "word=low" not in high["families"]["speech_text"]
    m.shutdown()


def test_window_signature_clips_note_and_chord_intervals(tmp_path):
    m = manager(tmp_path)
    reconstruction = {
        "analysis_range": {"start_seconds": 0.0, "end_seconds": 3.0},
        "visual": {"semantic_anchors": []},
        "audio": {
            "frames": [], "transcript": {"segments": [], "words": []},
            "note_intervals": [{"note": "C4", "start_seconds": 0.5, "end_seconds": 1.5}],
            "chord_intervals": [{"chord": "C:maj", "start_seconds": 1.5, "end_seconds": 2.5}],
            "onsets": [1.05, 1.55, 2.05],
            "tempo_bpm_hypothesis": 90.0,
        },
    }
    sig = m._window_signature_from_reconstruction(reconstruction, start_seconds=1.0, end_seconds=2.0)
    ev = sig["window_evidence"]
    assert ev["notes"][0]["start_seconds"] == 1.0
    assert ev["notes"][0]["end_seconds"] == 1.5
    assert ev["notes"][0]["overlap_fraction"] == 0.5
    assert ev["chords"][0]["start_seconds"] == 1.5
    assert ev["chords"][0]["end_seconds"] == 2.0
    assert ev["chords"][0]["overlap_fraction"] == 0.5
    assert ev["tempo_bpm_hypothesis"] == 120.0
    assert "tempo=mid_fast" in sig["families"]["music"]
    m.shutdown()



def test_temporal_alignment_explicit_query_range_locates_selected_motif(tmp_path):
    m = manager(tmp_path)
    query_id = "mediarec-" + "e" * 24
    target_id = "mediarec-" + "f" * 24

    def frame(t, setting, action):
        return {"time_seconds": t, "frame_id": f"f{t}", "people": [], "objects": [], "setting": setting,
                "lighting": "daylight", "camera_shot": "wide", "camera_motion": "static",
                "visible_text": [], "overall_action": action, "confidence": 0.9}

    query_vision = [
        frame(10.0, "room", "sitting"), frame(11.0, "room", "standing"),
        frame(12.0, "forest", "running"), frame(13.0, "forest", "running"), frame(14.0, "forest", "running"),
    ]
    target_vision = [
        frame(0.0, "street", "walking"), frame(1.0, "street", "walking"), frame(2.0, "street", "walking"),
        frame(3.0, "forest", "running"), frame(4.0, "forest", "running"), frame(5.0, "forest", "running"),
        frame(6.0, "room", "sitting"), frame(7.0, "room", "standing"), frame(8.0, "room", "standing"),
    ]
    empty_audio = {"frames": [], "onsets": [], "note_intervals": [], "chord_intervals": [],
                   "tempo_bpm_hypothesis": None, "transcript": {"segments": [], "words": [], "text": ""}}

    def write_job(job_id, label, vision, start, end):
        root = tmp_path / job_id
        root.mkdir()
        tracks = m._entity_tracks(vision)
        transitions = m._temporal_transitions(vision, tracks)
        sig = m._comparison_signatures(vision, [], empty_audio, tracks, transitions)
        reconstruction = {
            "analysis_range": {"start_seconds": start, "end_seconds": end, "duration_seconds": end-start, "profile": "forensic_range"},
            "source_clock": {"duration_seconds": end},
            "visual": {"semantic_anchors": vision, "entity_tracks": tracks, "temporal_transitions": transitions},
            "audio": empty_audio,
        }
        result = {"nodes": [{"label": label, "witness": {"reconstruction": reconstruction, "comparison_signatures": sig}}]}
        (root / "state.json").write_text(json.dumps({"job_id": job_id, "status": "completed", "filename": label, "created_at_ms": 1}))
        (root / "result.json").write_text(json.dumps(result))

    write_job(query_id, "query-long.mp4", query_vision, 10.0, 14.0)
    write_job(target_id, "target.mp4", target_vision, 0.0, 8.0)

    out = m.align_jobs(
        query_id, target_id,
        query_start_seconds=12.0, query_end_seconds=14.0,
        window_seconds=2.0, step_seconds=0.5, limit=4,
    )
    assert out["query_range"]["scope"] == "explicit_selection"
    assert out["query_range"]["start_seconds"] == 12.0
    assert out["query_range"]["end_seconds"] == 14.0
    assert out["query_window_evidence"] is not None
    best = out["matches"][0]
    assert 2.5 <= best["start_seconds"] <= 4.0, best
    assert best["overall_similarity"] > 0.45, best
    m.shutdown()


def test_temporal_alignment_rejects_query_range_outside_retained_analysis(tmp_path):
    m = manager(tmp_path)
    query_id = "mediarec-" + "1" * 24
    target_id = "mediarec-" + "2" * 24
    empty = {
        "analysis_range": {"start_seconds": 2.0, "end_seconds": 4.0},
        "source_clock": {"duration_seconds": 5.0},
        "visual": {"semantic_anchors": []},
        "audio": {"frames": [], "transcript": {"segments": [], "words": []}, "note_intervals": [], "chord_intervals": [], "onsets": []},
    }
    for job_id in (query_id, target_id):
        root = tmp_path / job_id
        root.mkdir()
        (root / "state.json").write_text(json.dumps({"job_id": job_id, "status": "completed", "filename": "x.mp4", "created_at_ms": 1}))
        (root / "result.json").write_text(json.dumps({"nodes": [{"label": "x.mp4", "witness": {"reconstruction": empty}}]}))
    import pytest
    with pytest.raises(ValueError, match="outside_retained_analysis"):
        m.align_jobs(query_id, target_id, query_start_seconds=1.0, query_end_seconds=3.0)
    with pytest.raises(ValueError, match="requires_start_and_end"):
        m.align_jobs(query_id, target_id, query_start_seconds=2.5)
    m.shutdown()



def test_motif_catalog_extracts_repeated_multimodal_pattern(tmp_path):
    m = manager(tmp_path)

    def frame(t, setting, action):
        return {
            "time_seconds": t, "frame_id": f"f{t}", "people": [], "objects": [],
            "setting": setting, "lighting": "daylight", "camera_shot": "wide",
            "camera_motion": "static", "visible_text": [], "overall_action": action, "confidence": 0.9,
        }

    vision = [
        frame(0.0, "forest", "running"), frame(0.5, "forest", "running"), frame(1.0, "room", "sitting"),
        frame(2.0, "street", "walking"),
        frame(3.0, "forest", "running"), frame(3.5, "forest", "running"), frame(4.0, "room", "sitting"),
        frame(5.0, "street", "walking"),
    ]
    tracks = m._entity_tracks(vision)
    transitions = m._temporal_transitions(vision, tracks)
    words = [
        {"word": " hey", "start_seconds": 0.1, "end_seconds": 0.4, "segment_index": 0, "word_index": 0, "probability": 0.9},
        {"word": " now", "start_seconds": 0.45, "end_seconds": 0.75, "segment_index": 0, "word_index": 1, "probability": 0.9},
        {"word": " hey", "start_seconds": 3.1, "end_seconds": 3.4, "segment_index": 1, "word_index": 0, "probability": 0.9},
        {"word": " now", "start_seconds": 3.45, "end_seconds": 3.75, "segment_index": 1, "word_index": 1, "probability": 0.9},
    ]
    segments = [
        {"segment_index": 0, "text": "hey now", "start_seconds": 0.1, "end_seconds": 0.75, "words": words[:2], "delivery": {"prosody": {"pace_band": "moderate", "energy_band": "moderate", "pitch_dynamics": "steady"}}},
        {"segment_index": 1, "text": "hey now", "start_seconds": 3.1, "end_seconds": 3.75, "words": words[2:], "delivery": {"prosody": {"pace_band": "moderate", "energy_band": "moderate", "pitch_dynamics": "steady"}}},
    ]
    deterministic = []
    audio_frames = []
    for t in [x * 0.25 for x in range(21)]:
        phase = t % 3.0
        repeated = phase <= 1.0
        deterministic.append({"time_seconds": t, "mean_luma": 25.0 if repeated else 70.0, "change_score": 10.0 if repeated else 2.0})
        audio_frames.append({"time_seconds": t, "rms": 0.18 if repeated else 0.03, "spectral_centroid_hz": 1200.0 if repeated else 500.0, "spectral_flux": 0.20 if repeated else 0.02})
    audio = {
        "frames": audio_frames,
        "onsets": [0.0, 0.5, 1.0, 3.0, 3.5, 4.0],
        "note_intervals": [
            {"note": "C4", "start_seconds": 0.0, "end_seconds": 0.45},
            {"note": "E4", "start_seconds": 0.5, "end_seconds": 0.95},
            {"note": "C4", "start_seconds": 3.0, "end_seconds": 3.45},
            {"note": "E4", "start_seconds": 3.5, "end_seconds": 3.95},
        ],
        "chord_intervals": [],
        "tempo_bpm_hypothesis": 120.0,
        "transcript": {"text": "hey now hey now", "words": words, "segments": segments},
    }
    reconstruction = {
        "analysis_range": {"start_seconds": 0.0, "end_seconds": 5.0, "duration_seconds": 5.0},
        "source_clock": {"duration_seconds": 5.0, "source_fps": 24.0},
        "visual": {
            "deterministic_samples": deterministic,
            "semantic_anchors": vision,
            "entity_tracks": tracks,
            "temporal_transitions": transitions,
        },
        "audio": audio,
    }
    catalog = m._motif_catalog(reconstruction, max_candidates=220, min_similarity=0.66)
    assert catalog["schema_version"] == "media_motif_catalog/v1"
    assert catalog["motif_count"] >= 1, catalog
    recurrent = [row for row in catalog["motifs"] if row["occurrence_count"] >= 2]
    assert recurrent
    best = recurrent[0]
    assert best["prototype"]["signature"].startswith("duoid:shake256-512:")
    assert best["identity_semantics"].startswith("not_person_identity_evidence")
    assert all(occ["source_time_semantics"] == "absolute_source_clock" for occ in best["occurrences"])
    assert all(
        m._motif_overlap_ratio(a, b) < 0.35 + 1e-9
        for i, a in enumerate(best["occurrences"])
        for b in best["occurrences"][i + 1:]
    )
    assert catalog["relationship_count"] >= best["occurrence_count"] - 1
    m.shutdown()


def test_motif_catalog_retains_salient_singleton_candidates(tmp_path):
    m = manager(tmp_path)
    vision = [
        {"time_seconds": 0.0, "frame_id": "a", "people": [], "objects": [], "setting": "room", "lighting": "dark",
         "camera_shot": "wide", "camera_motion": "static", "visible_text": [], "overall_action": "still", "confidence": 0.9},
        {"time_seconds": 1.0, "frame_id": "b", "people": [], "objects": [], "setting": "stage", "lighting": "bright",
         "camera_shot": "close", "camera_motion": "zoom", "visible_text": ["HELLO"], "overall_action": "flash", "confidence": 0.9},
        {"time_seconds": 2.0, "frame_id": "c", "people": [], "objects": [], "setting": "street", "lighting": "daylight",
         "camera_shot": "wide", "camera_motion": "pan", "visible_text": [], "overall_action": "walking", "confidence": 0.9},
    ]
    tracks = m._entity_tracks(vision)
    transitions = m._temporal_transitions(vision, tracks)
    reconstruction = {
        "analysis_range": {"start_seconds": 0.0, "end_seconds": 2.0, "duration_seconds": 2.0},
        "source_clock": {"duration_seconds": 2.0},
        "visual": {"deterministic_samples": [], "semantic_anchors": vision, "entity_tracks": tracks, "temporal_transitions": transitions},
        "audio": {"frames": [], "onsets": [], "note_intervals": [], "chord_intervals": [], "transcript": {"words": [], "segments": []}},
    }
    catalog = m._motif_catalog(reconstruction, max_candidates=80, min_similarity=0.95)
    assert catalog["salient_candidate_count"] >= 1
    assert all(row["status"] == "salient_singleton_candidate" for row in catalog["salient_candidates"])
    m.shutdown()


def test_motif_catalog_detects_periodic_recurrence(tmp_path):
    m = manager(tmp_path)
    words = []
    segments = []
    for idx, base in enumerate((0.0, 2.0, 4.0)):
        ws = [
            {"word": " ping", "start_seconds": base + 0.05, "end_seconds": base + 0.25, "segment_index": idx, "word_index": 0, "probability": 0.95},
            {"word": " pong", "start_seconds": base + 0.30, "end_seconds": base + 0.55, "segment_index": idx, "word_index": 1, "probability": 0.95},
        ]
        words.extend(ws)
        segments.append({"segment_index": idx, "text": "ping pong", "start_seconds": base + 0.05, "end_seconds": base + 0.55, "words": ws,
                         "delivery": {"prosody": {"pace_band": "moderate", "energy_band": "moderate", "pitch_dynamics": "steady"}}})
    audio = {
        "frames": [], "onsets": [0.0, 0.5, 2.0, 2.5, 4.0, 4.5], "note_intervals": [], "chord_intervals": [],
        "transcript": {"text": "ping pong ping pong ping pong", "words": words, "segments": segments},
    }
    reconstruction = {
        "analysis_range": {"start_seconds": 0.0, "end_seconds": 5.0, "duration_seconds": 5.0},
        "source_clock": {"duration_seconds": 5.0},
        "visual": {"deterministic_samples": [], "semantic_anchors": [], "entity_tracks": [], "temporal_transitions": []},
        "audio": audio,
    }
    catalog = m._motif_catalog(reconstruction, max_candidates=180, min_similarity=0.60)
    periodic = [row for row in catalog["motifs"] if (row.get("periodicity") or {}).get("classification") == "periodic"]
    assert periodic, catalog
    assert max(row["occurrence_count"] for row in periodic) >= 3
    m.shutdown()



def test_motif_prototype_similarity_prefers_matching_structure(tmp_path):
    m = manager(tmp_path)
    base = {
        "schema_version": "media_cross_comparison_signature/v1",
        "families": {
            "visual_context": ["setting=forest", "overall_action=running"],
            "motion": ["person:net=right"],
            "state_change": [], "scene_change": [], "speech_text": ["word=hey"],
            "speech_prosody": [], "music": ["note=c4", "pitch_class=c"],
        },
        "tokens": ["setting=forest", "overall_action=running", "person:net=right", "word=hey", "note=c4", "pitch_class=c"],
        "sequence_sketches": {"pitch_classes": ["c", "e", "g"]},
        "evidence_coverage": {"visual_context": "observed", "motion": "observed", "state_change": "observed", "scene_change": "observed", "speech_text": "observed", "speech_prosody": "observed", "music": "observed"},
        "measured_sketch": {"audio_rms": {"mean": 0.15, "stddev": 0.02}, "onset_rate_hz": 2.0},
    }
    same = json.loads(json.dumps(base))
    same["families"]["visual_context"] = ["setting=forest", "overall_action=running"]
    other = json.loads(json.dumps(base))
    other["families"]["visual_context"] = ["setting=office", "overall_action=sitting"]
    other["families"]["motion"] = ["person:net=stationary_or_below_resolution"]
    other["families"]["speech_text"] = ["word=goodbye"]
    other["families"]["music"] = ["note=f#5", "pitch_class=f#"]
    other["tokens"] = [token for values in other["families"].values() for token in values]
    other["measured_sketch"] = {"audio_rms": {"mean": 0.01, "stddev": 0.001}, "onset_rate_hz": 0.1}
    sim_same = m._motif_prototype_similarity(base, same)
    sim_other = m._motif_prototype_similarity(base, other)
    assert sim_same["overall_similarity"] > sim_other["overall_similarity"]
    assert sim_same["overall_similarity"] > 0.75
    m.shutdown()


def test_find_similar_motifs_searches_retained_catalogs(tmp_path):
    m = manager(tmp_path)
    qid = "mediarec-" + "3" * 24
    tid = "mediarec-" + "4" * 24
    oid = "mediarec-" + "5" * 24

    def prototype(setting, note):
        families = {
            "visual_context": [f"setting={setting}"], "motion": [], "state_change": [], "scene_change": [],
            "speech_text": [], "speech_prosody": [], "music": [f"note={note}", f"pitch_class={note.rstrip('0123456789')}"],
        }
        tokens = [token for values in families.values() for token in values]
        return {
            "schema_version": "media_cross_comparison_signature/v1",
            "signature": m._motif_duoid({"tokens": tokens}),
            "families": families, "tokens": tokens, "sequence_sketches": {},
            "evidence_coverage": {key: "observed" for key in families},
            "measured_sketch": {"audio_rms": {"mean": 0.10, "stddev": 0.01}, "onset_rate_hz": 2.0},
        }

    def write(job_id, label, motif_id, proto):
        root = tmp_path / job_id
        root.mkdir()
        motif = {
            "motif_id": motif_id, "label": label + " motif", "status": "recurrent", "motif_kind": "cross_modal",
            "occurrence_count": 2, "representative_occurrence": {"start_seconds": 0.0, "end_seconds": 1.0, "duration_seconds": 1.0},
            "prototype": proto,
        }
        reconstruction = {
            "analysis_range": {"start_seconds": 0.0, "end_seconds": 3.0, "duration_seconds": 3.0},
            "source_clock": {"duration_seconds": 3.0},
            "visual": {"semantic_anchors": []},
            "audio": {"frames": [], "transcript": {"segments": [], "words": []}},
            "motifs": {"schema_version": "media_motif_catalog/v1", "motifs": [motif], "salient_candidates": []},
        }
        result = {"nodes": [{"label": label, "witness": {"reconstruction": reconstruction}}]}
        (root / "state.json").write_text(json.dumps({"job_id": job_id, "status": "completed", "filename": label, "created_at_ms": 1}))
        (root / "result.json").write_text(json.dumps(result))

    write(qid, "query.mp4", "motif-query", prototype("forest", "c4"))
    write(tid, "same.mp4", "motif-same", prototype("forest", "c4"))
    write(oid, "other.mp4", "motif-other", prototype("office", "f#5"))
    out = m.find_similar_motifs(qid, "motif-query", limit=5, min_similarity=0.0, max_jobs=10)
    assert out["matches"]
    assert out["matches"][0]["job_id"] == tid, out
    assert out["matches"][0]["overall_similarity"] > out["matches"][-1]["overall_similarity"]
    m.shutdown()



def test_motif_family_consolidation_collapses_phase_shifted_variants(tmp_path):
    m = manager(tmp_path)

    def proto(setting="forest", note="c4"):
        families = {
            "visual_context": [f"setting={setting}", "overall_action=running"],
            "motion": ["person:net=right"],
            "state_change": [], "scene_change": [],
            "speech_text": [], "speech_prosody": [],
            "music": [f"note={note}", f"pitch_class={note.rstrip('0123456789')}"],
        }
        tokens = [token for values in families.values() for token in values]
        return {
            "schema_version": "media_cross_comparison_signature/v1",
            "signature": m._motif_duoid({"tokens": tokens}),
            "families": families,
            "tokens": tokens,
            "sequence_sketches": {},
            "evidence_coverage": {key: "observed" for key in families},
            "measured_sketch": {"audio_rms": {"mean": 0.12, "stddev": 0.02}, "onset_rate_hz": 2.0},
        }

    def occ(a, b, score=.9):
        return {
            "start_seconds": a, "end_seconds": b, "duration_seconds": b-a,
            "similarity_to_representative": score, "salience": .8,
            "source_time_semantics": "absolute_source_clock",
        }

    motifs = [
        {
            "motif_id": "motif-" + "1"*24, "duration_seconds": .25, "recurrence_score": .82,
            "occurrence_count": 3, "occurrences": [occ(1.00,1.25),occ(2.00,2.25),occ(3.00,3.25)],
            "representative_occurrence": {"start_seconds":1.0,"end_seconds":1.25,"duration_seconds":.25},
            "prototype": proto(), "periodicity": {}, "status": "strong_recurrence",
        },
        {
            "motif_id": "motif-" + "2"*24, "duration_seconds": .25, "recurrence_score": .79,
            "occurrence_count": 3, "occurrences": [occ(1.05,1.30),occ(2.05,2.30),occ(3.05,3.30)],
            "representative_occurrence": {"start_seconds":1.05,"end_seconds":1.30,"duration_seconds":.25},
            "prototype": proto(), "periodicity": {}, "status": "strong_recurrence",
        },
        {
            "motif_id": "motif-" + "3"*24, "duration_seconds": .25, "recurrence_score": .76,
            "occurrence_count": 2, "occurrences": [occ(4.0,4.25),occ(5.0,5.25)],
            "representative_occurrence": {"start_seconds":4.0,"end_seconds":4.25,"duration_seconds":.25},
            "prototype": proto(setting="office", note="f#5"), "periodicity": {}, "status": "recurrent",
        },
    ]
    canonical, suppressions = m._consolidate_motif_families(motifs, max_motifs=10)
    assert len(canonical) == 2
    merged = next(row for row in canonical if row["motif_id"] == "motif-" + "1"*24)
    assert merged["family_consolidation"]["raw_variant_count"] == 2
    assert merged["family_consolidation"]["suppressed_variant_count"] == 1
    assert merged["occurrence_count"] == 3
    assert len(suppressions) == 1
    assert suppressions[0]["suppressed_motif_id"] == "motif-" + "2"*24
    m.shutdown()


def test_motif_family_consolidation_does_not_merge_same_semantics_at_distinct_times(tmp_path):
    m = manager(tmp_path)
    families = {
        "visual_context": ["setting=forest"], "motion": [], "state_change": [], "scene_change": [],
        "speech_text": [], "speech_prosody": [], "music": ["note=c4"],
    }
    proto = {
        "schema_version": "media_cross_comparison_signature/v1",
        "signature": m._motif_duoid({"families": families}),
        "families": families,
        "tokens": ["setting=forest","note=c4"],
        "sequence_sketches": {},
        "evidence_coverage": {key:"observed" for key in families},
        "measured_sketch": {},
    }
    def motif(mid, starts):
        return {
            "motif_id": mid, "duration_seconds": .5, "recurrence_score": .8,
            "occurrence_count": len(starts),
            "occurrences": [{"start_seconds":s,"end_seconds":s+.5,"duration_seconds":.5,"similarity_to_representative":.9,"salience":.8} for s in starts],
            "representative_occurrence":{"start_seconds":starts[0],"end_seconds":starts[0]+.5,"duration_seconds":.5},
            "prototype": proto, "periodicity": {}, "status":"recurrent",
        }
    canonical, suppressions = m._consolidate_motif_families([
        motif("motif-"+"a"*24,[0.0,2.0]),
        motif("motif-"+"b"*24,[5.0,7.0]),
    ], max_motifs=10)
    assert len(canonical) == 2
    assert suppressions == []
    m.shutdown()



def test_visual_embeddings_best_effort_batch_client(tmp_path, monkeypatch):
    import duotronic_runtime.media_reconstruction as media_module
    m = manager(tmp_path)
    p0 = tmp_path / "a.jpg"; p1 = tmp_path / "b.jpg"
    p0.write_bytes(b"fake-jpeg-a"); p1.write_bytes(b"fake-jpeg-b")
    anchors = [
        {"anchor_index": 0, "sample_index": 1, "time_seconds": 0.25, "image_path": str(p0)},
        {"anchor_index": 1, "sample_index": 2, "time_seconds": 0.75, "image_path": str(p1)},
    ]
    monkeypatch.setattr(m, "_service", lambda service: {
        "candidate": {"node_id": "vm1", "service_endpoint": "http://10.77.0.3:8791", "service_endpoint_scope": "observed-live"},
        "record": {"embed_path": "/embed/batch", "model": "facebook/dinov2-small", "dimensions": 4,
                   "internet_required": False, "image": "image", "image_id": "exact"},
    } if service == "visual_embedding" else None)

    class Response:
        def raise_for_status(self): return None
        def json(self):
            return {"model": "facebook/dinov2-small", "items": [
                {"input_digest": "d0", "embedding": [2.0, 0.0, 0.0, 0.0], "dimensions": 4},
                {"input_digest": "d1", "embedding": [0.0, 3.0, 0.0, 0.0], "dimensions": 4},
            ]}
    class Client:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def post(self, url, json):
            assert url == "http://10.77.0.3:8791/embed/batch"
            assert len(json["images_b64"]) == 2
            return Response()
    monkeypatch.setattr(media_module.httpx, "Client", Client)
    rows, worker = m._visual_embeddings(anchors)
    assert worker["status"] == "completed"
    assert worker["embedded_count"] == 2
    assert worker["internet_required"] is False
    assert rows[0]["embedding"] == [1.0, 0.0, 0.0, 0.0]
    assert rows[1]["embedding"] == [0.0, 1.0, 0.0, 0.0]
    assert rows[0]["provenance"]["identity_semantics"].startswith("not_person_identity_evidence")
    m.shutdown()


def test_visual_embeddings_failure_is_nonfatal(tmp_path, monkeypatch):
    import duotronic_runtime.media_reconstruction as media_module
    m = manager(tmp_path)
    p = tmp_path / "a.jpg"; p.write_bytes(b"fake")
    monkeypatch.setattr(m, "_service", lambda service: {
        "candidate": {"node_id": "vm1", "service_endpoint": "http://10.77.0.3:8791"},
        "record": {"embed_path": "/embed/batch", "model": "facebook/dinov2-small", "dimensions": 384},
    })
    class Client:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def post(self, *args, **kwargs): raise RuntimeError("worker down")
    monkeypatch.setattr(media_module.httpx, "Client", Client)
    rows, worker = m._visual_embeddings([{"anchor_index":0,"sample_index":0,"time_seconds":0.0,"image_path":str(p)}])
    assert rows == []
    assert worker["status"] == "failed"
    assert worker["failed_batch_count"] == 1
    m.shutdown()


def test_motif_measured_sketch_centroids_visual_embeddings(tmp_path):
    m = manager(tmp_path)
    reconstruction = {
        "visual": {
            "deterministic_samples": [],
            "perceptual_embeddings": [
                {"time_seconds": 1.0, "embedding": [1.0, 0.0], "model": "dino"},
                {"time_seconds": 1.5, "embedding": [0.0, 1.0], "model": "dino"},
                {"time_seconds": 3.0, "embedding": [-1.0, 0.0], "model": "dino"},
            ],
        },
        "audio": {"frames": [], "onsets": []},
    }
    out = m._motif_measured_sketch(reconstruction, 0.5, 2.0)
    assert out["visual_embedding_count"] == 2
    assert out["visual_embedding_dimensions"] == 2
    centroid = np.asarray(out["visual_embedding_centroid"], dtype=float)
    assert abs(np.linalg.norm(centroid) - 1.0) < 1e-6
    assert centroid[0] > 0.70 and centroid[1] > 0.70
    m.shutdown()


def test_motif_sketch_similarity_uses_optional_visual_embedding(tmp_path):
    m = manager(tmp_path)
    same = {
        "audio_rms": {"mean": 0.1, "stddev": 0.01},
        "visual_embedding_centroid": [1.0, 0.0, 0.0],
    }
    near = {
        "audio_rms": {"mean": 0.1, "stddev": 0.01},
        "visual_embedding_centroid": [0.8, 0.6, 0.0],
    }
    far = {
        "audio_rms": {"mean": 0.1, "stddev": 0.01},
        "visual_embedding_centroid": [0.0, 0.0, 1.0],
    }
    s0 = m._motif_sketch_similarity(same, same)
    s1 = m._motif_sketch_similarity(same, near)
    s2 = m._motif_sketch_similarity(same, far)
    assert s0["visual_embedding_cosine"] > s1["visual_embedding_cosine"] > s2["visual_embedding_cosine"]
    assert s0["score"] > s1["score"] > s2["score"]
    assert s0["weights"]["visual_embedding"] == 0.45
    m.shutdown()


def test_offset_analysis_timeline_offsets_visual_embeddings(tmp_path):
    m = manager(tmp_path)
    embeddings = [{"time_seconds": 0.25, "embedding": [1.0, 0.0]}]
    m._offset_analysis_timeline(
        offset=2.0, metrics=[], vision=[], audio={"frames": [], "onsets": [], "note_intervals": [], "chord_intervals": []},
        words=[], transcript_segments=[], visual_embeddings=embeddings,
    )
    assert embeddings[0]["time_seconds"] == 2.25
    m.shutdown()



def test_ensure_visual_embeddings_legacy_sidecar_cache(tmp_path, monkeypatch):
    m = manager(tmp_path)
    job_id = "mediarec-" + "6" * 24
    root = tmp_path / job_id
    (root / "anchors").mkdir(parents=True)
    (root / "anchors" / "anchor-0000.jpg").write_bytes(b"a")
    (root / "anchors" / "anchor-0001.jpg").write_bytes(b"b")
    reconstruction = {
        "visual": {"semantic_anchors": [
            {"anchor_index": 0, "sample_index": 0, "time_seconds": 1.0},
            {"anchor_index": 1, "sample_index": 5, "time_seconds": 2.0},
        ]}
    }
    calls = {"n": 0}
    def fake_embed(anchors):
        calls["n"] += 1
        return [
            {"anchor_index":0,"sample_index":0,"time_seconds":1.0,"embedding":[1.0,0.0],"dimensions":2,"model":"dino"},
            {"anchor_index":1,"sample_index":5,"time_seconds":2.0,"embedding":[0.0,1.0],"dimensions":2,"model":"dino"},
        ], {"status":"completed","model":"dino","image_id":"exact","worker_id":"vm1","internet_required":False}
    monkeypatch.setattr(m, "_visual_embeddings", fake_embed)
    first = m._ensure_visual_embeddings_for_reconstruction(job_id, reconstruction)
    assert first["status"] == "derived"
    assert calls["n"] == 1
    assert (root / "derived_visual_embeddings.json").is_file()
    reconstruction2 = {"visual": {"semantic_anchors": reconstruction["visual"]["semantic_anchors"]}}
    second = m._ensure_visual_embeddings_for_reconstruction(job_id, reconstruction2)
    assert second["status"] == "cached"
    assert calls["n"] == 1
    assert len(reconstruction2["visual"]["perceptual_embeddings"]) == 2
    m.shutdown()


def test_align_jobs_prefers_optional_visual_embedding_when_other_scores_tie(tmp_path, monkeypatch):
    m = manager(tmp_path)
    qid = "mediarec-" + "7" * 24
    tid = "mediarec-" + "8" * 24
    def write(job_id, marker, end):
        root = tmp_path / job_id; root.mkdir()
        reconstruction = {
            "marker": marker,
            "analysis_range":{"start_seconds":0.0,"end_seconds":end,"duration_seconds":end},
            "source_clock":{"duration_seconds":end},
            "visual":{"deterministic_samples":[],"semantic_anchors":[],"perceptual_embeddings":[]},
            "audio":{"frames":[],"onsets":[],"transcript":{"words":[],"segments":[]}},
        }
        (root/"state.json").write_text(json.dumps({"job_id":job_id,"status":"completed","created_at_ms":1}))
        (root/"result.json").write_text(json.dumps({"nodes":[{"label":marker,"witness":{"reconstruction":reconstruction}}]}))
    write(qid,"query",1.0); write(tid,"target",2.0)
    monkeypatch.setattr(m, "_ensure_visual_embeddings_for_reconstruction", lambda *args, **kwargs: {"status":"test"})
    monkeypatch.setattr(m, "_window_signature_from_reconstruction", lambda *args, **kwargs: {
        "families":{}, "tokens":[], "sequence_sketches":{}, "window_evidence":{}, "signature":"s"
    })
    monkeypatch.setattr(m, "_compare_signature_bundles", lambda *args, **kwargs: {
        "overall_similarity":0.5,"token_jaccard":0.5,"family_weighted_similarity":0.5,"sequence_similarity":0.5,
        "comparison_coverage":{},"family_overlap":{},"common_tokens":[]
    })
    monkeypatch.setattr(m, "_measured_alignment_similarity", lambda *args, **kwargs: {"score":0.5})
    def sketch(reconstruction, start, end):
        if reconstruction.get("marker") == "query":
            return {"visual_embedding_centroid":[1.0,0.0]}
        return {"visual_embedding_centroid":[1.0,0.0] if start >= 0.99 else [0.0,1.0]}
    monkeypatch.setattr(m, "_motif_measured_sketch", sketch)
    out = m.align_jobs(qid, tid, window_seconds=1.0, step_seconds=1.0, limit=2, max_windows=10)
    assert out["matches"][0]["start_seconds"] == 1.0, out
    assert out["matches"][0]["visual_embedding_similarity"] == 1.0
    assert out["matches"][0]["score_weights"] == {"semantic":0.20,"measured":0.60,"visual_embedding":0.20}
    assert out["matches"][1]["visual_embedding_similarity"] == 0.0
    m.shutdown()



def test_motif_measured_sketch_audio_embedding_centroid(tmp_path):
    m=manager(tmp_path)
    reconstruction={"visual":{"deterministic_samples":[]},"audio":{"frames":[],"onsets":[],"perceptual_embeddings":[
        {"start_seconds":0.0,"end_seconds":1.0,"time_seconds":0.5,"embedding":[1.0,0.0],"model":"clap"},
        {"start_seconds":1.0,"end_seconds":2.0,"time_seconds":1.5,"embedding":[0.0,1.0],"model":"clap"},
        {"start_seconds":3.0,"end_seconds":4.0,"time_seconds":3.5,"embedding":[-1.0,0.0],"model":"clap"},
    ]}}
    out=m._motif_measured_sketch(reconstruction,0.5,2.0)
    assert out["audio_embedding_count"]==2
    assert out["audio_embedding_dimensions"]==2
    c=np.asarray(out["audio_embedding_centroid"],dtype=float)
    assert abs(np.linalg.norm(c)-1.0)<1e-6 and c[0]>.70 and c[1]>.70
    assert out["audio_embedding_identity_semantics"].startswith("not_speaker_identity_evidence")
    m.shutdown()


def test_motif_sketch_similarity_uses_both_perceptual_modalities(tmp_path):
    m=manager(tmp_path)
    a={"audio_rms":{"mean":.1,"stddev":.01},"visual_embedding_centroid":[1.,0.],"audio_embedding_centroid":[0.,1.]}
    same=dict(a)
    visual_far={**a,"visual_embedding_centroid":[0.,1.]}
    audio_far={**a,"audio_embedding_centroid":[1.,0.]}
    both_far={**a,"visual_embedding_centroid":[0.,1.],"audio_embedding_centroid":[1.,0.]}
    s0=m._motif_sketch_similarity(a,same); sv=m._motif_sketch_similarity(a,visual_far); sa=m._motif_sketch_similarity(a,audio_far); sb=m._motif_sketch_similarity(a,both_far)
    assert s0["score"]>sv["score"]>sb["score"]
    assert s0["score"]>sa["score"]>sb["score"]
    assert s0["weights"]=={"coarse_measured":.40,"visual_embedding":.30,"audio_embedding":.30}
    m.shutdown()


def test_audio_embedding_windows_are_bounded(tmp_path):
    m=manager(tmp_path)
    rows=m._audio_embedding_windows(0,3600,max_windows=512,window_seconds=1.0,hop_seconds=.5)
    assert 1 <= len(rows) <= 512
    assert rows[0]["start_seconds"]==0.0
    assert abs(rows[-1]["end_seconds"]-3600.0)<1e-6
    assert all(r["end_seconds"]>r["start_seconds"] for r in rows)
    m.shutdown()


def test_ensure_audio_embeddings_legacy_sidecar_cache(tmp_path,monkeypatch):
    m=manager(tmp_path); job_id="mediarec-"+"9"*24; root=tmp_path/job_id; root.mkdir(); (root/"source.mp4").write_bytes(b"media")
    reconstruction={"analysis_range":{"start_seconds":1.0,"end_seconds":3.0},"source_clock":{"duration_seconds":5.0},"audio":{}}
    calls={"n":0}
    def fake(source,*,start_seconds,end_seconds):
        calls["n"]+=1
        return [{"time_seconds":1.5,"start_seconds":1.,"end_seconds":2.,"embedding":[1.,0.],"dimensions":2,"model":"clap"}],{"status":"completed","model":"clap","image_id":"exact","worker_id":"vm1","internet_required":False}
    monkeypatch.setattr(m,"_audio_embeddings",fake)
    first=m._ensure_audio_embeddings_for_reconstruction(job_id,reconstruction)
    assert first["status"]=="derived" and calls["n"]==1 and (root/"derived_audio_embeddings.json").is_file()
    reconstruction2={"analysis_range":reconstruction["analysis_range"],"source_clock":reconstruction["source_clock"],"audio":{}}
    second=m._ensure_audio_embeddings_for_reconstruction(job_id,reconstruction2)
    assert second["status"]=="cached" and calls["n"]==1 and len(reconstruction2["audio"]["perceptual_embeddings"])==1
    m.shutdown()



def test_alignment_score_policy_uses_visual_and_audio_embeddings(tmp_path, monkeypatch):
    m=manager(tmp_path)
    def write(job_id,label):
        root=tmp_path/job_id; root.mkdir()
        reconstruction={
          "analysis_range":{"start_seconds":0.0,"end_seconds":2.0,"duration_seconds":2.0},
          "source_clock":{"duration_seconds":2.0},
          "visual":{"deterministic_samples":[{"time_seconds":0.,"mean_luma":20.,"change_score":1.},{"time_seconds":1.,"mean_luma":20.,"change_score":1.}],"semantic_anchors":[],"entity_tracks":[],"temporal_transitions":[],"perceptual_embeddings":[{"time_seconds":.5,"embedding":[1.,0.],"model":"dino"}]},
          "audio":{"frames":[{"time_seconds":0.,"rms":.1,"spectral_centroid_hz":1000.,"spectral_flux":.1},{"time_seconds":1.,"rms":.1,"spectral_centroid_hz":1000.,"spectral_flux":.1}],"onsets":[],"note_intervals":[],"chord_intervals":[],"transcript":{"words":[],"segments":[]},"perceptual_embeddings":[{"start_seconds":0.,"end_seconds":1.,"time_seconds":.5,"embedding":[0.,1.],"model":"clap"}]}
        }
        result={"nodes":[{"label":label,"witness":{"reconstruction":reconstruction}}]}
        (root/'state.json').write_text(json.dumps({"job_id":job_id,"status":"completed","filename":label,"created_at_ms":1}))
        (root/'result.json').write_text(json.dumps(result)); return reconstruction
    q='mediarec-'+'a'*24; tar='mediarec-'+'b'*24
    write(q,'q.mp4'); write(tar,'t.mp4')
    monkeypatch.setattr(m,'_ensure_visual_embeddings_for_reconstruction',lambda *a,**k:{"status":"embedded"})
    monkeypatch.setattr(m,'_ensure_audio_embeddings_for_reconstruction',lambda *a,**k:{"status":"embedded"})
    out=m.align_jobs(q,tar,window_seconds=2.0,step_seconds=.5,limit=2)
    best=out['matches'][0]
    assert best['visual_embedding_similarity'] is not None
    assert best['audio_embedding_similarity'] is not None
    assert best['score_weights']=={"semantic":.20,"measured":.50,"visual_embedding":.15,"audio_embedding":.15}
    assert out['scoring_policy']['when_measured_and_both_perceptual_embeddings_available']['audio_embedding_weight']==.15
    assert 'not_speaker_identity_evidence' in out['identity_semantics']
    m.shutdown()



def test_window_signature_includes_separate_ml_note_events(tmp_path):
    m=manager(tmp_path)
    reconstruction={
      "analysis_range":{"start_seconds":0.0,"end_seconds":4.0},
      "source_clock":{"duration_seconds":4.0},
      "visual":{"semantic_anchors":[]},
      "audio":{
        "frames":[],"onsets":[],"note_intervals":[{"start_seconds":0.0,"end_seconds":1.0,"note":"C4"}],
        "chord_intervals":[],"tempo_bpm_hypothesis":None,
        "ml_note_events":[
          {"start_seconds":1.0,"end_seconds":2.0,"midi":64,"note":"E4","activation":0.8,"provenance":{"model":"spotify/basic-pitch-0.4.0"}},
          {"start_seconds":3.0,"end_seconds":3.5,"midi":67,"note":"G4","activation":0.7,"provenance":{"model":"spotify/basic-pitch-0.4.0"}},
        ],
        "transcript":{"words":[],"segments":[]},
      },
    }
    out=m._window_signature_from_reconstruction(reconstruction,start_seconds=.75,end_seconds=2.25)
    ev=out["window_evidence"]
    assert [r["note"] for r in ev["ml_notes"]]==["E4"]
    assert any("ml_note=e4" in x.lower() for x in out["families"]["music"])
    assert any("ml_pitch_class=e" in x.lower() for x in out["families"]["music"])
    assert [x.lower() for x in out["sequence_sketches"]["ml_pitch_classes"]]==["e"]


def test_offset_analysis_timeline_offsets_ml_note_events(tmp_path):
    m=manager(tmp_path)
    audio={"frames":[],"perceptual_embeddings":[],"onsets":[],"note_intervals":[],"chord_intervals":[],
           "ml_note_events":[{"start_seconds":.25,"end_seconds":.75,"note":"C4"}]}
    m._offset_analysis_timeline(offset=10.0,metrics=[],vision=[],audio=audio,words=[],transcript_segments=[],visual_embeddings=[])
    assert audio["ml_note_events"][0]["start_seconds"]==10.25
    assert audio["ml_note_events"][0]["end_seconds"]==10.75


def test_catalog_capability_detectors_cover_audio_and_ml_notes(tmp_path):
    m=manager(tmp_path)
    catalog={"motifs":[{
      "prototype":{"measured_sketch":{"audio_embedding_centroid":[1.0,0.0]}},
      "occurrences":[{"window_evidence":{"ml_notes":[{"note":"C4"}]}}],
    }],"salient_candidates":[]}
    assert m._catalog_has_audio_embedding(catalog) is True
    assert m._catalog_has_ml_note_events(catalog) is True



def test_terminal_job_state_cannot_regress_to_cancelling(tmp_path):
    m=manager(tmp_path)
    root=tmp_path/("mediarec-"+"c"*24); root.mkdir()
    state={"job_id":root.name,"status":"cancelled","stage":"cancelled","progress":0.3}
    (root/"state.json").write_text(json.dumps(state))
    stale={"job_id":root.name,"status":"running","stage":"fake_work","progress":0.2}
    m._state(root,stale,status="cancelling",stage="cancelling",cancel_requested=True)
    final=json.loads((root/"state.json").read_text())
    assert final["status"]=="cancelled"
    assert final["stage"]=="cancelled"
