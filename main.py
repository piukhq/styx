import json
from io import BytesIO, StringIO

import paramiko
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
from loguru import logger

from settings import config, settings


def get_sftp_key() -> StringIO:
    vault_url = settings.vault_url
    vault_credential = DefaultAzureCredential()
    vault_client = SecretClient(vault_url=vault_url, credential=vault_credential)
    key = json.loads(vault_client.get_secret("mastercard-sftp").value)["key"]
    return StringIO(key)


def sftp_client(host: str, port: int, username: str) -> paramiko.SFTPClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.RSAKey.from_private_key(get_sftp_key())
    ssh.connect(
        host, port=port, username=username, pkey=key, disabled_algorithms={"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]}
    )
    return ssh.open_sftp()


def upload_blob(container: str, filename: str, data: BytesIO) -> None:
    client = BlobServiceClient.from_connection_string(settings.storage_connection_string)
    blob = client.get_blob_client(container=container, blob=filename)
    blob.upload_blob(data)


def run() -> None:
    mode = settings.mode
    sftp_host = config[mode]["sftp_host"]
    sftp_port = config[mode]["sftp_port"]
    sftp_user = config[mode]["sftp_user"]
    sftp_dir = config[mode]["sftp_dir"]
    blob_container = config[mode]["blob_container"]
    blob_dir = config[mode]["blob_dir"]
    logger.warning(
        f"Connecting to SFTP 'host': {sftp_host}, 'port': {sftp_port}, 'user': {sftp_user}, 'dir': {sftp_dir}"
    )
    s = sftp_client(host=sftp_host, port=sftp_port, username=sftp_user)
    for i in s.listdir(sftp_dir):
        data = BytesIO()
        s.getfo(f"{sftp_dir}/{i}", data)
        data.seek(0)
        logger.warning(f"Uploading Blob 'file_name': {i}, 'container': {blob_container}")
        upload_blob(container=blob_container, filename=f"{blob_dir}/{i}", data=data)


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(run, trigger=CronTrigger.from_crontab("0 * * * *"))
    scheduler.start()
