import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from talknread import llm  # noqa: E402
from talknread import subtitles as sub  # noqa: E402


def W(word, start, end):
    return SimpleNamespace(word=word, start=start, end=end)


def test_srt_vtt_format():
    segs = [sub.Seg(0.0, 2.5, "Olá, mundo."), sub.Seg(3725.123, 3727.0, "Fim.")]
    srt = sub.to_srt(segs)
    assert srt.startswith("1\n00:00:00,000 --> 00:00:02,500\nOlá, mundo.\n")
    assert "2\n01:02:05,123 --> 01:02:07,000" in srt
    vtt = sub.to_vtt(segs)
    assert vtt.startswith("WEBVTT")
    assert "00:00:00.000 --> 00:00:02.500" in vtt


def test_empty_text_skipped_and_numbering_continuous():
    srt = sub.to_srt([sub.Seg(0, 1, "a"), sub.Seg(1, 2, "  "), sub.Seg(2, 3, "b")])
    assert srt.count("-->") == 2 and "\n2\n" in srt


def test_wrap_two_lines_max():
    out = sub.wrap_lines("palavra " * 40)
    assert out.count("\n") == 1


def test_chunk_words_splits_on_pause_and_sentence():
    words = [W(" Oi", 0.0, 0.3), W(" tudo", 0.3, 0.6), W(" bem?", 0.6, 0.9),
             W(" Hoje", 3.0, 3.3), W(" vamos", 3.3, 3.6), W(" falar.", 3.6, 4.0)]
    chunks = sub.chunk_words(words)
    assert [c.text for c in chunks] == ["Oi tudo bem?", "Hoje vamos falar."]
    assert chunks[1].start == 3.0


def test_tidy_no_overlap_and_min_duration():
    out = sub.tidy([sub.Seg(0, 0.1, "a"), sub.Seg(0.2, 5, "b")])
    assert out[0].end <= out[1].start
    assert out[1].end - out[1].start >= 0.4


class FakeClient:
    def __init__(self, behavior):
        self.behavior = behavior
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        user = json.loads(kw["messages"][1]["content"])
        content = self.behavior(user["items"])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def test_llm_review_keeps_timestamps():
    segs = [sub.Seg(0, 1, "ola mundo"), sub.Seg(1, 2, "tudo bem")]
    client = FakeClient(lambda items: json.dumps(
        {"items": [{"id": i["id"], "text": i["text"].capitalize() + "."} for i in items]}))
    out, failed = llm.process(segs, "review", language="português", client=client, model="x")
    assert failed == 0
    assert [s.text for s in out] == ["Ola mundo.", "Tudo bem."]
    assert [(s.start, s.end) for s in out] == [(0, 1), (1, 2)]


def test_llm_failure_keeps_original():
    segs = [sub.Seg(0, 1, "a"), sub.Seg(1, 2, "b")]
    out, failed = llm.process(segs, "review", client=FakeClient(lambda items: "não é json"), model="x")
    assert failed == 2 and [s.text for s in out] == ["a", "b"]


def test_llm_wrong_ids_rejected():
    segs = [sub.Seg(0, 1, "a")]
    client = FakeClient(lambda items: json.dumps({"items": [{"id": 99, "text": "x"}]}))
    out, failed = llm.process(segs, "translate", target="inglês", client=client, model="x")
    assert failed == 1 and out[0].text == "a"


def test_llm_tolerates_code_fences():
    segs = [sub.Seg(0, 1, "a")]
    client = FakeClient(lambda items: "```json\n" + json.dumps(
        {"items": [{"id": 0, "text": "A"}]}) + "\n```")
    out, failed = llm.process(segs, "review", client=client, model="x")
    assert failed == 0 and out[0].text == "A"
