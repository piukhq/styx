from pydantic import BaseSettings


class Settings(BaseSettings):
    mode: str = "TS44"
    vault_url_storage: str = "https://bink-uksouth-prod-inf.vault.azure.net/"
    vault_url_sftp: str = "https://bink-uksouth-prod-com.vault.azure.net/"
    leader_election_enabled: bool = True
    redis_url: str


settings = Settings()

config = {
    "TGX4": {
        "sftp_host": "mtf.files.mastercard.com",
        "sftp_port": 16022,
        "sftp_user": "Z218502",
        "sftp_dir": "/0073185/test/download/TGX4",
        "blob_container": "harmonia-imports",
        "blob_dir": "test/mastercard-settlement",
    },
    "TGX2": {
        "sftp_host": "files.mastercard.com",
        "sftp_port": 16022,
        "sftp_user": "Z216458",
        "sftp_dir": "/0073185/production/download/TGX2",
        "blob_container": "harmonia-imports",
        "blob_dir": "test/mastercard-settlement",
    },
    "TS44": {
        "sftp_host": "files.mastercard.com",
        "sftp_port": 16022,
        "sftp_user": "Z218502",
        "sftp_dir": "/0073185/production/download/TS44",
        "blob_container": "harmonia-imports",
        "blob_dir": "payment/mastercard",
    },
    "TEST": {
        "sftp_host": "sftp.gb.bink.com",
        "sftp_port": 22,
        "sftp_user": "binktest_dev",
        "sftp_dir": "/archive",
        "blob_container": "harmonia-imports",
        "blob_dir": "styx-test",
    },
}
