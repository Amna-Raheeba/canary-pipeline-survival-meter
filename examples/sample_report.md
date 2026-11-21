Canary survival audit -- doc-7

canary (format / form)       planted    ingest     summarise  chunk      redact     translate  mail     
api_key-7 (api_key / verbatim) SURVIVES   SURVIVES   SURVIVES   SURVIVES   dead       dead       dead     
email-7 (email / verbatim)   SURVIVES   SURVIVES   SURVIVES   SURVIVES   dead       dead       dead     
account_id-7 (account_id / spaced) SURVIVES   SURVIVES   SURVIVES   SURVIVES   SURVIVES   dead       dead     
free_text-7 (free_text / verbatim) SURVIVES   SURVIVES   SURVIVES   SURVIVES   SURVIVES   SURVIVES   SURVIVES 

Redactor log: replaced 2 match(es) {'api_key': 1, 'email': 1, 'account_id': 0}; claims coverage of api_key, email, account_id.
Leaked into the mailed output: free_text-7
Leaked but invisible to the audit detector: none
Leaked but invisible to verbatim grep: free_text-7
