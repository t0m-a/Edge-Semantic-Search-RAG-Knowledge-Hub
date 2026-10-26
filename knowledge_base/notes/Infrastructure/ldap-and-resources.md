# LDAP Administration & Useful Resources

> [← Back to Main Index](README.md)

## Table of Contents

- [LDAP & OpenLDAP Management](#ldap--openldap-management)
  - [`ldapsearch` Queries](#ldapsearch-queries)
  - [Filter & Base DN Examples](#filter--base-dn-examples)
- [Useful System, Networking & Security Resources](#useful-system-networking--security-resources)

---

## LDAP & OpenLDAP Management

### `ldapsearch` Queries

Query an LDAP directory server by Organizational Unit (`ou`) or Organization (`o`) and Common Name (`cn`):

```bash
ldapsearch -D "cn=LDAP DIRECTORY SERVER" -w PASSWD -v -p PORT -b "ou=O_UNIT" "cn=CANON_NAME"
ldapsearch -D "cn=LDAP DIRECTORY SERVER" -w PASSWD -v -p PORT -b "o=ORGANISATION" "cn=CANON_NAME CANONICAL NAMES"
```

### Filter & Base DN Examples

- **What we search (Search Filter):**
  ```text
  (cn=CANON_NAME*)
  # e.g.: (cn=CODE APPNAME SHORTCODE) CANON_NAME CANONICAL NAMES
  ```
- **Where we search (Search Base DN):**
  ```text
  o=ORGANISATION,ou=ORGANISATIONAL_UNIT
  ```

---

## Useful System, Networking & Security Resources

- [Free Detection Tools — InfoSec Institute](http://resources.infosecinstitute.com/free-detection-tools/)
- [GNU Screen Documentation (ubuntu-fr.org)](https://doc.ubuntu-fr.org/screen)
- [Screen Command Examples to Manage Linux Terminals (Tecmint)](https://www.tecmint.com/screen-command-examples-to-manage-linux-terminals/)
- [How to Prompt for Yes/No/Cancel Input in a Linux Shell Script (StackOverflow)](https://stackoverflow.com/questions/226703/how-do-i-prompt-for-yes-no-cancel-input-in-a-linux-shell-script)
- [Bash History: Display Date & Time for Each Command (nixCraft)](https://www.cyberciti.biz/faq/unix-linux-bash-history-display-date-time/)
- [Liste des codes HTTP (Wikipedia FR)](https://fr.wikipedia.org/wiki/Liste_des_codes_HTTP)
- [Wring — Extract Data from Web Pages on the Command Line (Korben)](https://korben.info/wring-extraire-donnees-presentes-pages-web-ligne-de-commande.html)
- [googler — Search Google from the Linux Terminal (GitHub)](https://github.com/jarun/googler#installing-from-this-repository)
- [Nginx Tips Collection (Twitter Moment)](https://twitter.com/i/moments/1004697240013889536)
