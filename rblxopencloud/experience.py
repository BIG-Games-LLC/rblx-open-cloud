from .exceptions import rblx_opencloudException, InvalidKey, NotFound, RateLimited, ServiceUnavailable
import io, datetime
from typing import Optional, Iterable, Literal, Union
from .datastore import DataStore, OrderedDataStore
from . import user_agent, request_session
from .user import User
from .group import Group
from enum import Enum

__all__ = (
    "Experience",
    "ExperienceAgeRating",
    "ExperienceSocialLink",
    "Place"
)

class ExperienceAgeRating(Enum):
    """
    Enum representing the an experience's age rating.
    
    Attributes:
        Unknown (0): The current experience age rating is unknown (e.g. an unimplemented age rating).
        Unspecified (1): The experience has not provided an age rating.
        AllAges (2): The experience is marked as All Ages.
        NinePlus (3): The experience is marked as 9+.
        ThirteenPlus (4): The experience is marked as 13+.
        SeventeenPlus (5): The experience is marked as 17+, and requires users to verify their age to play.
    """

    Unknown = 0
    Unspecified = 1
    AllAges = 2
    NinePlus = 3
    ThirteenPlus = 4
    SeventeenPlus = 5

class ExperienceSocialLink():
    """
    Represents a social link in an experience.
    
    Args:
        title (str): The text displayed for the social link.
        uri (str): The URI of the social link.

    Attributes:
        title (str): The text displayed for the social link.
        uri (str): The URI of the social link.
    """

    def __init__(self, title: str, uri: str) -> None:
        self.title = title
        self.uri = uri
    
    def __repr__(self) -> str:
        return f"rblxopencloud.ExperienceSocialLink(title=\"{self.title}\", uri=\"{self.uri}\")"

exeperience_age_rating_strings = {
    "AGE_RATING_UNSPECIFIED": ExperienceAgeRating.Unspecified,
    "AGE_RATING_ALL": ExperienceAgeRating.AllAges,
    "AGE_RATING_9_PLUS": ExperienceAgeRating.NinePlus,
    "AGE_RATING_13_PLUS": ExperienceAgeRating.ThirteenPlus,
    "AGE_RATING_17_PLUS": ExperienceAgeRating.SeventeenPlus,
}

class Place():
    """
    Represents a place within an experience on Roblox. Currently only holds place information, and can only be updated with [`Experience.update_place()`][rblxopencloud.Experience.update_place].
    
    !!! warning
        This class isn't designed to be created by users. It is returned by [`Experience.fetch_place()`][rblxopencloud.Experience.fetch_place], and [`Experience.update_place()`][rblxopencloud.Experience.update_place].
    
    Attributes:
        id (int): The place's ID.
        experience (Experience): The experience this place is a part of.
        name (str): The place's name.
        description (str): The place's description.
        created_at (datetime.datetime): The time the place was created.
        updated_at (datetime.datetime): The time the place was last updated.
        server_size (str): The maximum number of players that can be in a single server.
    """

    def __init__(self, data, api_key, experience) -> None:
        self.id: int = int(data['path'].split("/")[-1])
        self.experience: Experience = experience
        self.name: str = data["displayName"]
        self.description: str = data["description"]
        self.created_at: datetime.datetime = datetime.datetime.fromisoformat((data["createTime"].split("Z")[0]+("." if not "." in data["createTime"] else "")+"0"*6)[0:26])
        self.updated_at: datetime.datetime = datetime.datetime.fromisoformat((data["updateTime"].split("Z")[0]+("." if not "." in data["updateTime"] else "")+"0"*6)[0:26])
        self.server_size: str = data["serverSize"]
        self.__api_key = api_key
    
    def __repr__(self) -> str:
        return f"rblxopencloud.Place({self.id}, name={self.name}, experience={repr(self.experience)})"
        

class Experience():
    """
    Represents an experience/game on Roblox. Allows interaction with data stores, messaging service, etc.

    Args:
        id: The experience/universe ID
        api_key: The API key created on the [Creator Dashboard](https://create.roblox.com/credentials) with access to the experience.
    
    Attributes:
        id (int): The experience/universe ID
        owner (Optional[Union[User, Group]]): The object of the experience owner. Only present from OAuth2 or after using [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info]
        name (Optional[str]): The experience's name. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        description (Optional[str]): The experience's description. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        created_at (Optional[datetime.datetime]): The time the experience was created. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        updated_at (Optional[datetime.datetime]): The time the experience was last updated. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        public (Optional[bool]): Wether the game is public. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        voice_chat_enabled (Optional[bool]): Wether the game has voice chat enabled. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        age_rating (Optional[ExperienceAgeRating]: The experience's age rating. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.)
        private_server_price (Optional[int]): The price in robux of private servers, will stay `None` if private servers are disabled. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        desktop_enabled (Optional[bool]): Wether the game can be played on desktop. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        mobile_enabled (Optional[bool]): Wether the game can be played on mobile phones. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        tablet_enabled (Optional[bool]): Wether the game can be played on tablets. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        console_enabled (Optional[bool]): Wether the game can be played on consoles. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        vr_enabled (Optional[bool]): Wether the game can be played on vr headsets. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        facebook_social_link (Optional[ExperienceSocialLink]): The game's facebook social link, if there is one. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        twitter_social_link (Optional[ExperienceSocialLink]): The game's twitter social link, if there is one. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        youtube_social_link (Optional[ExperienceSocialLink]): The game's youtube social link, if there is one. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        twitch_social_link (Optional[ExperienceSocialLink]): The game's twitch social link, if there is one. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        discord_social_link (Optional[ExperienceSocialLink]): The game's discord social link, if there is one. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        group_social_link (Optional[ExperienceSocialLink]): The game's group social link, if there is one. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
        guilded_social_link (Optional[ExperienceSocialLink]): The game's guilded social link, if there is one. Only present after [`Experience.fetch_info()`][rblxopencloud.Experience.fetch_info] is called.
    """

    def __init__(self, id: int, api_key: str):
        self.id: int = id
        self.__api_key: str = api_key

        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.created_at: Optional[datetime.datetime] = None
        self.updated_at: Optional[datetime.datetime] = None
        self.owner: Optional[Union[User, Group]] = None
        self.public: Optional[bool] = None
        self.voice_chat_enabled: Optional[bool] = None
        self.age_rating: Optional[ExperienceAgeRating] = None
        self.private_server_price: Optional[int] = None
        self.desktop_enabled: Optional[bool] = None
        self.mobile_enabled: Optional[bool] = None
        self.tablet_enabled: Optional[bool] = None
        self.console_enabled: Optional[bool] = None
        self.vr_enabled: Optional[bool] = None

        self.facebook_social_link: Optional[ExperienceSocialLink] = None
        self.twitter_social_link: Optional[ExperienceSocialLink] = None
        self.youtube_social_link: Optional[ExperienceSocialLink] = None
        self.twitch_social_link: Optional[ExperienceSocialLink] = None
        self.discord_social_link: Optional[ExperienceSocialLink] = None
        self.group_social_link: Optional[ExperienceSocialLink] = None
        self.guilded_social_link: Optional[ExperienceSocialLink] = None
    
    def __repr__(self) -> str:
        return f"rblxopencloud.Experience({self.id})"
    
    def __update_params(self, data):
        self.name = data["displayName"]
        self.description = data["description"]
        self.created_at = datetime.datetime.fromisoformat((data["createTime"].split("Z")[0]+("." if not "." in data["createTime"] else "")+"0"*6)[0:26])
        self.updated_at = datetime.datetime.fromisoformat((data["updateTime"].split("Z")[0]+("." if not "." in data["updateTime"] else "")+"0"*6)[0:26])
        if data.get("user"):
            self.owner = User(int(data["user"].split("/")[1]), self.__api_key)
        elif data.get("group"):
            self.owner = Group(int(data["group"].split("/")[1]), self.__api_key)
        
        self.public = data["visibility"] == "PUBLIC"
        self.voice_chat_enabled = data["voiceChatEnabled"]
        self.age_rating = exeperience_age_rating_strings.get(data["ageRating"], ExperienceAgeRating.Unknown)
        self.private_server_price = data.get("privateServerPriceRobux", None)

        if data.get("facebookSocialLink"): self.facebook_social_link = ExperienceSocialLink(
                data["facebookSocialLink"]["title"], data["facebookSocialLink"]["uri"])
            
        if data.get("twitterSocialLink"): self.twitter_social_link = ExperienceSocialLink(
                data["twitterSocialLink"]["title"], data["twitterSocialLink"]["uri"])
        
        if data.get("youtubeSocialLink"): self.youtube_social_link = ExperienceSocialLink(
                data["youtubeSocialLink"]["title"], data["youtubeSocialLink"]["uri"])
            
        if data.get("twitchSocialLink"): self.twitch_social_link = ExperienceSocialLink(
                data["twitchSocialLink"]["title"], data["twitchSocialLink"]["uri"])
            
        if data.get("discordSocialLink"): self.discord_social_link = ExperienceSocialLink(
                data["discordSocialLink"]["title"], data["discordSocialLink"]["uri"])
            
        if data.get("robloxGroupSocialLink"): self.group_social_link = ExperienceSocialLink(
                data["robloxGroupSocialLink"]["title"], data["robloxGroupSocialLink"]["uri"])
            
        if data.get("guildedSocialLink"): self.guilded_social_link = ExperienceSocialLink(
                data["guildedSocialLink"]["title"], data["guildedSocialLink"]["uri"])
            
        self.desktop_enabled = data["desktopEnabled"]
        self.mobile_enabled = data["mobileEnabled"]
        self.tablet_enabled = data["tabletEnabled"]
        self.console_enabled = data["consoleEnabled"]
        self.vr_enabled = data["vrEnabled"]
    
    def fetch_info(self) -> "Experience":
        """
        Updates the empty attributes in the class with the experience info.

        Returns:
            The class itself.

        Raises:
            InvalidKey: The API key isn't valid, or is from an invalid IP address.
            NotFound: The group does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """

        response = request_session.get(f"https://apis.roblox.com/cloud/v2/universes/{self.id}",
            headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent})
        
        if response.status_code == 401: raise InvalidKey(response.text)
        elif response.status_code == 404: raise NotFound(response.json()['message'])
        elif response.status_code == 429: raise RateLimited("You're being rate limited!")
        elif response.status_code >= 500: raise ServiceUnavailable(f"Internal Server Error: '{response.text}'")
        elif not response.ok: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}: '{response.text}'")
        
        self.__update_params(response.json())
        return self
    
    def update(self, voice_chat_enabled: Optional[bool] = None, private_server_price: Optional[Union[int, bool]] = None,
            desktop_enabled: Optional[bool] = None, mobile_enabled: Optional[bool] = None,
            tablet_enabled: Optional[bool] = None, console_enabled: Optional[bool] = None,
            vr_enabled: Optional[bool] = None,
            facebook_social_link: Optional[Union[ExperienceSocialLink, bool]] = None,
            twitter_social_link: Optional[Union[ExperienceSocialLink, bool]] = None,
            youtube_social_link: Optional[Union[ExperienceSocialLink, bool]] = None,
            twitch_social_link: Optional[Union[ExperienceSocialLink, bool]] = None,
            discord_social_link: Optional[Union[ExperienceSocialLink, bool]] = None,
            group_social_link: Optional[Union[ExperienceSocialLink, bool]] = None,
            guilded_social_link: Optional[Union[ExperienceSocialLink, bool]] = None):
        """
        Updates the experience, and update's the classes attributes.

        **The `universe:write` scope is required for OAuth2 authorization.**

        Args:
            voice_chat_enabled: Wether voice chat should be enabled in the experience.
            private_server_price: The price in robux for the private server price. Set this to `False` to disable private servers.
            desktop_enabled: Wether the experience can be played on desktop devices.
            mobile_enabled: Wether the experience can be played on mobile phones.
            console_enabled: Wether the experience can be played on consoles.
            vr_enabled: Wether the experience can be played on vr headsets.
            facebook_social_link: A [`rblxopencloud.ExperienceSocialLink`][rblxopencloud.ExperienceSocialLink] for the experience's facebook social link.
            twitter_social_link: A [`rblxopencloud.ExperienceSocialLink`][rblxopencloud.ExperienceSocialLink] for the experience's twitter or 'X' social link.
            youtube_social_link: A [`rblxopencloud.ExperienceSocialLink`][rblxopencloud.ExperienceSocialLink] for the experience's youtube social link.
            twitch_social_link: A [`rblxopencloud.ExperienceSocialLink`][rblxopencloud.ExperienceSocialLink] for the experience's twitch social link.
            discord_social_link: A [`rblxopencloud.ExperienceSocialLink`][rblxopencloud.ExperienceSocialLink] for the experience's discord social link.
            group_social_link: A [`rblxopencloud.ExperienceSocialLink`][rblxopencloud.ExperienceSocialLink] for the experience's group social link.
            guilded_social_link: A [`rblxopencloud.ExperienceSocialLink`][rblxopencloud.ExperienceSocialLink] for the experience's guilded social link.

        Returns:
            The class itself.

        Raises:
            InvalidKey: The API key isn't valid, or is from an invalid IP address.
            NotFound: The group does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        
        !!! tip
            To update the experience's name or description use [`Experience.update_place`][rblxopencloud.Experience.update_place] on the experience's start place.
        """

        new_experience, field_mask = {}, []

        if voice_chat_enabled != None:
            new_experience["voiceChatEnabled"] = voice_chat_enabled
            field_mask.append("voiceChatEnabled")

        if private_server_price != None:
            if private_server_price == True:
                raise ValueError("private_server_robux_price should be either int or False.")

            if type(private_server_price) == int:
                new_experience["privateServerPriceRobux"] = private_server_price
            
            field_mask.append("privateServerPriceRobux")

        for platform, value in {
            "facebook": facebook_social_link,
            "twitter": twitter_social_link,
            "youtube": youtube_social_link,
            "twitch": twitch_social_link,
            "discord": discord_social_link,
            "robloxGroup": group_social_link,
            "guilded": guilded_social_link
        }.items():
            if value != None:
                if value == True:
                    raise ValueError(f"{platform}_social_link should be either ExperienceSocialLink or False.")

                if type(value) == ExperienceSocialLink:
                    new_experience[f"{platform}SocialLink"] = {
                        "title": value.title,
                        "uri": value.uri
                    }
                    field_mask.append(f"{platform}SocialLink.title")
                    field_mask.append(f"{platform}SocialLink.uri")
                else:
                    field_mask.append(f"{platform}SocialLink")

        for platform, value in {
            "desktop": desktop_enabled,
            "mobile": mobile_enabled,
            "tablet": tablet_enabled,
            "console": console_enabled,
            "vr": vr_enabled
        }.items():
            if value != None:
                new_experience[f"{platform}Enabled"] = value
                field_mask.append(f"{platform}Enabled")
        
        response = request_session.patch(f"https://apis.roblox.com/cloud/v2/universes/{self.id}",
            headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent},
            json=new_experience, params={"updateMask": ",".join(field_mask)})
                        
        if response.status_code == 401: raise InvalidKey(response.text)
        elif response.status_code == 404: raise NotFound(response.json()['message'])
        elif response.status_code == 429: raise RateLimited("You're being rate limited!")
        elif response.status_code >= 500: raise ServiceUnavailable(f"Internal Server Error: '{response.text}'")
        elif not response.ok: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}: '{response.text}'")
        
        self.__update_params(response.json())
    
    def get_data_store(self, name: str, scope: Optional[str]="global") -> DataStore:
        """
        Creates a [`rblxopencloud.DataStore`][rblxopencloud.DataStore] with the provided name and scope. This function doesn't make an API call so there is no validation.

        Args:
            name: The data store name.
            scope: The data store scope. Set it to none for `scope/key` syntax.
        
        Returns:
            The Data Store with the provided name and scope.
        """
        return DataStore(name, self, self.__api_key, None, scope)
    
    def get_ordered_data_store(self, name: str, scope: Optional[str]="global") -> OrderedDataStore:
        """
        Creates a [`rblxopencloud.OrderedDataStore`][rblxopencloud.OrderedDataStore] with the provided name and scope. This function doesn't make an API call so there is no validation.

        Args:
            name: The data store name.
            scope: The data store scope. Set it to none for `scope/key` syntax.

        Returns:
            The Ordered Data Store with the provided name and scope.
        """
        return OrderedDataStore(name, self, self.__api_key, scope)

    def list_data_stores(self, prefix: Optional[str]="", limit: Optional[int]=None, scope: Optional[Union[str, None]]="global") -> Iterable[DataStore]:
        """
        Interates [`rblxopencloud.DataStore`][rblxopencloud.DataStore] for all of the Data Stores in the experience.

        Example:
            This will print every data store in the experience. 
            ```py
            for datastore in experience.list_data_stores():
                print(datastore)
            ```
            If you'd like the datastores in a list, you can use the list method:
            ```py
            list(experience.list_data_stores())
            ```

        Args:
            prefix: Only return Data Stores with names starting with this value.
            limit: The maximum number of Data Stores to iterate.
            scope: The scope for all data stores. Defaults to global, and can be `None` for key syntax like `scope/key`.
        
        Returns:
            An Iterable of every [`rblxopencloud.DataStore`][rblxopencloud.DataStore] in the experience.

        Raises:
            InvalidKey: The API key isn't valid, doesn't have access to list data stores, or is from an invalid IP address.
            NotFound: The experience does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """
        nextcursor = ""
        yields = 0
        while limit == None or yields < limit:
            response = request_session.get(f"https://apis.roblox.com/datastores/v1/universes/{self.id}/standard-datastores",
                headers={"x-api-key": self.__api_key}, params={
                    "prefix": prefix,
                    "cursor": nextcursor if nextcursor else None
                })
            if response.status_code == 401: raise InvalidKey("Your key may have expired, or may not have permission to access this resource.")
            elif response.status_code == 404: raise NotFound("The datastore you're trying to access does not exist.")
            elif response.status_code == 429: raise RateLimited("You're being rate limited.")
            elif response.status_code >= 500: raise ServiceUnavailable("The service is unavailable or has encountered an error.")
            elif not response.ok: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}")
            
            data = response.json()
            for datastore in data["datastores"]:
                yields += 1
                yield DataStore(datastore["name"], self, self.__api_key, datastore["createdTime"], scope)
                if limit == None or yields >= limit: break
            nextcursor = data.get("nextPageCursor")
            if not nextcursor: break
    
    def publish_message(self, topic: str, data: str) -> None:
        """
        Publishes a message to live game servers that can be recieved with [MessagingService](https://create.roblox.com/docs/reference/engine/classes/MessagingService).

        **The `universe-messaging-service:publish` scope is required for OAuth2 authorization.**

        Args:
            topic: The topic to send the message in
            data: The message to send. Open Cloud does not support sending dictionaries/tables with publishing messages. You'll have to json encode it before sending it, and decode it in Roblox.
        
        Raises:
            InvalidKey: The API key isn't valid, doesn't have access to publish messages, or is from an invalid IP address.
            NotFound: The experience does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        
        !!! note
            Messages sent by Open Cloud with only be recieved by live servers. Studio won't recieve thesse messages.
        """
        response = request_session.post(f"https://apis.roblox.com/messaging-service/v1/universes/{self.id}/topics/{topic}",
        json={"message": data}, headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent})
        if response.status_code == 200: return
        elif response.status_code == 401: raise InvalidKey("Your key may have expired, or may not have permission to access this resource.")
        elif response.status_code == 404: raise NotFound(f"The place does not exist.")
        elif response.status_code == 429: raise RateLimited("You're being rate limited.")
        elif response.status_code >= 500: raise ServiceUnavailable("The service is unavailable or has encountered an error.")
        else: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}")  

    def restart_servers(self) -> None:
        """
        Shutdowns all game servers in the experience which are not on the latest published version. It takes 1 to 6 minutes for all required servers to be shutdown. It is similar to the 'Migrate To Latest Update' button on the game page.

        **The `universe:write` scope is required for OAuth2 authorization.**

        Raises:
            InvalidKey: The API key isn't valid, doesn't have access to write experiences, or is from an invalid IP address.
            NotFound: The experience does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """
        response = request_session.post(f"https://apis.roblox.com/cloud/v2/universes/{self.id}:restartServers", json={},
            headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent})

        if response.status_code == 200: return
        elif response.status_code == 401: raise InvalidKey("Your key may have expired, or may not have permission to access this resource.")
        elif response.status_code == 404: raise NotFound(f"The place does not exist.")
        elif response.status_code == 429: raise RateLimited("You're being rate limited.")
        elif response.status_code >= 500: raise ServiceUnavailable("The service is unavailable or has encountered an error.")
        else: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}")  
        
    def fetch_place(self, place_id:int) -> Place:
        """
        Fetches the information of a place within the expereince.

        Args:
            place_id: The place ID to fetch information for.

        Returns:
            The place information.
        
        Raises:
            InvalidKey: The API key isn't valid, or is from an invalid IP address.
            NotFound: The experience or place does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """
        response = request_session.get(f"https://apis.roblox.com/cloud/v2/universes/{self.id}/places/{place_id}",
            headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent})
        
        if response.status_code == 401: raise InvalidKey(response.text)
        elif response.status_code == 404: raise NotFound(response.json()['message'])
        elif response.status_code == 429: raise RateLimited("You're being rate limited!")
        elif response.status_code >= 500: raise ServiceUnavailable(f"Internal Server Error: '{response.text}'")
        elif not response.ok: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}: '{response.text}'")
        
        return Place(response.json(), self.__api_key, self)
    
    def update_place(self, place_id: int, name: Optional[str]=None, description: Optional[str]=None, server_size: Optional[int]=None) -> Place:
        """
        Updates information for a place within the experience.

        **The `universe.place:write` scope is required for OAuth2 authorization.**

        Args:
            place_id: The place ID to update.
            name: The new name for the place. If it is the start place, this will update the experience's name.
            description: The new description for the place. If it is the start place, this will update the experience's description.
            server_size: The new server size for the place.
        
        Returns:
            The updated place information.
        
        Raises:
            InvalidKey: The API key isn't valid, doesn't have access to write places, or is from an invalid IP address.
            NotFound: The experience or place does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """

        new_experience, field_mask = {}, []

        if name != None:
            new_experience["displayName"] = name
            field_mask.append("displayName")

        if description != None:
            new_experience["description"] = description
            field_mask.append("description")

        if server_size != None:
            new_experience["serverSize"] = server_size
            field_mask.append("serverSize")
        
        print("[DEBUG]", new_experience, field_mask)

        response = request_session.patch(f"https://apis.roblox.com/cloud/v2/universes/{self.id}/places/{place_id}",
            headers={"x-api-key" if not self.__api_key.startswith("Bearer ") else "authorization": self.__api_key, "user-agent": user_agent},
            json=new_experience, params={"updateMask": ",".join(field_mask)})
        
        print("[DEBUG]", response.status_code, response.request.path_url, f"\n{response.json()}")
                        
        if response.status_code == 401: raise InvalidKey(response.text)
        elif response.status_code == 404: raise NotFound(response.json()['message'])
        elif response.status_code == 429: raise RateLimited("You're being rate limited!")
        elif response.status_code >= 500: raise ServiceUnavailable(f"Internal Server Error: '{response.text}'")
        elif not response.ok: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}: '{response.text}'")
        
        return Place(response.json(), self.__api_key, self)

    def upload_place(self, place_id:int, file: io.BytesIO, publish: Optional[bool] = False) -> int:
        """
        Uploads the place file to Roblox, optionally choosing to publish it.

        Example:
            Replace `0000000` with the target place's ID, and `example.rbxl` should be the path to the roblox place file.
            ```py
            with open("example.rbxl", "rb") as file:
                experience.upload_place(0000000, file, publish=False)
            ```

        Args:
            place_id: The place ID to upload the file to.
            file: The place file to upload, opened in bytes.
            publish: Wether to publish the new place file.

        Returns:
            The place's new version ID.
        
        Raises:
            InvalidKey: The API key isn't valid, doesn't have access to publish places, or is from an invalid IP address.
            NotFound: The experience does not exist.
            RateLimited: You've exceeded the rate limits.
            ServiceUnavailable: The Roblox servers ran into an error, or are unavailable right now.
            rblx_opencloudException: Roblox returned an unexpected error.
        """
        response = request_session.post(f"https://apis.roblox.com/universes/v1/{self.id}/places/{place_id}/versions",
            headers={"x-api-key": self.__api_key, 'content-type': 'application/octet-stream', "user-agent": user_agent}, data=file.read(), params={
                "versionType": "Published" if publish else "Saved"
            })
        if response.status_code == 200:
            return response.json()["versionNumber"]
        elif response.status_code == 401: raise InvalidKey("Your key may have expired, or may not have permission to access this resource.")
        elif response.status_code == 404: raise NotFound(f"The place does not exist.")
        elif response.status_code == 429: raise RateLimited("You're being rate limited.")
        elif response.status_code >= 500: raise ServiceUnavailable("The service is unavailable or has encountered an error.")
        else: raise rblx_opencloudException(f"Unexpected HTTP {response.status_code}")   