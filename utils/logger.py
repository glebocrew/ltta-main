from datetime import datetime
from os import path as os_path


class Logger:
    def __init__(self, path: str, module_name: str = "logs.txt"):
        """
        Logger is a class for logs.
        Logs statuses:
        [DEBUG, INFO, LOG, ERROR, FATAL]

        :param path: an existing/new file where you want your logs to be written
        """
        self.module_name = module_name

        if os_path.exists(path):
            self.log_file = open(path, encoding="utf-8", mode="a", buffering=1)
        else:
            self.log_file = open(file=path, encoding="utf-8", mode="a")
            self.log_file.write(
                f"{datetime.now()} INFO [{self.module_name}] Created file {path} where the logs will be displayed.\n"
            )

    def log(self, status: str, message: str):
        """
        Writes some debug information to your path file
        :param status: [DEBUG, INFO, LOG, ERROR, FATAL]
        :param message: your comment
        """
        self.log_file.write(
            f"{datetime.now()} {status.upper()} [{self.module_name}] {message}\n"
        )
        self.log_file.flush()

    def stop(self):
        self.log_file.close()
