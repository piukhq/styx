# Styx

> Personification of Hatred

Downloads files from Mastercard and uploads then to Azure Blob Storage

```
Testing: sftp -i id_mastercard -P 16022 Z218502@mtf.files.mastercard.com
         | Contains: /0073185/test/download/TGX4
Production: sftp -i id_mastercard -P 16022 Z216458@files.mastercard.com
         | Contains: /0073185/production/download/TGX2
File Express: sftp -i id_mastercard -P 16022 Z218502@files.mastercard.com
         | Contains: /0073185/production/download/TS44
         |           /0073185/production/download/TGX2
```

## Running locally

Make sure you've got access to the Azure Key Vaults for Common and Infrastructure (spoiler: you don't unless you're DevOps)
