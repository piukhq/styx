import json
import logging
from io import BytesIO, StringIO

import paramiko
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient

logging.getLogger("azure.identity").setLevel(logging.ERROR)

from settings import mode, config


def get_sftp_key() -> StringIO:
    vault_url = "https://bink-uksouth-prod-com.vault.azure.net/"
    vault_credential = DefaultAzureCredential()
    vault_client = SecretClient(vault_url=vault_url, credential=vault_credential)
    key = json.loads(vault_client.get_secret("mastercard-sftp").value)["key"]
    return StringIO(key)


def get_storage_key() -> str:
    vault_url = "https://bink-uksouth-prod-inf.vault.azure.net/"
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
    sftp_host = config[mode]["sftp_host"]
    sftp_port = config[mode]["sftp_port"]
    sftp_user = config[mode]["sftp_user"]
    sftp_dir = config[mode]["sftp_dir"]
    blob_container = config[mode]["blob_container"]
    blob_dir = config[mode]["blob_dir"]
    s = sftp_client(host=sftp_host, port=sftp_port, username=sftp_user)
    for i in s.listdir(sftp_dir):
        data = BytesIO()
        s.getfo(f"{sftp_dir}/{i}", data)
        data.seek(0)
        try:
            upload_blob(container=blob_container, filename=f"{blob_dir}/{i}", data=data)
        except Exception:
            with open(f"/tmp/{i}", "wb") as f:
                f.write(data)


if __name__ == "__main__":
    run()
