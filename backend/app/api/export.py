"""비교 결과 Export.

세 가지 포맷:
- HTML : Jinja 템플릿으로 self-contained 단일 파일
- CSV  : diff 행 단위 (kind, section, key, left_value, right_value, severity)
- PDF  : WeasyPrint로 HTML→PDF (Linux 컨테이너에서 동작)

요청 형식은 비교와 동일: {recipe_ids, options}. 백엔드가 직접 compare를 돌려 결과를 받아 변환.
"""

from __future__ import annotations

import asyncio
import csv
import io
from dataclasses import asdict
from concurrent.futures import ProcessPoolExecutor

from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse
from jinja2 import Environment, BaseLoader, select_autoescape
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.compare import _build_options, _load_recipe_inputs
from app.api.envelope import ApiError
from app.compare import CompareRequest, compare_recipes
from app.db.session import get_db

router = APIRouter(prefix="/api/export", tags=["export"])

_EXEC = ProcessPoolExecutor(max_workers=2)


class ExportBody(BaseModel):
    recipe_ids: list[int]
    options: dict | None = None


_HTML_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Recipe Compare {{ generated_at }}</title>
<style>
  body { font-family: ui-sans-serif, "Noto Sans KR", sans-serif; margin: 24px; color: #0f172a; }
  h1 { margin: 0 0 12px; font-size: 20px; }
  .meta { color: #475569; font-size: 13px; margin-bottom: 16px; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 13px; }
  th, td { border: 1px solid #e2e8f0; padding: 6px 8px; text-align: left; vertical-align: top; }
  th { background: #f1f5f9; }
  .k-added { background: #dcfce7; }
  .k-removed { background: #fee2e2; }
  .k-changed { background: #fef3c7; }
  .sev-critical { color: #b91c1c; font-weight: 700; }
  .sev-major { color: #c2410c; font-weight: 600; }
  .sev-minor { color: #a16207; }
  .sev-info { color: #475569; }
  .pair-head { margin-top: 24px; font-weight: 600; }
  pre.value { margin: 0; white-space: pre-wrap; word-break: break-all; font-family: ui-monospace, monospace; font-size: 12px; max-width: 380px; }
</style>
</head>
<body>
  <h1>Recipe Compare Export</h1>
  <div class="meta">
    schema={{ schema_version }} · generated={{ generated_at }} · inputs={{ inputs|length }} · pairs={{ pairs|length }}
  </div>

  <h2>입력 Recipe</h2>
  <table>
    <thead><tr><th>recipe_id</th><th>라인</th><th>모델</th><th>설비</th><th>경로</th><th>Film</th></tr></thead>
    <tbody>
    {% for r in inputs %}
      <tr>
        <td>{{ r.recipe_id }}</td>
        <td>{{ r.line_name }}</td>
        <td>{{ r.model_name }}</td>
        <td>{{ r.equipment_name }}</td>
        <td>{{ r.path }}</td>
        <td>{{ r.film_name }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>

  <h2>요약</h2>
  <table>
    <tr><th>전체 쌍</th><td>{{ summary.total_pairs }}</td></tr>
    <tr><th>동일</th><td>{{ summary.pairs_identical }}</td></tr>
    <tr><th>차이 있음</th><td>{{ summary.pairs_with_diffs }}</td></tr>
    <tr><th>총 차이 수</th><td>{{ summary.total_diffs }}</td></tr>
    <tr><th>kind별</th><td>{{ summary.by_kind }}</td></tr>
    <tr><th>severity별</th><td>{{ summary.by_severity }}</td></tr>
  </table>

  {% for p in pairs %}
    <div class="pair-head">
      Pair: {{ p.left_recipe_id }} ↔ {{ p.right_recipe_id }}
      &nbsp;·&nbsp; same={{ p.same }} &nbsp;·&nbsp; similarity={{ '%.3f'|format(p.similarity) }}
    </div>
    <table>
      <thead>
        <tr>
          <th>kind</th><th>section</th><th>key</th>
          <th>left</th><th>right</th>
          <th>severity</th><th>note</th>
        </tr>
      </thead>
      <tbody>
      {% for d in p.diffs %}
        <tr class="k-{{ d.kind }}">
          <td>{{ d.kind }}</td>
          <td>{{ d.section or "" }}</td>
          <td>{{ d.key or "" }}</td>
          <td><pre class="value">{{ d.left_value or "" }}</pre></td>
          <td><pre class="value">{{ d.right_value or "" }}</pre></td>
          <td class="sev-{{ d.severity }}">{{ d.severity }}</td>
          <td>{{ d.note or "" }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  {% endfor %}

  {% if warnings %}
    <h2>경고</h2>
    <ul>{% for w in warnings %}<li>{{ w }}</li>{% endfor %}</ul>
  {% endif %}
</body>
</html>
"""


def _render_html(result_dict: dict) -> str:
    env = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html"]))
    tpl = env.from_string(_HTML_TEMPLATE)
    return tpl.render(**result_dict)


async def _run_compare(db: Session, recipe_ids: list[int], options: dict | None):
    if len(recipe_ids) < 2:
        raise ApiError("export.too_few", "최소 2개 Recipe가 필요합니다.")
    inputs = _load_recipe_inputs(db, recipe_ids)
    req = CompareRequest(recipes=inputs, options=_build_options(options))
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_EXEC, compare_recipes, req)


@router.post("/html")
async def export_html(body: ExportBody, db: Session = Depends(get_db)):
    result = await _run_compare(db, body.recipe_ids, body.options)
    html = _render_html(asdict(result))
    return Response(
        content=html,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="compare.html"'},
    )


@router.post("/csv")
async def export_csv(body: ExportBody, db: Session = Depends(get_db)):
    result = await _run_compare(db, body.recipe_ids, body.options)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "left_recipe_id",
            "right_recipe_id",
            "kind",
            "section",
            "key",
            "left_value",
            "right_value",
            "left_line",
            "right_line",
            "severity",
            "note",
        ]
    )
    for p in result.pairs:
        for d in p.diffs:
            w.writerow(
                [
                    p.left_recipe_id,
                    p.right_recipe_id,
                    d.kind,
                    d.section or "",
                    d.key or "",
                    d.left_value or "",
                    d.right_value or "",
                    d.left_line if d.left_line is not None else "",
                    d.right_line if d.right_line is not None else "",
                    d.severity,
                    d.note or "",
                ]
            )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8-sig")]),  # Excel용 BOM
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="compare.csv"'},
    )


@router.post("/pdf")
async def export_pdf(body: ExportBody, db: Session = Depends(get_db)):
    result = await _run_compare(db, body.recipe_ids, body.options)
    html = _render_html(asdict(result))
    try:
        from weasyprint import HTML  # 지연 import — 환경에 따라 무거울 수 있음.

        pdf_bytes = HTML(string=html).write_pdf()
    except Exception as e:
        raise ApiError(
            "export.pdf_unavailable",
            f"PDF 생성 실패 (WeasyPrint 미설치 또는 시스템 라이브러리 부족): {e}",
            500,
        )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="compare.pdf"'},
    )
