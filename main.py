import json
import logging
import socket
from io import BytesIO, StringIO

import paramiko
import redis
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
from pythonjsonlogger import jsonlogger

logging.getLogger("azure.identity").setLevel(logging.ERROR)
logger = logging.getLogger()
logHandler = logging.StreamHandler()
logFmt = jsonlogger.JsonFormatter(timestamp=True)
logHandler.setFormatter(logFmt)
logger.addHandler(logHandler)


from settings import config, settings


def is_leader():
    if settings.leader_election_enabled:
        r = redis.Redis.from_url(settings.redis_url)
        lock_key = "styx"
        hostname = socket.gethostname()
        is_leader = False

        with r.pipeline() as pipe:
            try:
                pipe.watch(lock_key)
                leader_host = pipe.get(lock_key)
                if leader_host in (hostname.encode(), None):
                    pipe.multi()
                    pipe.setex(lock_key, 10, hostname)
                    pipe.execute()
                    is_leader = True
            except redis.WatchError:
                pass
    else:
        is_leader = True
    return is_leader


def get_sftp_key() -> StringIO:
    vault_url = settings.vault_url_sftp
    vault_credential = DefaultAzureCredential()
    vault_client = SecretClient(vault_url=vault_url, credential=vault_credential)
    key = json.loads(vault_client.get_secret("mastercard-sftp").value)["key"]
    return StringIO(key)


def get_storage_key() -> str:
    vault_url = settings.vault_url_storage
    vault_credential = DefaultAzureCredential()
    vault_client = SecretClient(vault_url=vault_url, credential=vault_credential)
    return json.loads(vault_client.get_secret("infra-storage-common").value)["connection_string"]


def sftp_client(host: str, port: int, username: str) -> paramiko.SFTPClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.RSAKey.from_private_key(get_sftp_key())
    ssh.connect(host, port=port, username=username, pkey=key)
    return ssh.open_sftp()


def upload_blob(container: str, filename: str, data: BytesIO) -> None:
    client = BlobServiceClient.from_connection_string(get_storage_key())
    blob = client.get_blob_client(container=container, blob=filename)
    blob.upload_blob(data)


def run() -> None:
    if is_leader():
        mode = settings.mode
        sftp_host = config[mode]["sftp_host"]
        sftp_port = config[mode]["sftp_port"]
        sftp_user = config[mode]["sftp_user"]
        sftp_dir = config[mode]["sftp_dir"]
        blob_container = config[mode]["blob_container"]
        blob_dir = config[mode]["blob_dir"]
        logging.warning(
            msg="Connecting to SFTP",
            extra={"host": sftp_host, "port": sftp_port, "user": sftp_user, "directory": sftp_dir},
        )
        s = sftp_client(host=sftp_host, port=sftp_port, username=sftp_user)
        for i in s.listdir(sftp_dir):
            data = BytesIO()
            s.getfo(f"{sftp_dir}/{i}", data)
            data.seek(0)
            try:
                logging.warning(msg="Uploading Blob", extra={"filename": i, "container": blob_container})
                upload_blob(container=blob_container, filename=f"{blob_dir}/{i}", data=data)
            except Exception:
                with open(f"/tmp/{i}", "wb") as f:
                    f.write(data)


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(run, trigger=CronTrigger.from_crontab("0 * * * *"))
    scheduler.start()
