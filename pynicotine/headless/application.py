# COPYRIGHT (C) 2021-2022 Nicotine+ Contributors
#
# GNU GENERAL PUBLIC LICENSE
#    Version 3, 29 June 2007
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import threading
import sys
import time
import os
import pandas as pd
from pynicotine.cli import cli
from pynicotine.config import config
from pynicotine.core import core
from pynicotine.events import events
from pynicotine.logfacility import log
from pynicotine.search import Searches
import socket 
import json
import requests
from dotenv import load_dotenv


load_dotenv()
class Application:

    def __init__(self):

        sys.excepthook = self.exception_hook

        for log_level in ("download", "upload"):
            log.add_log_level(log_level, is_permanent=False)

        for event_name, callback in (
            ("confirm-quit", self.on_confirm_quit),
            ("shares-unavailable", self.on_shares_unavailable)
        ):
            events.connect(event_name, callback)

    def auto_search(self, search_term,  core):
        for f in os.listdir("pynicotine/search_results"):
            if f != "__init__.py":
                os.remove(f"pynicotine/search_results/{f}")
        searched=False
        if core.user_status==2:
            if not searched:
                core.search.do_search(search_term, "global")
            
    def status_message(self, status,core):
        url = f"http://{os.environ['API_HOST']}:{os.environ['API_PORT']}/status_message"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        token = core.search.token
        params={"search_term":core.search.searches[token].term, "status":status}
        response = requests.post(url, params=params, headers=headers)


    def auto_download(self, tracks_cnt, core):
        token = core.search.token
        try:
            df = pd.read_csv(
                f"pynicotine/search_results/{token}.csv",
                names=["user", "freeulslots", "ulspeed", "inqueue"],sep="|"
            )
        except:
            print("No search results")
            self.status_message("not_found",core)
            return False
        df = df[df["freeulslots"] == True]
        df = df.sort_values(by=["ulspeed", "inqueue"], ascending=False)
        find = False
        for _, item in df["user"].iteritems():
            try:
                files = pd.read_csv(
                    f"pynicotine/search_results/{item}_{token}.csv",
                    names=["index", "file", "size", "idk", "bitrate", "duration"],
                    sep="|"
                )
                if files.shape[0] >=tracks_cnt:
                    for _, row in files.iterrows():
                        try:
                            if ".mp3" in row["file"] and row["bitrate"] >= 320:
                                print(item)
                                find = True
                                break
                        except:
                            pass

                    if find:
                        break
            except:
                pass
        if find:
            print(f"Downloading from user {item}")
            for _, row in files.iterrows():
                core.transfers.get_file(item,row["file"],path="",transfer=None, size=row["size"], bitrate=str(row["bitrate"]), length=str(row["duration"]), bypass_filter=False, ui_callback=True)
            self.status_message("success",core)         
            
        else:
            print("Not found")   
            self.status_message("criterias_not_met",core)         
        for f in os.listdir("pynicotine/search_results"):
            if f != "__init__.py":
                os.remove(f"pynicotine/search_results/{f}")


    def run(self):
        core.start()
        core.connect()
        HOST = ''   # Symbolic name, meaning all available interfaces
        PORT = 5000 # Arbitrary non-privileged port

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.setblocking(False)
        s.listen(1)

        print('Waiting for connections...')
        
        conn = None
        
        # Main loop, process events from threads 20 times per second
        while not core.shutdown:
            # Check if there is an existing connection
            if conn:
                try:
                    data = conn.recv(1024)
                    if data:
                        print(data)
                        json_message = data.decode("utf-8")
                        message = json.loads(json_message)
                        if message["function"] == "auto_search":
                            self.auto_search(message["search_term"], core)
                        elif message["function"] == "auto_download":
                            self.auto_download(message["tracks_cnt"], core)
                    else:
                        # The connection has been closed, reset conn variable
                        conn.close()
                        conn = None
                except BlockingIOError:
                    pass
            
            # Check for new connections
            try:
                conn, addr = s.accept()
                conn.setblocking(False)
                print('Connected by', addr)
            except BlockingIOError:
                pass

            events.process_thread_events()
            time.sleep(0.05)

        config.write_configuration()
        return 0
    
    def exception_hook(self, _exc_type, exc_value, _exc_traceback):
        core.quit()
        raise exc_value

    def on_confirm_quit_response(self, user_input):
        if user_input.lower().startswith("y"):
            core.quit()

    def on_confirm_quit(self, _remember):
        cli.prompt("Do you really want to quit Nicotine+ (Y/N)?: ", callback=self.on_confirm_quit_response)

    def on_shares_unavailable_response(self, user_input):

        if user_input == "test":
            core.shares.rescan_shares()
            return

        log.add("no")

    def on_shares_unavailable(self, _shares):
        cli.prompt("Enter some text: ", callback=self.on_shares_unavailable_response)
