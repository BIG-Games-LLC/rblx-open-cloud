from .exceptions import rblx_opencloudException, InvalidKey, NotFound, RateLimited, ServiceUnavailable, PreconditionFailed
import urllib.parse, datetime, json
from typing import Union, Optional, Iterable, TYPE_CHECKING
from . import user_agent, request_session

if TYPE_CHECKING:
    from .experience import Experience

__all__ = (
    "SortedMap",
    "SortedMapEntry",
    "MemoryStoreQueue"
)

class SortedMapEntry():
    """
    Represents an entry in a sorted map.

    !!! warning
        This class isn't designed to be created by users. It is returned by [`SortedMap.get()`][rblxopencloud.SortedMap.get] and [`SortedMap.set()`][rblxopencloud.SortedMap.set].

    Attributes:
        key (str): The entry's key.
        scope (str): The entry's scope.
        value (int): The value of the entry.
    """
    def __init__(self, data) -> None:
        self.key: str = data["id"]
        self.sort_key: Optional[Union[int, str]] = data.get("numericSortKey") or data.get("stringSortKey")
        self.value: int = data["value"]
        self.etag: str = data["etag"]
        self.expires_at: datetime.datetime = datetime.datetime.fromisoformat((data["expireTime"].split("Z")[0]+("" if "." in data["expireTime"] else ".")+"0"*6)[0:26])
    
    def __repr__(self) -> str:
        return f"rblxopencloud.SortedMapEntry(\"{self.key}\", value={json.dumps(self.value)})"

class SortedMap():
    """
    Represents a sorted map memory store in an experience.

    !!! warning
        This class isn't designed to be created by users. It is returned by [`Experience.get_sorted_map()`][rblxopencloud.Experience.get_sorted_map].

    Attributes:
        name (str): The sorted map's name.
        experience (Experience): The experience the data store belongs to.
    """

    def __init__(self, name, experience, api_key):
        self.name: str = name
        self.__api_key: str = api_key
        self.experience: Experience = experience
    
    def __repr__(self) -> str:
        return f"rblxopencloud.SortedMap(\"{self.name}\", experience={repr(self.experience)})"
    
    def __str__(self) -> str:
        return self.name

    def list_keys(self, descending: bool=False, limit: Optional[int]=None,
        lower_bound_key: Optional[Union[str, int]]=None, upper_bound_key: Optional[Union[str, int]]=None,
        lower_bound_sort_key: Optional[Union[str, int]]=None, upper_bound_sort_key: Optional[Union[str, int]]=None
        ) -> Iterable[SortedMapEntry]:
        """
        Returns an Iterable of keys in the sorted map.

        Args:
            descending: Wether to return keys in descending order. When false, keys are returned in ascending order.
            limit: Will not return more keys than this number. Set to `None` for no limit.
            lower_bound_key: Only return values with key names greater than this value.
            upper_bound_key: Only return values with key names less than this value.
            lower_bound_sort_key: Only return values with sort keys greater than this value.
            upper_bound_sort_key: Only return values with sort keys less than this value.
            
        Returns:
            An Iterable of all keys in the sorted map.
        
        Raises:
            InvalidKey: The API key isn't valid, doesn't have access to list data store keys, or is from an invalid IP address.
            NotFound: The experience or data store does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """
        filter = []

        if lower_bound_key:
            if type(lower_bound_key) == str: lower_bound_key = f"\"{lower_bound_key}\""
            filter.append(f"id > {lower_bound_key}")
        
        if upper_bound_key:
            if type(upper_bound_key) == str: upper_bound_key = f"\"{upper_bound_key}\""
            filter.append(f"id < {upper_bound_key}")

        if lower_bound_sort_key:
            if type(lower_bound_sort_key) == str: lower_bound_sort_key = f"\"{lower_bound_sort_key}\""
            filter.append(f"sortKey > {lower_bound_sort_key}")
        
        if upper_bound_sort_key:
            if type(upper_bound_sort_key) == str: upper_bound_sort_key = f"\"{upper_bound_sort_key}\""
            filter.append(f"sortKey < {upper_bound_sort_key}")
        print(" && ".join(filter))
        nextcursor = ""
        yields = 0
        while limit == None or yields < limit:
            response = request_session.get(f"https://apis.roblox.com/cloud/v2/universes/{self.experience.id}/memory-store/sorted-maps/{urllib.parse.quote_plus(self.name)}/items",
                headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent}, params={
                "pageToken": nextcursor if nextcursor else None,
                "orderBy": "desc" if descending else None,
                "maxPageSize": limit if limit and limit < 100 else 100,
                "filter": " && ".join(filter)
            })
            if response.status_code == 400: raise rblx_opencloudException(response.json()["message"])
            elif response.status_code == 401: raise InvalidKey(response.text)
            elif response.status_code == 403: raise InvalidKey(response.json()["message"])
            elif response.status_code == 404: raise NotFound(response.json()["message"])
            elif response.status_code == 429: raise RateLimited(response.json()["message"])
            elif response.status_code >= 500: raise ServiceUnavailable(f"Internal Server Error: '{response.text}'")
            elif not response.ok: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}: '{response.text}'")

            data = response.json()
            for item in data["items"]:
                yields += 1
                yield SortedMapEntry(item)
                if limit != None and yields >= limit: break
            nextcursor = data.get("nextPageToken")
            if not nextcursor: break

    def get(self, key: str) -> SortedMapEntry:
        """
        Fetches the value of a key.

        Args:
            key: The key to find.
        
        Returns:
            The entry information such as value, expiration time, and sort key. 
        
        Raises:
            InvalidKey: The API key isn't valid, doesn't have access to read memory store sorted maps, or is from an invalid IP address.
            NotFound: The experience does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """
        
        response = request_session.get(f"https://apis.roblox.com/cloud/v2/universes/{self.experience.id}/memory-store/sorted-maps/{urllib.parse.quote_plus(self.name)}/items/{urllib.parse.quote_plus(key)}",
            headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent})

        if response.ok: return SortedMapEntry(response.json())
        elif response.status_code == 400: raise rblx_opencloudException(response.json()["message"])
        elif response.status_code == 401: raise InvalidKey(response.text)
        elif response.status_code == 403: raise InvalidKey(response.json()["message"])
        elif response.status_code == 404: raise NotFound(response.json()["message"])
        elif response.status_code == 429: raise RateLimited(response.json()["message"])
        elif response.status_code >= 500: raise ServiceUnavailable(f"Internal Server Error: '{response.text}'")
        else: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}: '{response.text}'")

    def set(self, key: str, value: Union[str, dict, list, int, float], expiration_seconds: int, sort_key: Optional[Union[int, float, str]]=None, exclusive_create: bool=False, exclusive_update: bool=False):        
        """
        Creates or updates the provided key.

        Args:
            key: The key to be created or updated.
            value: Only delete if the current [SortedMapEntry.etag] is the same as the provided value.
            expiration_seconds: The number of seconds for the entry to live. Can not be greater than 3888000 seconds.
            sort_key: The key used for sorting. Check the [Roblox documentation](https://create.roblox.com/docs/cloud-services/memory-stores/sorted-map#adding-or-overwriting-data) for more.
            exclusive_create: Wether to fail if the key already has a value.
            exclusive_update: Wether to fail if the key doesn't have a value.
        
        Returns:
            The new entry information such as value, expiration time, and sort key. 
        
        Raises:
            ValueError: Both `exclusive_create` and `exclusive_update` are `True`
            InvalidKey: The API key isn't valid, doesn't have access to write memory store sorted maps, or is from an invalid IP address.
            NotFound: The experience does not exist.
            PreconditionFailed: `exclusive_create` or `exclusive_update` preconditions failed.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """
        if exclusive_create and exclusive_update: raise ValueError("exclusive_create and exclusive_updated can not both be True")

        if not exclusive_create:
            response = request_session.patch(f"https://apis.roblox.com/cloud/v2/universes/{self.experience.id}/memory-store/sorted-maps/{urllib.parse.quote_plus(self.name)}/items/{urllib.parse.quote_plus(key)}",
                headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent}, params={"allowMissing": str(not exclusive_update).lower()}, json={
                    "Value": value,
                    "Ttl": f"{expiration_seconds}s",
                    "stringSortKey" if type(sort_key) == str else "numericSortKey": sort_key
                })
        else:
            response = request_session.post(f"https://apis.roblox.com/cloud/v2/universes/{self.experience.id}/memory-store/sorted-maps/{urllib.parse.quote_plus(self.name)}/items",
                headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent}, json={
                    "Id": key,
                    "Value": value,
                    "Ttl": f"{expiration_seconds}s",
                    "stringSortKey" if type(sort_key) == str else "numericSortKey": sort_key
                })

        if response.ok:
            data = response.json()
            if not data.get("id"):
                data["id"] = key
            return SortedMapEntry(data)
        elif response.status_code == 409:
            if response.json()["error"] == "ALREADY_EXISTS":
                raise PreconditionFailed(None, None, response.json()["message"])
            else:
                raise rblx_opencloudException(response.json()["message"])
        elif response.status_code == 404 and exclusive_update:
            raise PreconditionFailed(None, None, response.json()["message"])
        elif response.status_code == 400: raise rblx_opencloudException(response.json()["message"])
        elif response.status_code == 401: raise InvalidKey(response.text)
        elif response.status_code == 403: raise InvalidKey(response.json()["message"])
        elif response.status_code == 429: raise RateLimited(response.json()["message"])
        elif response.status_code >= 500: raise ServiceUnavailable(f"Internal Server Error: '{response.text}'")
        else: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}: '{response.text}'")
    
    def remove(self, key: str, etag: Optional[str]=None) -> None:
        """
        Deletes a key from the sorted map.

        Args:
            key: The key to remove.
            etag: Only delete if the current [SortedMapEntry.etag] is the same as the provided value.
        
        Raises:
            InvalidKey: The API key isn't valid, doesn't have access to write memory store sorted maps, or is from an invalid IP address.
            NotFound: The experience does not exist.
            PreconditionFailed: The provided `etag` is not the current etag.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """
        
        response = request_session.delete(f"https://apis.roblox.com/cloud/v2/universes/{self.experience.id}/memory-store/sorted-maps/{urllib.parse.quote_plus(self.name)}/items/{urllib.parse.quote_plus(key)}",
            headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent}, params={"etag": etag})

        if response.ok: return None
        elif response.status_code == 400: raise rblx_opencloudException(response.json()["message"])
        elif response.status_code == 401: raise InvalidKey(response.text)
        elif response.status_code == 403: raise InvalidKey(response.json()["message"])
        elif response.status_code == 404: raise NotFound(response.json()["message"])
        elif response.status_code == 409 and response.json()["error"] == "ABORTED":
            raise PreconditionFailed(None, None, response.json()["message"])
        elif response.status_code == 429: raise RateLimited(response.json()["message"])
        elif response.status_code >= 500: raise ServiceUnavailable(f"Internal Server Error: '{response.text}'")
        else: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}: '{response.text}'")

class MemoryStoreQueue():
    """
    Represents a memory store queue in an experience.

    !!! warning
        This class isn't designed to be created by users. It is returned by [`Experience.get_memory_store_queue()`][rblxopencloud.Experience.get_memory_store_queue].

    Attributes:
        name (str): The queue's name.
        experience (Experience): The experience the queue belongs to.
    """

    def __init__(self, name, experience, api_key):
        self.name: str = name
        self.__api_key: str = api_key
        self.experience: Experience = experience
    
    def __repr__(self) -> str:
        return f"rblxopencloud.MemoryStoreQueue(\"{self.name}\", experience={repr(self.experience)})"
    
    def __str__(self) -> str:
        return self.name

    def add(self, value: Union[str, dict, list, int, float], expiration_seconds: int=30, priority: float=0) -> None:
        """
        Adds a value to the queue.

        Args:
            value: The value to be added to the queue.
            expiration_seconds: The number of seconds for the value to stay in the queue.
            priority: The value's priority. Keys with higher priorities leave the queue first.
                
        Raises:
            InvalidKey: The API key isn't valid, doesn't have access to add queue items, or is from an invalid IP address.
            NotFound: The experience does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """
        
        response = request_session.post(f"https://apis.roblox.com/cloud/v2/universes/{self.experience.id}/memory-store/queues/{urllib.parse.quote_plus(self.name)}/items:add",
            headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent}, json={
                "Data": value,
                "Ttl": f"{expiration_seconds}s",
                "Priority": priority
            })

        if response.ok: return None
        elif response.status_code == 400: raise rblx_opencloudException(response.json()["message"])
        elif response.status_code == 401: raise InvalidKey(response.text)
        elif response.status_code == 403: raise InvalidKey(response.json()["message"])
        elif response.status_code == 429: raise RateLimited(response.json()["message"])
        elif response.status_code >= 500: raise ServiceUnavailable(f"Internal Server Error: '{response.text}'")
        else: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}: '{response.text}'")
    
    def read(self, count: int=1, all_or_nothing: bool=False, invisibility_seconds: int=30) -> tuple[list[Union[str, dict, list, int, float]], Optional[str]]:
        """
        Reads values from the queue.

        Args:
            count: The number of values to return
            all_or_nothing: Wether to return nothing if there isn't enough values in the queue to fullfill the reuqested `count`.
            invisibility_seconds: The number of seconds the keys should be invisible from further read requests.
        
        Returns:
            A tuple with a list of values as the first parameter, and a readid string as the second parameter. The read ID string can be used on [`MemoryStoreQueue.remove()`][rblxopencloud.MemoryStoreQueue.remove] When the second parameter is `None`, then they are no values to be removed.

        Raises:
            InvalidKey: The API key isn't valid, doesn't have access to read queue items, or is from an invalid IP address.
            NotFound: The experience does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """

        response = request_session.get(f"https://apis.roblox.com/cloud/v2/universes/{self.experience.id}/memory-store/queues/{urllib.parse.quote_plus(self.name)}/items:read",
            headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent}, params={
                "count": count,
                "allOrNothing": all_or_nothing,
                "invisibilityTimeoutSeconds": invisibility_seconds
            }, json={})
        
        if response.status_code == 200: return response.json()["data"], response.json()["id"]
        elif response.status_code == 204: return [], None
        elif response.status_code == 400: raise rblx_opencloudException(response.json()["message"])
        elif response.status_code == 401: raise InvalidKey(response.text)
        elif response.status_code == 403: raise InvalidKey(response.json()["message"])
        elif response.status_code == 429: raise RateLimited(response.json()["message"])
        elif response.status_code >= 500: raise ServiceUnavailable(f"Internal Server Error: '{response.text}'")
        else: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}: '{response.text}'")

    def remove(self, read_id: str) -> None:
        """
        Permanently removes previously read values from the queue. 

        Args:
            read_id: The read ID returned by [`MemoryStoreQueue.read()`][rblxopencloud.MemoryStoreQueue.read]
        
        Raises:
            InvalidKey: The API key isn't valid, doesn't have access to discard queue items, or is from an invalid IP address.
            NotFound: The experience does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """

        response = request_session.post(f"https://apis.roblox.com/cloud/v2/universes/{self.experience.id}/memory-store/queues/{urllib.parse.quote_plus(self.name)}/items:discard",
            headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent}, params={
                "readId": read_id
            }, json={})

        if response.status_code == 200: return None
        elif response.status_code == 400: raise rblx_opencloudException(response.json()["message"])
        elif response.status_code == 401: raise InvalidKey(response.text)
        elif response.status_code == 403: raise InvalidKey(response.json()["message"])
        elif response.status_code == 429: raise RateLimited(response.json()["message"])
        elif response.status_code >= 500: raise ServiceUnavailable(f"Internal Server Error: '{response.text}'")
        else: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}: '{response.text}'")