from datetime import datetime


class Filename:
    def __init__(self, username, chat_id, bot_config_key):
        log_path: str = username.replace("@", "") + "-" + chat_id
        self.history_log: str = f"logs/{bot_config_key}/{log_path}.log"
        self.prompt_log: str = f"logs/{bot_config_key}/{log_path}_prompts.log"
        self.voice_path: str = f"audio/{bot_config_key}/{log_path}_" + datetime.now().strftime('%Y%m%d%H%M%S') + ".ogg"


class UserActive:
    def __init__(self, username, chat_id):
        self.username: str = username.strip('@')
        self.isActive: bool = False
        self.chat_id: str = chat_id
        self.conv_id: str = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.coachVoice: bool = True
        self.prompt_text: str = None

    def __eq__(self, other):
        if isinstance(other, UserActive):
            return self.username == other.username
        elif isinstance(other, str):
            return self.username == other.strip("@")
        return False

    def set_active_status(self, t: bool):
        self.isActive = t


class Conversation:
    def __init__(self):
        self.users = dict()

    def new_user(self, user: UserActive):
        self.users[user.username] = user

    def _change_status_user(
        self,
        username: str,
        status: bool
    ):
        for u in self.users:
            if u == username:
                self.users[u].set_active_status(status)
                break

    def activate_user(self, username):
        self._change_status_user(username, True)

    def deactivate_user(self, username):
        self._change_status_user(username, False)
