"""
AppPaaS uWSGI 호환용 WSGI 진입점.
Step 1: 최소 동작 확인 (임포트 없음)
"""
import sys
import os

# 디버그: 어떤 경로에서 실행되는지 확인
_cwd = os.getcwd()
_file = os.path.abspath(__file__)
_backend_path = os.path.join(os.path.dirname(_file), "backend")
sys.path.insert(0, _backend_path)

try:
    from app.main import app as fastapi_app
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(fastapi_app)
    _status = f"OK - FastAPI loaded. cwd={_cwd}, file={_file}"
except Exception as e:
    import traceback
    _err = traceback.format_exc()
    _status = f"ERROR: {e}\n{_err}"

    # 임포트 실패 시에도 uWSGI가 application을 찾을 수 있게 fallback 제공
    def application(environ, start_response):
        body = _status.encode("utf-8")
        start_response("500 Internal Server Error", [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ])
        return [body]
