import json
import logging
from io import StringIO

import paramiko
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logging.getLogger("azure.identity").setLevel(logging.ERROR)


def get_sftp_key() -> str:
    vault_url = "https://bink-uksouth-prod-com.vault.azure.net/"
    vault_credential = DefaultAzureCredential()
    vault_client = SecretClient(vault_url=vault_url, credential=vault_credential)
    key = json.loads(vault_client.get_secret("mastercard-sftp").value)["key"]
    return StringIO(key)


def sftp_client(host: str, port: int, username: str) -> paramiko.SFTPClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.RSAKey.from_private_key(get_sftp_key())
    ssh.connect(host, port=port, username=username, pkey=key)
    return ssh.open_sftp()


# s = sftp_client(host="mtf.files.mastercard.com", port=16022, username="Z218502")
# s = sftp_client(host="files.mastercard.com", port=16022, username="Z216458")
# s = sftp_client(host="files.mastercard.com", port=16022, username="Z218502")
