import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import ldap
import ldap.ldapobject
import ldap.modlist as modlist


class LDAPService:
    """Service for LDAP operations including backup and restore."""

    def __init__(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        base_dn: str,
        bind_dn: Optional[str] = None,
        bind_password: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.base_dn = base_dn
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        self.conn: Optional[ldap.ldapobject.LDAPObject] = None

    def connect(self):
        """Establish connection to LDAP server."""
        protocol = "ldaps" if self.use_ssl else "ldap"
        ldap_url = f"{protocol}://{self.host}:{self.port}"

        # Disable certificate verification for LDAPS with self-signed certificates
        # Must be done before initialize()
        if self.use_ssl:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            # Also ignore certificate hostname mismatches
            ldap.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

        self.conn = ldap.initialize(ldap_url)
        self.conn.set_option(ldap.OPT_REFERRALS, 0)

        if self.bind_dn and self.bind_password:
            self.conn.simple_bind_s(self.bind_dn, self.bind_password)
        else:
            self.conn.simple_bind_s()

    def disconnect(self):
        """Close LDAP connection."""
        if self.conn:
            self.conn.unbind_s()
            self.conn = None

    def search_all_entries(
        self, search_filter: str = "(objectClass=*)"
    ) -> List[Tuple[str, Dict]]:
        """Search all entries in LDAP directory."""
        if not self.conn:
            self.connect()

        try:
            result: List[Tuple[str, Dict]] = self.conn.search_s(  # type: ignore
                self.base_dn, ldap.SCOPE_SUBTREE, search_filter, None
            )
            return result
        except ldap.LDAPError as e:
            raise Exception(f"LDAP search failed: {str(e)}")

    def search_entries(
        self,
        search_filter: str = "(objectClass=*)",
        attributes: Optional[List[str]] = None,
        size_limit: int = 0,
    ) -> List[Tuple[str, Dict]]:
        """Search entries with optional filters and size limit."""
        if not self.conn:
            self.connect()

        try:
            result: List[Tuple[str, Dict]] = self.conn.search_ext_s(  # type: ignore
                self.base_dn,
                ldap.SCOPE_SUBTREE,
                search_filter,
                attributes,
                0,
                None,
                None,
                -1,
                size_limit,
            )
            return result
        except ldap.LDAPError as e:
            raise Exception(f"LDAP search failed: {str(e)}")

    def backup_to_ldif(
        self, output_path: str, search_filter: str = "(objectClass=*)"
    ) -> int:
        """Backup LDAP entries to LDIF format."""
        entries = self.search_all_entries(search_filter)

        with open(output_path, "w", encoding="utf-8") as f:
            for dn, attrs in entries:
                if dn is None:
                    continue

                # Write DN
                f.write(f"dn: {dn}\n")

                # Write attributes
                for attr, values in attrs.items():
                    for value in values:
                        if isinstance(value, bytes):
                            # Handle binary data
                            try:
                                value_str = value.decode("utf-8")
                            except UnicodeDecodeError:
                                # Base64 encode binary data
                                import base64

                                value_str = base64.b64encode(value).decode("utf-8")
                                f.write(f"{attr}:: {value_str}\n")
                                continue
                        else:
                            value_str = str(value)
                        f.write(f"{attr}: {value_str}\n")

                f.write("\n")

        return len(entries)

    def backup_certificates(self, output_path: str) -> int:
        """Backup certificate-related configuration entries to LDIF format."""
        if not self.conn:
            self.connect()

        # Common TLS-related attributes in OpenLDAP cn=config
        attributes = [
            "olcTLSCACertificateFile",
            "olcTLSCertificateFile",
            "olcTLSCertificateKeyFile",
            "olcTLSCACertificatePath",
            "olcTLSCipherSuite",
            "olcTLSVerifyClient",
            "olcTLSCRLFile",
            "olcTLSProtocolMin",
        ]

        try:
            entries = self.conn.search_ext_s(  # type: ignore
                "cn=config",
                ldap.SCOPE_SUBTREE,
                "(objectClass=*)",
                attributes,
                0,
                None,
                None,
                -1,
                0,
            )
        except ldap.LDAPError as e:
            raise Exception(f"LDAP certificate backup failed: {str(e)}")

        with open(output_path, "w", encoding="utf-8") as f:
            for dn, attrs in entries:
                if dn is None:
                    continue

                f.write(f"dn: {dn}\n")

                for attr, values in attrs.items():
                    for value in values:
                        if isinstance(value, bytes):
                            try:
                                value_str = value.decode("utf-8")
                            except UnicodeDecodeError:
                                import base64

                                value_str = base64.b64encode(value).decode("utf-8")
                                f.write(f"{attr}:: {value_str}\n")
                                continue
                        else:
                            value_str = str(value)
                        f.write(f"{attr}: {value_str}\n")

                f.write("\n")

        return len(entries)

    def backup_to_json(
        self, output_path: str, search_filter: str = "(objectClass=*)"
    ) -> int:
        """Backup LDAP entries to JSON format."""
        entries = self.search_all_entries(search_filter)

        json_data: List[Dict[str, Any]] = []
        for dn, attrs in entries:
            if dn is None:
                continue

            entry: Dict[str, Any] = {"dn": dn, "attributes": {}}

            for attr, values in attrs.items():
                entry["attributes"][attr] = []
                # values is bytes or list of bytes from LDAP
                values_list: List[Any] = (
                    values if isinstance(values, list) else [values]
                )
                for value in values_list:
                    if isinstance(value, bytes):
                        try:
                            entry["attributes"][attr].append(value.decode("utf-8"))
                        except UnicodeDecodeError:
                            import base64

                            entry["attributes"][attr].append(
                                {"binary": base64.b64encode(value).decode("utf-8")}
                            )
                    else:
                        entry["attributes"][attr].append(str(value))

            json_data.append(entry)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        return len(json_data)

    def restore_from_ldif(self, input_path: str) -> int:
        """Restore LDAP entries from LDIF format."""
        if not self.conn:
            self.connect()

        restored_count = 0

        with open(input_path, "r", encoding="utf-8") as f:
            current_dn: Optional[str] = None
            current_attrs: Dict[str, List[str]] = {}

            for line in f:
                line = line.rstrip("\n")

                if not line:
                    # End of entry
                    if current_dn and current_attrs:
                        try:
                            # Convert to LDAP modlist format
                            ldif_attrs: Dict[str, List[bytes]] = {}
                            for attr, values in current_attrs.items():
                                ldif_attrs[attr] = [
                                    v.encode("utf-8") if isinstance(v, str) else v
                                    for v in values
                                ]

                            # Add entry
                            self.conn.add_s(  # type: ignore[union-attr]
                                current_dn, modlist.addModlist(ldif_attrs)
                            )
                            restored_count += 1
                        except ldap.ALREADY_EXISTS:
                            # Entry exists, skip
                            pass
                        except ldap.LDAPError as e:
                            # Log error but continue
                            print(f"Error restoring {current_dn}: {str(e)}")

                    current_dn = None
                    current_attrs = {}
                    continue

                if line.startswith("dn: "):
                    current_dn = line[4:]
                elif ": " in line:
                    attr, value = line.split(": ", 1)
                    if attr not in current_attrs:
                        current_attrs[attr] = []
                    current_attrs[attr].append(value)

        return restored_count

    def get_modified_entries(
        self, since: datetime, search_filter: str = "(objectClass=*)"
    ) -> List[Tuple[str, Dict]]:
        """Get entries modified since a specific time (for incremental backup)."""
        # Construct time filter
        time_str = since.strftime("%Y%m%d%H%M%SZ")
        filter_str = f"(&{search_filter}(modifyTimestamp>={time_str}))"

        return self.search_all_entries(filter_str)

    def backup_schema(self, output_path: str) -> int:
        """Backup LDAP schema (cn=schema) to LDIF format."""
        schema_entries = self.search_all_entries(search_filter="(objectClass=*)")

        # Filter only schema-related entries
        schema_list = [
            (dn, attrs)
            for dn, attrs in schema_entries
            if dn and ("cn=schema" in dn.lower() or "objectclasses" in attrs)
        ]

        with open(output_path, "w", encoding="utf-8") as f:
            for dn, attrs in schema_list:
                f.write(f"dn: {dn}\n")
                for attr, values in attrs.items():
                    for value in values:
                        if isinstance(value, bytes):
                            try:
                                value_str = value.decode("utf-8")
                            except UnicodeDecodeError:
                                import base64

                                value_str = base64.b64encode(value).decode("utf-8")
                                f.write(f"{attr}:: {value_str}\n")
                                continue
                        else:
                            value_str = str(value)
                        f.write(f"{attr}: {value_str}\n")
                f.write("\n")

        return len(schema_list)

    def backup_config(self, output_path: str) -> int:
        """Backup LDAP configuration (cn=config) to LDIF format."""
        config_entries = self.search_all_entries(search_filter="(objectClass=*)")

        # Filter only config-related entries
        config_list = [
            (dn, attrs)
            for dn, attrs in config_entries
            if dn and "cn=config" in dn.lower()
        ]

        with open(output_path, "w", encoding="utf-8") as f:
            for dn, attrs in config_list:
                f.write(f"dn: {dn}\n")
                for attr, values in attrs.items():
                    for value in values:
                        if isinstance(value, bytes):
                            try:
                                value_str = value.decode("utf-8")
                            except UnicodeDecodeError:
                                import base64

                                value_str = base64.b64encode(value).decode("utf-8")
                                f.write(f"{attr}:: {value_str}\n")
                                continue
                        else:
                            value_str = str(value)
                        f.write(f"{attr}: {value_str}\n")
                f.write("\n")

        return len(config_list)

    def backup_rootdse(self, output_path: str) -> int:
        """Backup Root DSE (server capabilities) to LDIF format."""
        # Connect and get rootDSE by searching with empty DN
        if not self.conn:
            self.connect()

        try:
            # Get Root DSE
            result = self.conn.search_s("", ldap.SCOPE_BASE, "(objectClass=*)")

            with open(output_path, "w", encoding="utf-8") as f:
                for dn, attrs in result:
                    if dn is None:
                        continue
                    f.write(f"dn: {dn}\n")
                    for attr, values in attrs.items():
                        for value in values:
                            if isinstance(value, bytes):
                                try:
                                    value_str = value.decode("utf-8")
                                except UnicodeDecodeError:
                                    import base64

                                    value_str = base64.b64encode(value).decode("utf-8")
                                    f.write(f"{attr}:: {value_str}\n")
                                    continue
                            else:
                                value_str = str(value)
                            f.write(f"{attr}: {value_str}\n")
                    f.write("\n")

            return len(result)
        except ldap.LDAPError as e:
            raise Exception(f"Failed to backup Root DSE: {str(e)}")

    def backup_acls(self, output_path: str) -> int:
        """Backup access control lists (ACLs).

        Includes:
        - OpenLDAP: openLDAPaci attributes from all entries + olcAccess from cn=config
        - Active Directory: nTSecurityDescriptor attribute
        - 389-DS: ACL attributes on entries
        """
        if not self.conn:
            self.connect()

        acl_entries: List[Tuple[str, Dict]] = []
        acl_attributes = [
            "openLDAPaci",  # OpenLDAP entry-level ACLs
            "nTSecurityDescriptor",  # Active Directory
            "aci",  # Generic ACL attribute
        ]

        # Search for entries with ACL attributes
        acl_filter = "(|(openLDAPaci=*)(nTSecurityDescriptor=*)(aci=*))"
        try:
            acl_entries = self.search_entries(acl_filter, acl_attributes)
        except Exception:
            # If search fails, try to get all entries and filter
            all_entries = self.search_all_entries()
            acl_entries = [
                (dn, {k: v for k, v in attrs.items() if k.lower() in [a.lower() for a in acl_attributes]})  # noqa: E501
                for dn, attrs in all_entries
                if any(k.lower() in [a.lower() for a in acl_attributes] for k in attrs.keys())  # noqa: E501
            ]

        # Also try to backup OpenLDAP's cn=config ACLs (olcAccess rules)
        try:
            # Search for olcAccess entries in cn=config
            result = self.conn.search_s(
                "cn=config",
                ldap.SCOPE_SUBTREE,
                "(olcAccess=*)",
                None
            )
            acl_entries.extend(result)
        except Exception:
            pass  # cn=config may not be accessible or supported

        # Write ACLs to LDIF
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# LDAP Access Control Lists (ACLs)\n")
            f.write(f"# Backup created: {datetime.now().isoformat()}\n\n")

            for dn, attrs in acl_entries:
                if dn is None:
                    continue

                f.write(f"dn: {dn}\n")

                for attr, values in attrs.items():
                    for value in values:
                        if isinstance(value, bytes):
                            try:
                                value_str = value.decode("utf-8")
                            except UnicodeDecodeError:
                                import base64

                                value_str = base64.b64encode(value).decode("utf-8")
                                f.write(f"{attr}:: {value_str}\n")
                                continue
                        else:
                            value_str = str(value)
                        f.write(f"{attr}: {value_str}\n")

                f.write("\n")

        return len(acl_entries)

    def test_connection(self) -> bool:
        """Test LDAP connection."""
        try:
            self.connect()
            self.disconnect()
            return True
        except Exception as e:
            raise Exception(f"LDAP connection failed: {str(e)}")
        except Exception:
            return False
