import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

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

    # Attributes that commonly cause referential-integrity / constraint
    # violations when the referenced entry has not been created yet.
    _DEFERRABLE_ATTRS = frozenset({
        "manager",
        "secretary",
        "member",
        "uniqueMember",
        "memberOf",
        "owner",
        "seeAlso",
        "ssoRoles",
    })

    def _create_missing_entry(self, dn: str, logger) -> bool:
        """
        Create a minimal entry for a missing DN.
        Determines objectClass based on DN structure.
        For ssoRoles targets, use groupOfNames; for ou=roles and users, adjust accordingly.
        """
        try:
            # Parse DN to determine objectClass
            parts = dn.split(",")
            first_rdn = parts[0].lower() if parts else ""
            
            # Check if this is an ssoRoles target (usually under ou=roles)
            # ssoRoles expects groupOfNames objects
            is_ssoroles_context = any("ou=roles" in p.lower() for p in parts)
            
            # Determine appropriate objectClass
            if first_rdn.startswith("cn="):
                # It's a group or organizational unit - always use groupOfNames for consistency
                object_class = "groupOfNames"
            elif first_rdn.startswith("ou="):
                # It's an organizational unit
                # If it's part of a roles structure, it might need to support groupOfNames members
                if is_ssoroles_context and "ou=roles" in dn.lower():
                    # This is an intermediate OU in a roles structure
                    # Create as groupOfNames to allow member attributes
                    object_class = "groupOfNames"
                else:
                    object_class = "organizationalUnit"
            elif first_rdn.startswith("uid="):
                # It's a user
                object_class = "inetOrgPerson"
            else:
                # Default to groupOfNames for safety (works for most references)
                object_class = "groupOfNames"
            
            # Build minimal entry attributes
            entry_attrs: Dict[str, List[str]] = {
                "objectClass": [object_class]
            }
            
            # Add required attributes based on type
            if object_class == "groupOfNames":
                # Groups need at least one member - use root DN as placeholder
                entry_attrs["member"] = [self.base_dn]
            elif object_class == "organizationalUnit":
                # OU doesn't need additional attributes
                pass
            elif object_class == "inetOrgPerson":
                # Users need sn and cn at minimum
                rdn_value = first_rdn.split("=", 1)[1] if "=" in first_rdn else "unknown"
                entry_attrs["sn"] = [rdn_value]
                entry_attrs["cn"] = [rdn_value]
            
            # Convert to bytes and create entry
            bytes_attrs = self._to_bytes_dict(entry_attrs)
            self.conn.add_s(dn, modlist.addModlist(bytes_attrs))  # type: ignore[union-attr]
            logger.info("Created missing entry: %s (objectClass: %s)", dn, object_class)
            return True
            
        except Exception as e:
            logger.warning("Could not create missing entry %s: %s", dn, e)
            return False

    @staticmethod
    def _topological_sort(
        entries: List[Tuple[str, Dict[str, List[str]]]]
    ) -> List[Tuple[str, Dict[str, List[str]]]]:
        """
        Sort entries by dependencies using topological sort.
        
        Entries with manager attributes are processed after their managers.
        This ensures referential integrity constraints are satisfied.
        """
        # Build a map of DN -> entry for quick lookup
        dn_to_entry: Dict[str, Tuple[str, Dict[str, List[str]]]] = {
            dn: (dn, attrs) for dn, attrs in entries
        }
        all_dns: Set[str] = set(dn_to_entry.keys())
        
        # Build dependency graph: dn -> list of dns it depends on
        dependencies: Dict[str, Set[str]] = {}
        for dn, attrs in entries:
            dependencies[dn] = set()
            # Check for manager attribute
            if "manager" in attrs:
                for manager_dn in attrs["manager"]:
                    if manager_dn in all_dns:
                        dependencies[dn].add(manager_dn)
            # Check for ssoRoles attribute
            if "ssoRoles" in attrs:
                for role_dn in attrs["ssoRoles"]:
                    if role_dn in all_dns:
                        dependencies[dn].add(role_dn)
        
        # Kahn's algorithm for topological sort
        in_degree: Dict[str, int] = {dn: 0 for dn in all_dns}
        for dn, deps in dependencies.items():
            in_degree[dn] = len(deps)
        
        queue: List[str] = [dn for dn in all_dns if in_degree[dn] == 0]
        sorted_dns: List[str] = []
        
        # Build adjacency list (reverse dependencies)
        dependents: Dict[str, List[str]] = {dn: [] for dn in all_dns}
        for dn, deps in dependencies.items():
            for dep in deps:
                dependents[dep].append(dn)
        
        while queue:
            dn = queue.pop(0)
            sorted_dns.append(dn)
            for dependent in dependents[dn]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Return entries in sorted order
        return [dn_to_entry[dn] for dn in sorted_dns if dn in dn_to_entry]

    @staticmethod
    def _to_bytes_dict(
        attrs: Dict[str, List[str]],
    ) -> Dict[str, List[bytes]]:
        """Convert a string-valued attribute dict to bytes for python-ldap."""
        return {
            attr: [
                v.encode("utf-8") if isinstance(v, str) else v for v in values
            ]
            for attr, values in attrs.items()
        }

    def restore_from_ldif(self, input_path: str) -> int:
        """Restore LDAP entries from LDIF format.

        Uses a multi-pass approach to handle referential-integrity
        constraints (e.g. ``manager``, ``ssoRoles``):

        1. Parse all entries from the LDIF file.
        2. **Topologically sort** entries by dependencies (managers & roles before users).
        3. **Pass 1** – attempt a full add of every entry.
        4. **Pass 2** – retry failed entries as-is (ordering fix).
        5. **Pass 3** – for entries that still fail, strip deferrable
           reference attributes (manager, ssoRoles …), add the entry
           without them, then re-apply the stripped attributes via an
           LDAP *modify* operation.
        """
        import logging

        logger = logging.getLogger(__name__)

        if not self.conn:
            self.connect()

        # --- Phase 1: parse all entries from the file ---
        entries: List[Tuple[str, Dict[str, List[str]]]] = []
        current_dn: Optional[str] = None
        current_attrs: Dict[str, List[str]] = {}

        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")

                if not line:
                    if current_dn and current_attrs:
                        entries.append((current_dn, current_attrs))
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

            # Handle last entry if file doesn't end with a blank line
            if current_dn and current_attrs:
                entries.append((current_dn, current_attrs))

        # --- Phase 2: topologically sort by dependencies (managers/roles first) ---
        entries = self._topological_sort(entries)
        logger.info(
            "Topologically sorted %d entries by dependencies "
            "(managers/roles first)",
            len(entries),
        )

        # --- Phase 3: pass 1 – full add ---
        restored_count = 0
        failed_entries: List[Tuple[str, Dict[str, List[str]]]] = []

        for dn, attrs in entries:
            try:
                self.conn.add_s(  # type: ignore[union-attr]
                    dn, modlist.addModlist(self._to_bytes_dict(attrs))
                )
                restored_count += 1
            except ldap.ALREADY_EXISTS:
                restored_count += 1
            except ldap.LDAPError:
                failed_entries.append((dn, attrs))

        if not failed_entries:
            return restored_count

        # --- Phase 4: pass 2 – simple retry (ordering fix) ---
        logger.info(
            "Restore pass 1: %d ok, %d failed. Starting pass 2 (retry)…",
            restored_count,
            len(failed_entries),
        )
        still_failed: List[Tuple[str, Dict[str, List[str]]]] = []

        for dn, attrs in failed_entries:
            try:
                self.conn.add_s(  # type: ignore[union-attr]
                    dn, modlist.addModlist(self._to_bytes_dict(attrs))
                )
                restored_count += 1
            except ldap.ALREADY_EXISTS:
                restored_count += 1
            except ldap.LDAPError:
                still_failed.append((dn, attrs))

        if not still_failed:
            return restored_count

        # --- Phase 5: pass 3 – strip deferrable attrs, add, then modify ---
        logger.info(
            "Restore pass 2: %d still failing. Starting pass 3 "
            "(strip‑and‑modify)…",
            len(still_failed),
        )
        # Collect deferred attribute modifications to apply at the end
        deferred_mods: List[Tuple[str, Dict[str, List[str]]]] = []
        final_failed: List[Tuple[str, str]] = []

        for dn, attrs in still_failed:
            # Split attributes into safe vs deferrable
            safe_attrs: Dict[str, List[str]] = {}
            deferred_attrs: Dict[str, List[str]] = {}
            for attr, values in attrs.items():
                if attr.lower() in {a.lower() for a in self._DEFERRABLE_ATTRS}:
                    deferred_attrs[attr] = values
                else:
                    safe_attrs[attr] = values

            if not safe_attrs:
                # Nothing left to add (should not happen)
                final_failed.append((dn, "No non-deferred attributes"))
                continue

            try:
                self.conn.add_s(  # type: ignore[union-attr]
                    dn, modlist.addModlist(self._to_bytes_dict(safe_attrs))
                )
                restored_count += 1
                if deferred_attrs:
                    deferred_mods.append((dn, deferred_attrs))
            except ldap.ALREADY_EXISTS:
                restored_count += 1
                if deferred_attrs:
                    deferred_mods.append((dn, deferred_attrs))
            except ldap.LDAPError as e:
                final_failed.append((dn, str(e)))
                logger.warning("Error restoring %s (stripped): %s", dn, e)

        # Now apply deferred attribute modifications
        # First, collect all referenced DNs and create missing ones
        all_referenced_dns: Set[str] = set()
        for dn, deferred_attrs in deferred_mods:
            for attr, values in deferred_attrs.items():
                if attr.lower() in {"manager", "ssoroles"}:
                    all_referenced_dns.update(values)
        
        # Check which referenced DNs exist and create missing ones (including ancestors)
        existing_dns: Set[str] = set()
        missing_dns_to_create: List[str] = []
        
        if all_referenced_dns:
            for ref_dn in all_referenced_dns:
                try:
                    result = self.conn.search_s(  # type: ignore[union-attr]
                        ref_dn, ldap.SCOPE_BASE, "(objectClass=*)"
                    )
                    if result:
                        existing_dns.add(ref_dn)
                except ldap.NO_SUCH_OBJECT:
                    # Mark for creation
                    missing_dns_to_create.append(ref_dn)
            
            # For missing DNs, also check and create ancestors if needed
            for ref_dn in missing_dns_to_create:
                # Extract parent OUs from DN
                dn_parts = ref_dn.split(",")
                accumulated_dn = ""
                for i, part in enumerate(dn_parts):
                    if i == 0:
                        accumulated_dn = part
                    else:
                        accumulated_dn = part + "," + accumulated_dn
                    
                    # Skip base DN itself
                    if accumulated_dn == self.base_dn:
                        continue
                    
                    # Check if this ancestor exists
                    if accumulated_dn not in existing_dns:
                        try:
                            result = self.conn.search_s(  # type: ignore[union-attr]
                                accumulated_dn, ldap.SCOPE_BASE, "(objectClass=*)"
                            )
                            if result:
                                existing_dns.add(accumulated_dn)
                            else:
                                # Create missing ancestor
                                if self._create_missing_entry(accumulated_dn, logger):
                                    existing_dns.add(accumulated_dn)
                        except ldap.NO_SUCH_OBJECT:
                            # Create missing ancestor
                            if self._create_missing_entry(accumulated_dn, logger):
                                existing_dns.add(accumulated_dn)
            
            # Now create the actual missing DNs
            for ref_dn in missing_dns_to_create:
                if self._create_missing_entry(ref_dn, logger):
                    existing_dns.add(ref_dn)
        
        deferred_ok = 0
        deferred_fail = 0
        deferred_skipped = 0
        retry_failed = []
        
        for dn, deferred_attrs in deferred_mods:
            mod_list = [
                (ldap.MOD_ADD, attr, [
                    v.encode("utf-8") if isinstance(v, str) else v
                    for v in values
                ])
                for attr, values in deferred_attrs.items()
            ]
            try:
                self.conn.modify_s(dn, mod_list)  # type: ignore[union-attr]
                deferred_ok += 1
            except ldap.TYPE_OR_VALUE_EXISTS:
                deferred_ok += 1
            except ldap.LDAPError as e:
                # Save for potential retry
                retry_failed.append((dn, deferred_attrs, str(e)))
                deferred_fail += 1
                logger.debug(
                    "Initial attempt failed for deferred attrs on %s: %s", dn, e
                )
        
        # Retry failed modifications once more (in case entry creation helped)
        if retry_failed:
            logger.info(
                "Retrying %d failed deferred attribute modifications…", len(retry_failed)
            )
            for dn, deferred_attrs, initial_error in retry_failed:
                mod_list = [
                    (ldap.MOD_ADD, attr, [
                        v.encode("utf-8") if isinstance(v, str) else v
                        for v in values
                    ])
                    for attr, values in deferred_attrs.items()
                ]
                try:
                    self.conn.modify_s(dn, mod_list)  # type: ignore[union-attr]
                    deferred_ok += 1
                    deferred_fail -= 1
                    logger.info("Retry succeeded for %s", dn)
                except ldap.TYPE_OR_VALUE_EXISTS:
                    deferred_ok += 1
                    deferred_fail -= 1
                except ldap.LDAPError as e:
                    logger.warning(
                        "Retry failed for deferred attrs on %s: %s", dn, e
                    )

        if deferred_ok or deferred_fail or deferred_skipped:
            logger.info(
                "Deferred attribute modifications: %d succeeded, %d failed, %d skipped",
                deferred_ok,
                deferred_fail,
                deferred_skipped,
            )

        if final_failed:
            logger.warning(
                "Restore completed with %d entries that could not be restored",
                len(final_failed),
            )

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
