import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver

default_checkpoint_path = "agent_checkpoints.db"


def open_checkpointer():
    checkpoint_path = os.environ.get("CHECKPOINT_DB", default_checkpoint_path)
    connection = sqlite3.connect(checkpoint_path, check_same_thread=False)
    return SqliteSaver(connection)