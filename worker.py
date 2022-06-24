from helpers import *
import itertools

class Worker:
    def __init__(self, logger:LoggingHelper, requester:RequestsHelper) -> None:
        self.__logger = logger
        self.__requester = requester
        self.__reddit = RedditHelper(self.__logger, self.__requester)
        self.__telegram = TelegramHelper(self.__logger, self.__requester)
        self.__discord = DiscordHelper(self.__logger)

        self.__pending_posts = None
        self.__processed_posts = None
        self.__failed_posts = None
        self.__init_local_files()
        self.__refresh_pending_posts()
        self.__retry_failed_posts()

    def __init_local_files(self):
        local_files = [
            "pending_posts.txt",
            "processed_posts.txt",
            "failed_posts.txt"
        ]
        for file in local_files:
            if os.path.isfile(file) is False:
                with open(file, "w", encoding="utf-16") as _:
                    self.__logger.info("Worker", f"Created new {file} successfully.")
            else:
                self.__logger.info("Worker", f"{file} already exists locally, using local copy.")
        
        with open("pending_posts.txt", "r", encoding="utf-16") as input_file:
            self.__pending_posts = [item.strip() for item in input_file.readlines()]
        with open("processed_posts.txt", "r", encoding="utf-16") as input_file:
            self.__processed_posts = [item.strip() for item in input_file.readlines()]
        with open("failed_posts.txt", "r", encoding="utf-16") as input_file:
            self.__failed_posts = [item.strip() for item in input_file.readlines()]

    def __refresh_pending_posts(self):
        excluded = self.__pending_posts + self.__processed_posts + self.__failed_posts
        new_posts = self.__reddit.get_saved_posts(excluded=excluded)
        self.__pending_posts = [*new_posts, *self.__pending_posts]
        self.__pending_posts = sorted(self.__pending_posts, reverse=True)
        if not self.__pending_posts:
            self.__logger.info("Worker", f"No posts to solve, sleeping for {IDLE_SLEEP/60} minutes.")
            time.sleep(IDLE_SLEEP)
        elif new_posts:
            self.__list_to_file(self.__pending_posts, "pending_posts.txt")
            self.__logger.info("Worker", "Pending posts updated.")
        else:
            self.__logger.info("Worker", "No new posts to solve, continuing with currently pending posts.")

    def __retry_failed_posts(self):
        self.__logger.info("Worker", "Searching for old failed posts to retry.")
        if self.__failed_posts:
            self.__logger.info("Worker", "Failed posts found, queued for retyring.")
            self.__pending_posts.extend(self.__failed_posts)
            self.__pending_posts = list(set(self.__pending_posts))
            self.__pending_posts = sorted(self.__pending_posts, reverse=True)
        else:
            self.__logger.info("Wokrer", "No failed posts found, continuing as usual.")

    def load_refresher(self):
        self.__logger.info("Worker", "Periodic check for new posts if any.")
        self.__refresh_pending_posts()

    def __list_to_file(self, list:list, file:str):
        with open(file, "w", encoding="utf-16") as output_file:
            output_file.write("\n".join(list))

    def __generator(self):
        while True:
            if len(self.__pending_posts) != 0:
                self.__logger.info("Worker", f"{len(self.__pending_posts)} posts remaining before refresh.")
                unsaved_post = self.__pending_posts.pop()
                self.__logger.info("Worker", f"Popped post with id: {unsaved_post} from pending posts.")
                self.__list_to_file(self.__pending_posts, "pending_posts.txt")
                yield unsaved_post
            else:
                self.__refresh_pending_posts()
    
    def get_unsolved_post(self):
        return self.__generator().__next__()

    def solve_post(self, post_id:str):
        post_details = self.__reddit.get_post_details(post_id)
        self.__logger.info("Worker", f"Started solving post with id: {post_id}")
        if post_details:
            status, group = self.__telegram.solve_post(post_details)
            if status:
                self.__logger.info("Worker", f"Success solving post with id: {post_id}")
                if group == "photo":
                    self.__discord.send(PHOTOS_WEBHOOK, post_id)
                elif group == "animation":
                    self.__discord.send(ANIMATIONS_WEBHOOK, post_id)
                elif group == "video":
                    self.__discord.send(VIDEOS_WEBHOOK, post_id)
                elif group == "audio":
                    self.__discord.send(AUDIO_WEBHOOK, post_id)
                elif group == "document":
                    self.__discord.send(DOCUMENTS_WEBHOOK, post_id)
                elif group == "message":
                    self.__discord.send(MESSAGES_WEBHOOK, post_id)
                elif group == "group":
                    self.__discord.send(GROUP_WEBHOOK, post_id)
                self.__logger.info("Worker", f"Finished solving post with id: {post_id}")
                self.__processed_posts.append(post_id)
                self.__list_to_file(self.__processed_posts, "processed_posts.txt")
            else:
                self.__logger.error("Worker", f"Failure solving post with id: {post_id}")
                self.__discord.send(FAILED_WEBHOOK, post_id)
                self.__failed_posts.append(post_id)
                self.__list_to_file(self.__failed_posts, "failed_posts.txt")
        else:
            self.__logger.error("Worker", f"Failure solving post with id: {post_id}")
            self.__discord.send(FAILED_WEBHOOK, post_id)
            self.__failed_posts.append(post_id)
            self.__list_to_file(self.__failed_posts, "failed_posts.txt")

if __name__=="__main__":
    logger = LoggingHelper()
    requester = RequestsHelper(logger)
    workerInstance = Worker(logger, requester)

    if REFRESH_AFTER_POSTS < 5:
        REFRESH_AFTER_POSTS = 5
        logger.info("Worker", "REFRESH_AFTER_POSTS < 5, setting to 5 to check after every 5 posts.")

    for mod in itertools.cycle(range(REFRESH_AFTER_POSTS-1, -1, -1)):
        unsolved_post = workerInstance.get_unsolved_post()
        workerInstance.solve_post(unsolved_post)
        time.sleep(SLEEP_BETWEEN_POSTS)
        if mod == 0:
            workerInstance.load_refresher()
            logger.info("Worker", f"Sleeping for {3*SLEEP_BETWEEN_POSTS} seconds to allow manual stopping without errors.")
            time.sleep(3*SLEEP_BETWEEN_POSTS)