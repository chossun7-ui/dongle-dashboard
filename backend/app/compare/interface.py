"""비교 알고리즘 공개 진입점.

본 모듈은 알고리즘 본체(`algorithm.py`, 사내 AI 작성)를 동적으로 우선 호출하고,
없으면 더미 구현(`stub.py`)으로 폴백한다.

사내 AI가 `backend/app/compare/algorithm.py`를 추가하면 자동으로 그 구현이 사용된다.
파일이 없거나 import 실패 시에도 서버는 정상 부팅되며, 비교 요청 시 stub이 응답한다.
"""

from __future__ import annotations

import importlib
import logging
from typing import Callable

from app.compare.types import CompareRequest, CompareResult

_log = logging.getLogger(__name__)

_ALGO_MODULE = "app.compare.algorithm"
_STUB_MODULE = "app.compare.stub"


def _resolve_impl() -> Callable[[CompareRequest], CompareResult]:
    """우선순위: algorithm.compare_recipes → stub.compare_recipes."""
    for mod_name in (_ALGO_MODULE, _STUB_MODULE):
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, "compare_recipes", None)
            if callable(fn):
                if mod_name == _STUB_MODULE:
                    _log.warning(
                        "compare 알고리즘 본체(%s)가 없어 stub으로 폴백합니다. "
                        "사내 AI가 작성한 본체를 algorithm.py로 추가하세요.",
                        _ALGO_MODULE,
                    )
                return fn
        except ImportError as e:  # pragma: no cover - defensive
            _log.debug("compare 구현 모듈 %s import 실패: %s", mod_name, e)
    raise RuntimeError(
        "compare_recipes 구현을 찾지 못했습니다. "
        f"{_ALGO_MODULE} 또는 {_STUB_MODULE} 둘 중 하나라도 있어야 합니다."
    )


def compare_recipes(request: CompareRequest) -> CompareResult:
    """비교 본체 호출의 단일 게이트웨이.

    API 라우터는 항상 이 함수를 통해 비교를 수행한다.
    동적 폴백 덕분에 사내 AI가 본체를 늦게 제출해도 서버 코드가 망가지지 않는다.

    CPU 바운드이므로 FastAPI 라우터에서는 `loop.run_in_executor(ProcessPoolExecutor, ...)`
    로 감싸 호출한다.
    """
    if len(request.recipes) < 2:
        raise ValueError("비교를 위해서는 최소 2개의 Recipe가 필요합니다.")
    impl = _resolve_impl()
    return impl(request)
