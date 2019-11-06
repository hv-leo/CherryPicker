import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import Pmw
import logging


class GUI:
    def __init__(self, controller):
        self.controller = controller

        self.jira_url_label = None
        self.jira_url_input = None
        self.jira_user_label = None
        self.jira_user_input = None
        self.jira_password_label = None
        self.jira_password_input = None

        self.github_user_label = None
        self.github_user_input = None
        self.github_password_label = None
        self.github_password_input = None

        self.service_pack_label = None
        self.service_pack_input = None
        self.assignee_label = None
        self.assignee_input = None
        self.base_folder_label = None
        self.base_folder_input = None

        self.sps_listbox = None
        self.copy_button = None
        self.clear_button = None
        self.backports_listbox = None

        self.log_text = None
        self.text_handler = None
        self.logger = None

        self.window = tk.Tk()
        self.window.title("Tatooine Backporter")
        self.create_widgets()

    def create_widgets(self):
        # Create some room around all the internal frames
        self.window['padx'] = 5
        self.window['pady'] = 5

        # - - - - - - - - - - - - - - - - - - - - -
        # JIRA Credentials
        jira_label = ttk.Label(self.window, text="JIRA Credentials")
        jira_label.grid(row=1, column=1, sticky=tk.W, pady=3)

        jira_frame = ttk.Frame(self.window)
        jira_frame.grid(row=2, column=1, sticky=tk.E + tk.W + tk.N + tk.S, padx=30, pady=4)
        self.jira_url_label, self.jira_url_input, self.jira_user_label, self.jira_user_input, self.jira_password_label, self.jira_password_input = self.create_jira_credentials_fields(
            jira_frame)

        # - - - - - - - - - - - - - - - - - - - - -
        # GitHub Credentials
        github_label = ttk.Label(self.window, text="GitHub Credentials")
        github_label.grid(row=3, column=1, sticky=tk.W, pady=3)

        github_frame = ttk.Frame(self.window)
        github_frame.grid(row=4, column=1, sticky=tk.E + tk.W + tk.N + tk.S, padx=30, pady=4)
        self.github_user_label, self.github_user_input, self.github_password_label, self.github_password_input = self.create_github_fields(
            github_frame)

        # - - - - - - - - - - - - - - - - - - - - -
        # Backport Fields
        backport_label = ttk.Label(self.window, text="Backport Fields")
        backport_label.grid(row=5, column=1, sticky=tk.W, pady=3)

        backport_frame = ttk.Frame(self.window)
        backport_frame.grid(row=6, column=1, sticky=tk.E + tk.W + tk.N + tk.S, padx=30, pady=4)
        self.service_pack_label, self.service_pack_input, self.assignee_label, self.assignee_input, self.base_folder_label, self.base_folder_input = self.create_backport_fields(
            backport_frame)

        # - - - - - - - - - - - - - - - - - - - - -
        # Get SP Cases
        do_btn = ttk.Button(self.window, text="Get Cases!", command=self.controller.get_sp_cases)
        do_btn.grid(row=7, column=1, sticky=tk.E + tk.W + tk.N + tk.S)

        # - - - - - - - - - - - - - - - - - - - - -
        # SP Cases
        sp_cases_label = ttk.Label(self.window, text="SP Cases")
        sp_cases_label.grid(row=1, column=2, sticky=tk.W, pady=3)

        self.sp_cases_frame = ttk.Frame(self.window)
        self.sp_cases_frame.grid(row=2, column=2, sticky=tk.E + tk.W + tk.N + tk.S, rowspan=5)

        self.sps_listbox, self.copy_button, self.clear_button, self.backports_listbox = self.create_sp_cases_fields(self.sp_cases_frame)

        # - - - - - - - - - - - - - - - - - - - - -
        # Do It
        do_btn = ttk.Button(self.window, text="Do It!", command=self.controller.backport)
        do_btn.grid(row=7, column=2, sticky=tk.E + tk.W + tk.N + tk.S)

        # - - - - - - - - - - - - - - - - - - - - -
        # Logger Text Box
        self.log_text = ScrolledText(self.window, state='disabled')
        self.log_text.configure(font='TkFixedFont')
        self.log_text.grid(row=8, column=1, columnspan=3, sticky=tk.E + tk.W + tk.N + tk.S)
        self.config_logging()
        logging.info("Hello! Let's do some Backports!")

    def log_info(self, message):
        logging.info(message)
        self.log_text.update()

    def log_error(self, message):
        logging.error(message)
        self.log_text.update()

    def clear_logs(self):
        self.log_text = ScrolledText(self.window, state='disabled')
        self.log_text.configure(font='TkFixedFont')
        self.log_text.grid(row=8, column=1, columnspan=3, sticky=tk.E + tk.W + tk.N + tk.S)
        self.log_text.update()
        self.config_logging()

    def update_sp_list(self, sp_cases):
        for sp_case in sp_cases:
            self.sps_listbox.insert(tk.END, sp_case)

    def add_backports(self):
        currents_items = [sp for sp in self.backports_listbox.get() if sp]
        selected = self.sps_listbox.getcurselection()
        if selected:
            new_items = [sp for sp in selected if sp not in currents_items]
            for item in new_items:
                self.backports_listbox.insert(tk.END, item)

    def clear_backports(self):
        self.backports_listbox.clear()

    def create_jira_credentials_fields(self, parent):
        url_label = ttk.Label(parent, text="URL: ")
        url_label.grid(row=1, column=1)
        url_input = ttk.Entry(parent)
        url_input.grid(row=1, column=2)

        user_label = ttk.Label(parent, text="Username: ")
        user_label.grid(row=2, column=1)
        user_input = ttk.Entry(parent)
        user_input.grid(row=2, column=2)

        password_label = ttk.Label(parent, text="Password: ")
        password_label.grid(row=3, column=1)
        password_input = ttk.Entry(parent, show="*")
        password_input.grid(row=3, column=2)

        return url_label, url_input, user_label, user_input, password_label, password_input

    def create_github_fields(self, parent):
        user_label = ttk.Label(parent, text="Username: ")
        user_label.grid(row=1, column=1)
        user_input = ttk.Entry(parent)
        user_input.grid(row=1, column=2)

        password_label = ttk.Label(parent, text="Password: ")
        password_label.grid(row=2, column=1)
        password_input = ttk.Entry(parent, show="*")
        password_input.grid(row=2, column=2)

        return user_label, user_input, password_label, password_input

    def create_backport_fields(self, parent):
        service_pack_label = ttk.Label(parent, text="Service Pack: ")
        service_pack_label.grid(row=1, column=1)
        service_pack_input = ttk.Entry(parent)
        service_pack_input.grid(row=1, column=2)

        assignee_label = ttk.Label(parent, text="Assignee: ")
        assignee_label.grid(row=2, column=1)
        assignee_input = ttk.Entry(parent)
        assignee_input.grid(row=2, column=2)

        base_folder_label = ttk.Label(parent, text="Base Folder: ")
        base_folder_label.grid(row=3, column=1)
        base_folder_input = ttk.Entry(parent)
        base_folder_input.grid(row=3, column=2)

        return service_pack_label, service_pack_input, assignee_label, assignee_input, base_folder_label, base_folder_input

    def create_sp_cases_fields(self, parent):
        sps_listbox = Pmw.ScrolledListBox(parent,
                                          listbox_height=12,
                                          vscrollmode="static",
                                          listbox_selectmode=tk.EXTENDED,
                                          listbox_width=80)
        sps_listbox.grid(row=1, column=1, rowspan=12)

        copy_button = tk.Button(parent, text=">>>", command=self.add_backports)
        copy_button.grid(row=4, column=2)

        clear_button = tk.Button(parent, text="Clear", command=self.clear_backports)
        clear_button.grid(row=5, column=2)

        backports_listbox = Pmw.ScrolledListBox(parent,
                                                listbox_height=12,
                                                vscrollmode="static",
                                                listbox_selectmode=tk.EXTENDED,
                                                listbox_width=80)
        backports_listbox.grid(row=1, column=3, rowspan=12)

        return sps_listbox, copy_button, clear_button, backports_listbox

    def config_logging(self):
        # Create textLogger
        self.text_handler = TextHandler(self.log_text)

        # Logging configuration
        logging.basicConfig(filename='test.log',
                            level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        # Add the handler to logger
        self.logger = logging.getLogger()
        self.logger.addHandler(self.text_handler)


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

