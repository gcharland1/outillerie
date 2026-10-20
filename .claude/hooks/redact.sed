# Masque les secrets connus dans les transcripts exportés (sed -E).
s#(://[^:/@[:space:]]+:)[^@[:space:]]+@#\1***@#g
s#((SECRET|PASSWORD|PASSWD|TOKEN|API_KEY)[A-Z_]*[[:space:]]*[=:][[:space:]]*["']?)[^[:space:]"'`]+#\1***#Ig
