"""Fix for middleware body reading issue"""

# This is the correct way to implement the receive function
async def fixed_receive():
    # Return the body in the format expected by Starlette
    return {"type": "http.request", "body": body}

# The issue is that the receive function should be called multiple times
# First call returns the body, subsequent calls return empty body
class BodyReader:
    def __init__(self, body: bytes):
        self.body = body
        self.has_read = False
    
    async def __call__(self):
        if not self.has_read:
            self.has_read = True
            return {"type": "http.request", "body": self.body}
        else:
            # Return empty body for subsequent reads
            return {"type": "http.request", "body": b""}

# Better implementation:
from starlette.datastructures import Headers
from starlette.requests import Request
import io

def recreate_request(request: Request, body: bytes):
    """Recreate request with new body that can be read"""
    
    # Create a new receive callable
    async def receive():
        return {"type": "http.request", "body": body}
    
    # Create new request with the receive function
    new_request = Request(
        {
            "type": "http",
            "asgi": request.scope.get("asgi"),
            "http_version": request.scope.get("http_version"),
            "method": request.method,
            "scheme": request.url.scheme,
            "path": request.url.path,
            "query_string": request.url.query.encode() if request.url.query else b"",
            "root_path": request.scope.get("root_path", ""),
            "headers": request.headers.raw,
            "server": request.scope.get("server"),
            "client": request.scope.get("client"),
            "state": request.scope.get("state", {}),
        },
        receive=receive
    )
    
    return new_request