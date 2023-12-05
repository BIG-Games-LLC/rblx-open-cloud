from typing import Literal, Optional, TypeVar, Generic
import requests, time

VERSION: str = "1.6.0"
VERSION_INFO: Literal['alpha', 'beta', 'final'] = "final"

user_agent: str = f"rblx-open-cloud/{VERSION} (https://github.com/treeben77/rblx-open-cloud)"

request_session: requests.Session = requests.Session()

T = TypeVar("T", )

class Operation(Generic[T]):
    def __init__(self, path: str, api_key: str, return_type: T, **return_meta) -> None:
        self.__path: str = path
        self.__api_key: str = api_key
        self.__return_type: T = return_type
        self.__return_meta: dict = return_meta
    
    def __repr__(self) -> str:
        return "rblxopencloud.Operation()"
    
    def fetch_status(self) -> Optional[T]:
        response = request_session.get(f"https://apis.roblox.com/{self.__path}",
            headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent})
        
        if response.ok:
            info = response.json()
            if not info.get("done"): return None
            
            if callable(self.__return_type):
                return self.__return_type(info["response"], **self.__return_meta)
            else:
                return self.__return_type
        else:
            if response.status_code == 401 or response.status_code == 403: raise InvalidKey("Your key may have expired, or may not have permission to access this resource.")
            elif response.status_code == 429: raise RateLimited("You're being rate limited.")
            elif response.status_code >= 500: raise ServiceUnavailable("The service is unavailable or has encountered an error.")
            elif not response.ok: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}")
    
    def wait(self, timeout_seconds: Optional[float]=None, interval_seconds: float=0) -> T:
        start_time = time.time()
        while True:
            result = self.fetch_status()
            if result: return result

            if timeout_seconds and time.time() - start_time > timeout_seconds:
                raise TimeoutError("Timeout exceeded")

            if interval_seconds > 0: time.sleep(interval_seconds)

del Literal, Optional, TypeVar, T, requests, time, Generic

from .experience import *
from .datastore import *
from .exceptions import *
from .user import *
from .oauth2 import *
from .group import *
from .creator import *
from .webhook import *
