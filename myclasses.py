from datetime import datetime
from dataclasses import dataclass
from typing import Optional


class UserData:
    def __init__(self):
        self.name: Optional[str] = None
        self.goal: Optional[str] = None
        self.attempts: Optional[str] = None
        self.stopping: Optional[str] = None
        self.smart_s: Optional[str] = None
        self.smart_m: Optional[str] = None
        self.smart_a: Optional[str] = None
        self.smart_r: Optional[str] = None
        self.smart_t: Optional[str] = None

    def __repr__(self):
        return "UserData:\n" + "\n".join(["%s: %s" % item for item in vars(self).items()])


class Filename:
    def __init__(self, username, chat_id, bot_config_key):
        log_path: str = username.replace("@", "") + "-" + chat_id
        self.history_log: str = f"logs/{bot_config_key}/{log_path}.log"
        self.prompt_log: str = f"logs/{bot_config_key}/{log_path}_prompts.log"
        self.voice_path: str = f"audio/{bot_config_key}/{log_path}_" + datetime.now().strftime('%Y%m%d%H%M%S') + ".ogg"


class UserActive:
    def __init__(self, username, chat_id, coachVoice=False):
        self.username: str = username.strip('@')
        self.isActive: bool = False
        self.chat_id: str = chat_id
        self.conv_id: str = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.coachVoice: bool = coachVoice
        self.prompt_text: Optional[str] = None
        self.user_data: UserData = UserData()
        self.pretreatment_step: Optional[int, float] = 0

    def __eq__(self, other):
        if isinstance(other, UserActive):
            return self.username == other.username
        elif isinstance(other, str):
            return self.username == other.strip("@")
        return False

    def set_active_status(self, t: bool):
        self.isActive = t
        if t:
            self.pretreatment_step = 0


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


if __name__ == '__main__':
    u = UserActive(
        'test', '11314'
    )
    u.user_data.name = 'Lisa'
    setattr(u.user_data, 'goal', 'to find a job')
    print(u.user_data)
