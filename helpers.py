from load_variables import *
import boto3
import discord
import hashlib
import html
import io
import json
import logging
import magic
import os
import PIL.Image
import praw
import re
import requests
import time
import urllib.parse

class LoggingHelper:
    def __init__(self) -> None:
        self.__logger = logging.getLogger("ReScrapper")
        self.__logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        self.__setup_log_file()
        file_handler = logging.FileHandler(filename='events.log', mode='a')
        stream_handler = logging.StreamHandler()

        file_handler.setLevel(logging.DEBUG)
        stream_handler.setLevel(logging.INFO)

        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        self.__logger.addHandler(file_handler)
        self.__logger.addHandler(stream_handler)

    def __setup_log_file(self) -> None:
        if os.path.isfile("events.log"):
            with open("events.log", "a") as out:
                out.write("\n\n")
        
        with open("events.log", "a") as out:
            out.write(self.__emphasize("ReScrapper Event Logs"))
            out.write(self.__emphasize(f"Logger created at {time.ctime()}"))
            out.write("\n")

    def __emphasize(self, string:str) -> str:
        return ">>>"+string.center(60)+"<<<\n"

    def debug(self, prefix:str, message:str) -> None:
        self.__logger.debug(f"{prefix} - {message}")

    def info(self, prefix:str, message:str) -> None:
        self.__logger.info(f"{prefix} - {message}")

    def error(self, prefix:str, message:str) -> None:
        self.__logger.error(f"{prefix} - {message}")

class RequestsHelper:
    def __init__(self, logger:LoggingHelper) -> None:
        '''Requires an existing LoggingHelper object.'''
        self.__logger = logger
    
    def get(self, resource_url:str) -> requests.Response|None:
        '''GET Request, returns Response if no errors, None otherwise.'''
        get_headers = GET_HEADERS
        blacklist = ["https://i.imgur.com/removed.png"]
        resource_obtained = False
        attempts_till_now = 0
        self.__logger.debug("Requests", f"Sending GET request to URL: {resource_url}")
        try:
            while (not resource_obtained) and (attempts_till_now < GET_ATTEMPTS):
                self.__logger.debug("Requests", f"Current attempt: {attempts_till_now+1}/{GET_ATTEMPTS}")
                response = requests.get(resource_url, headers=get_headers)
                for blacklisted_url in blacklist:
                    if response.url == blacklisted_url:
                        return None
                if response.status_code == 200:
                    resource_obtained = True
                    break
                else:
                    self.__logger.debug("Requests", f"Attempt unsuccessful, retrying in {SLEEP_ON_FAILED_GET} seconds.")
                    attempts_till_now += 1
                    time.sleep(SLEEP_ON_FAILED_GET)
        except Exception as error:
            self.__logger.error("Requests", error)
            return None
        else:
            if resource_obtained:
                self.__logger.info("Requests", "Resource obtained successfully.")
                return response
            else:
                self.__logger.error("Requests", "Failure obtaining resource.")
                return None

    def post(self, api_url:str, files=None, data=None) -> requests.Response|None:
        '''POST Request, returns Response if no errors, None otherwise.'''
        post_headers = POST_HEADERS
        resource_sent = False
        attempts_till_now = 0
        self.__logger.debug("Requests", f"Sending POST request to Telegram API")
        try:
            while (not resource_sent) and (attempts_till_now < POST_ATTEMPTS):
                self.__logger.debug("Requests", f"Current attempt: {attempts_till_now+1}/{POST_ATTEMPTS}")
                response = requests.post(api_url, files=files, data=data, headers=post_headers)
                if response.status_code == 200:
                    resource_sent = True
                    break
                else:
                    self.__logger.debug("Requests", f"Attempt unsuccessful, retrying in {SLEEP_ON_FAILED_POST} seconds.")
                    attempts_till_now += 1
                    time.sleep(SLEEP_ON_FAILED_POST)
        except Exception as error:
            self.__logger.error("Requests", error)
            return None
        else:
            if resource_sent:
                self.__logger.info("Requests", "Resource sent successfully.")
                return response
            else:
                self.__logger.error("Requests", "Failure sending resource.")
                return None

    def check_domain(self, resource_url:str) -> list[str, str]:
        self.__logger.debug("Requests", "Checking URL domain.")
        if "i.redd.it" in resource_url:
            return "REDDIT_IMAGE", resource_url
        elif "v.redd.it" in resource_url:
            return "REDDIT_VIDEO", resource_url
        elif "reddit.com/gallery" in resource_url:
            return "REDDIT_GALLERY", resource_url
        elif "imgur.com" in resource_url:
            return "IMGUR", resource_url.replace(".gifv",".mp4").replace(".gif",".mp4")
        if "redgifs.com" in resource_url:
            return "REDGIFS", resource_url
        elif "gfycat.com" in resource_url:
            return "GFYCAT", resource_url
        else:
            return "OTHERS", resource_url

    def page_text(self, page_url:str) -> str|None:
        '''Returns page contents as text.'''
        self.__logger.debug("Requests", "Loading page as text.")
        response = self.get(page_url)
        if response:
            return response.text
        else:
            return None
    
    def load_json(self, json_url:str) -> list|dict|None:
        '''JSON URL -> list/dict object.'''
        self.__logger.debug("Requests", "Loading json from URL.")
        response = self.get(json_url)
        if response and json_url.endswith(".json"):
            return json.load(io.BytesIO(response.content))
        else:
            return None

class File:
    def __init__(self, resource_url:str, logger:LoggingHelper, requester:RequestsHelper) -> None:
        '''Requires existing LoggingHelper and RequestsHelper objects.'''
        self.__logger = logger
        self.__requester = requester
        self.__resource_url = resource_url
        self.__response = self.__requester.get(self.__resource_url)

    @property
    def exists(self) -> bool:
        if self.__response is not None:
            return True
        else:
            return False
    
    @property
    def name(self) -> str:
        if self.exists:
            return os.path.basename(urllib.parse.unquote(urllib.parse.urlparse(self.__resource_url).path))
        else:
            return ""

    @property
    def bytes(self) -> bytes:
        if self.exists:
            return self.__response.content
        else:
            return None

    @property
    def __file(self) -> io.BytesIO:
        if self.exists:
            return io.BytesIO(self.bytes)
        else:
            return None
    
    @property
    def hash(self) -> str:
        if self.exists:
            return hashlib.sha512(self.__file.read()).hexdigest()
        else:
            return ""

    @property
    def __mime_type(self) -> str:
        if self.exists:
            return magic.from_buffer(self.__file.read(), mime=True)
        else:
            return ""

    @property
    def __size(self) -> int:
        if self.exists:
            return len(self.bytes)
        else:
            return 0

    @property
    def file_headers(self) -> (dict|None):
        if self.exists:
            if self.__size > FIFTY_MB:
                return None
            else:
                return {self.group:(self.name, self.bytes, self.__mime_type)}
        else:
            return None

    @property
    def group(self) -> str:
        photo_mimes = ["image/jpeg", "image/png", "image/webp"]
        anim_mimes = ["image/gif"]
        video_mimes = ["video/mp4", "video/x-m4v"]
        audio_mimes = ["audio/mpeg"]

        if self.__mime_type in photo_mimes and self.__is_sendable_photo:
            return "photo"
        elif self.__mime_type in anim_mimes:
            return "animation"
        elif self.__mime_type in video_mimes:
            return "video"
        elif self.__mime_type in audio_mimes:
            return "audio"
        else:
            return "document"

    @property
    def __is_sendable_photo(self) -> bool:
        try:
            image = PIL.Image.open(self.__file)
        except Exception as error:
            self.__logger.error("File", error)
        else:
            width = image.width
            height = image.height
            _WH_ratio = width / height
            _HW_ratio = height / width
            _dim_sum = height + width
            if _WH_ratio > 20 or _HW_ratio > 20 or _dim_sum > 10000 or self.__size > TEN_MB:
                return False
            else:
                return True

class DiscordHelper:
    def __init__(self, logger:LoggingHelper) -> None:
        '''Requires an existing LoggingHelper object.'''
        self.__logger = logger

    def __get_webhook(self, webhook_url:str) -> discord.Webhook:
        return discord.Webhook.from_url(webhook_url, adapter=discord.RequestsWebhookAdapter())

    def send(self, webhook_url:str, message:str) -> None:
        '''Sends message on webhook.'''
        self.__get_webhook(webhook_url=webhook_url).send(message)
        self.__logger.info("Discord", "Message posted.")

class FilebaseHelper:
    def __init__(self, logger:LoggingHelper) -> None:
        self.__logger = logger
        self.__filebase_client = boto3.client(
            service_name="s3",
            endpoint_url="https://s3.filebase.com",
            aws_access_key_id=FILEBASE_KEY,
            aws_secret_access_key=FILEBASE_SECRET
        )

    def upload_file(self, file) -> bool:
        '''Uploads file to bucket.'''
        try:
            self.__filebase_client.upload_file(file, FILEBASE_BUCKET_NAME, os.path.basename(file))
            self.__logger.info("Filebase", f"Uploaded {file} successfully.")
            return True
        except:
            self.__logger.info("Filebase", f"Failure uploading {file}.")
            return False

    def download_file(self, file) -> bool:
        '''Downloads file from bucket.'''
        try:
            self.__filebase_client.download_file(FILEBASE_BUCKET_NAME, os.path.basename(file), file)
            self.__logger.info("Filebase", f"Downloaded {file} successfully.")
            return True
        except:
            self.__logger.info("Filebase", f"Failure downloading {file}.")
            return False

class RedditHelper:
    def __init__(self, logger:LoggingHelper, requester:RequestsHelper) -> None:
        self.__logger = logger
        self.__requester = requester
        self.__reddit_client = praw.Reddit(
            user_agent=REDDIT_USER_AGENT,
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD
        )

    def get_post_details(self, post_id:str) -> tuple[str, str, str, str, str]:
        '''Returns a tuple of strings containing post details.'''
        json_data = self.__requester.load_json(f"https://www.reddit.com/comments/{post_id}.json")
        if not self.__check_solubility(json_data):
            self.__logger.info("Reddit", "Post cannot be solved.")
            return []
        parent_post_data = dict(json_data[0]["data"]["children"][0]["data"])
        post_title = self.__fix_json_text(parent_post_data["title"])
        post_author = f"u/{parent_post_data['author']}"
        post_subreddit = parent_post_data["subreddit_name_prefixed"]
        post_primary_link = self.__fix_json_text(parent_post_data["url_overridden_by_dest"])
        self.__logger.info("Reddit", "Post details obtained successfully.")
        return [post_id, post_title, post_author, post_subreddit, post_primary_link]

    def __check_solubility(self, json_data:dict) -> bool:
        self.__logger.debug("Reddit", "Checking if post is solvable.")
        if json_data is None:
            return False
        elif "error" in json_data:
            return False
        elif "url_overridden_by_dest" not in json_data[0]["data"]["children"][0]["data"]:
            return False
        elif not json_data[0]["data"]["children"][0]["data"]["url_overridden_by_dest"]:
            return False
        else:
            return True

    def __fix_json_text(self, escaped_text:str) -> str:
        return html.unescape(escaped_text.encode("utf-16", "surrogatepass").decode("utf-16"))

    def get_saved_posts(self, excluded=list[str]):
        '''Gets a list of currently saved posts excluding the passed list.'''
        self.__logger.debug("Reddit", "Checking Reddit for saved posts.")
        currently_saved_posts = []
        if not excluded:
            excluded = []
        for submission in self.__reddit_client.user.me().saved(limit=None):
            post_id = str(submission)
            if post_id not in excluded:
                currently_saved_posts.append(post_id)
        self.__logger.info("Reddit", f"Obtained {len(currently_saved_posts)} new posts from Reddit.")
        return currently_saved_posts

class TelegramHelper:
    def __init__(self, logger:LoggingHelper, requester:RequestsHelper) -> None:
        self.__logger = logger
        self.__requester = requester
        self.__image_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        self.__animation_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendAnimation"
        self.__video_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
        self.__audio_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendAudio"
        self.__document_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        self.__media_group_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"
        self.__message_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    def __get_base_message_from_post_details(self, post_details:list) -> list[str]:
        base_message = []
        if post_details[0] is not None:
            base_message.append(f"Post ID: {post_details[0]}")
        if post_details[1] is not None:
            base_message.append(f"{post_details[1]}")
        if post_details[2] is not None:
            base_message.append(f"by {post_details[2]}")
        if post_details[3] is not None:
            base_message.append(f"via {post_details[3]}")
        if post_details[4] is not None:
            base_message.append(f"Primary URL: {post_details[4]}")
        self.__logger.info("Telegram", "Obtained base caption.")
        return base_message

    def __send_single(self, file:File, caption:str) -> tuple[bool, str]:
        api_url = None
        params = None
        if file.file_headers:
            params = {'chat_id':TELEGRAM_CHAT_ID, 'caption':caption}
            if file.group == "photo":
                api_url = self.__image_api_url
                self.__logger.info("Telegram", "File sent as photo.")
            elif file.group == "animation":
                api_url = self.__animation_api_url
                self.__logger.info("Telegram", "File sent as animation.")
            elif file.group == "video":
                api_url = self.__video_api_url
                self.__logger.info("Telegram", "File sent as video.")
            elif file.group == "audio":
                api_url = self.__audio_api_url
                self.__logger.info("Telegram", "File sent as audio.")
            else:
                api_url = self.__document_api_url
                self.__logger.info("Telegram", "File sent as document.")
            post_response = self.__requester.post(api_url=api_url, files=file.file_headers, data=params)
            if post_response:
                return True, file.group
            else:
                return False, "failed"
        else:
            if file.exists:
                params = {'chat_id':TELEGRAM_CHAT_ID, 'text':caption}
                api_url = self.__message_api_url
                self.__logger.info("Telegram", "File exceeds 50 MB, sent as message.")
                post_response = self.__requester.post(api_url=api_url, data=params)
                if post_response:
                    return True, "message"
                else:
                    return False, "failed"
            else:
                self.__logger.info("Telegram", "File does not exist.")
                return False, "failed"

    def __send_group(self, file_list:list[File], caption_list:list[str]) -> tuple[bool, str]:
        media_types = [file.group for file in file_list]
        if "document" in media_types:
            media_types = ["document" for file in file_list]
        media_group = []
        file_bytes = {}
        for ix, file in enumerate(file_list):
            media_group.append({"type":media_types[ix], "media":f"attach://{file.name}", "caption":caption_list[ix]})
            file_bytes[file.name] = file.bytes
        media_group = json.dumps(media_group)
        params = {"chat_id":TELEGRAM_CHAT_ID, "media":media_group}
        api_url = self.__media_group_api_url
        self.__logger.info("Telegram", "Files sent as media group.")
        post_response = self.__requester.post(api_url=api_url, files=file_bytes, data=params)
        if post_response:
            return True, "group"
        else:
            return False, "failed"

    def __send_media(self, file_list:list[File], caption_list:list) -> tuple[bool, str]:
        if len(caption_list) > 1:
            return self.__send_group(file_list, caption_list)
        else:
            return self.__send_single(file_list[0], caption_list[0])

    def __fix_json_text(self, escaped_text:str) -> str:
        return html.unescape(escaped_text.encode("utf-16", "surrogatepass").decode("utf-16"))

    def __solve_reddit_image(self, post_details:list) -> tuple[bool, str]:
        self.__logger.info("Telegram", "Post falls under Reddit-hosted images.")
        base_message = self.__get_base_message_from_post_details(post_details)
        file = File(post_details[4], self.__logger, self.__requester)
        caption = "\n".join(base_message)
        return self.__send_media([file], [caption])

    def __solve_reddit_video(self, post_details:list) -> tuple[bool, str]:
        self.__logger.info("Telegram", "Post falls under Reddit-hosted videos.")
        base_message = self.__get_base_message_from_post_details(post_details)
        json_data = self.__requester.load_json(f"https://www.reddit.com/comments/{post_details[0]}.json")
        parent_post_data = dict(json_data[0]["data"]["children"][0]["data"])
        candidate_video_url = self.__fix_json_text(parent_post_data["media"]["reddit_video"]["fallback_url"])
        candidate_audio_url = candidate_video_url.split("DASH_")[0] + "DASH_audio.mp4"
        message_extension = []
        video_file = File(candidate_video_url, self.__logger, self.__requester)
        audio_file = File(candidate_audio_url, self.__logger, self.__requester)
        if video_file.exists:
            message_extension.append(f"Video URL: {candidate_video_url}")
        if audio_file.exists:
            message_extension.append(f"Audio URL: {candidate_audio_url}")
        base_message.extend(message_extension)
        caption = "\n".join(base_message)
        return self.__send_media([video_file], [caption])

    def __solve_reddit_gallery(self, post_details:list) -> tuple[bool, str]:
        self.__logger.info("Telegram", "Post falls under Reddit-hosted gallery.")
        base_message = self.__get_base_message_from_post_details(post_details)
        json_data = self.__requester.load_json(f"https://www.reddit.com/comments/{post_details[0]}.json")
        parent_post_data = dict(json_data[0]["data"]["children"][0]["data"])
        if parent_post_data["is_gallery"] is True and parent_post_data["media_metadata"] is not None:
            image_dict = parent_post_data["media_metadata"]
            file_list = []
            caption_list = []
            for key in image_dict:
                image_link = self.__fix_json_text(image_dict[key]["s"]["u"])
                file_list.append(File(image_link, self.__logger, self.__requester))
                caption_list.append("\n".join(base_message + [f"Image URL: {image_link}"]))
            if file_list:
                send_status = []
                div_groups = 1.0
                while (len(file_list)/div_groups) > 10.0:
                    div_groups += 1.0
                group_size = int(len(file_list)/div_groups)
                for div in range(int(div_groups)):
                     send_status.append(self.__send_media(file_list[(div*group_size):((div+1)*group_size)], caption_list[(div*group_size):((div+1)*group_size)])[0])
                if False not in send_status:
                    return True, "group"
            else:
                return False, "failed"
        else:
            return False, "failed"

    def __solve_imgur(self, post_details:list) -> tuple[bool, str]:
        self.__logger.info("Telegram", "Post falls under Imgur-hosted media.")
        base_message = self.__get_base_message_from_post_details(post_details)
        file = File(post_details[4], self.__logger, self.__requester)
        caption = "\n".join(base_message)
        return self.__send_media([file], [caption])

    def __solve_redgifs_gfycat(self, post_details:list) -> tuple[bool, str]:
        self.__logger.info("Telegram", "Post falls under Redgifs/Gfycat-hosted media.")
        base_message = self.__get_base_message_from_post_details(post_details)
        CONTENT_RE = re.compile(r'https:\/\/[a-z0-9]+.(redgifs|gfycat).com\/[a-zA-Z-]*.mp4')
        page_text = self.__requester.page_text(post_details[4])
        try:
            media_link = re.search(CONTENT_RE, page_text).group(0)
            file = File(media_link, self.__logger, self.__requester)
            caption = "\n".join(base_message + [f"Media URL: {media_link}"])
            return self.__send_media([file], [caption])
        except:
            return False, "failed"

    def __solve_others(self, post_details:list) -> tuple[bool, str]:
        self.__logger.info("Telegram", "Post doesn't fall under any known category.")
        base_message = self.__get_base_message_from_post_details(post_details)
        file = File(post_details[4], self.__logger, self.__requester)
        caption = "\n".join(base_message)
        return self.__send_media([file], [caption])

    def solve_post(self, post_details:list[str]) -> tuple[bool, str]:
        '''Solves post given post details.'''
        domain, post_details[4] = self.__requester.check_domain(post_details[4])
        if domain == "REDDIT_IMAGE":
            return self.__solve_reddit_image(post_details)
        elif domain == "REDDIT_VIDEO":
            return self.__solve_reddit_video(post_details)
        elif domain == "REDDIT_GALLERY":
            return self.__solve_reddit_gallery(post_details)
        elif domain == "IMGUR":
            return self.__solve_imgur(post_details)
        elif domain == "REDGIFS":
            return self.__solve_redgifs_gfycat(post_details)
        elif domain == "GFYCAT":
            return self.__solve_redgifs_gfycat(post_details)
        else:
            return self.__solve_others(post_details)